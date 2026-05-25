<template>
  <div class="resource-page">
    <section class="page-head">
      <div>
        <h1>资源中心</h1>
        <p>按类型、可见范围和标签维护校本资源，支撑教学方案、任务和评价复用。</p>
      </div>
      <div class="head-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadResources">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增资源</el-button>
      </div>
    </section>

    <section class="resource-layout">
      <aside class="type-panel">
        <button
          v-for="item in typeOptions"
          :key="item.value"
          type="button"
          class="type-item"
          :class="{ active: filters.resource_type === item.value }"
          @click="selectType(item.value)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </aside>

      <main class="main-panel">
        <div class="toolbar">
          <el-input v-model="keyword" clearable placeholder="搜索资源名称、标签或说明" class="search" />
          <el-select v-model="filters.visibility" clearable placeholder="可见范围" class="filter" @change="reloadFirstPage">
            <el-option v-for="item in visibilityOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-button :icon="Search" @click="reloadFirstPage">筛选</el-button>
        </div>

        <el-table v-loading="loading" :data="filteredResources" row-key="id" @row-click="openDetail">
          <el-table-column label="资源名称" min-width="220">
            <template #default="{ row }">
              <div class="title-cell">
                <strong>{{ row.title }}</strong>
                <span>{{ row.metadata?.description || row.url || row.file_path || '暂无说明' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="130">
            <template #default="{ row }">
              <el-tag effect="light">{{ typeText(row.resource_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="标签" min-width="180">
            <template #default="{ row }">
              <div class="tag-list">
                <el-tag v-for="tag in resourceTags(row)" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
                <span v-if="resourceTags(row).length === 0" class="muted">-</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="范围" width="110">
            <template #default="{ row }">
              {{ visibilityText(row.visibility) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' || row.status === 'published' ? 'success' : 'info'" effect="light">
                {{ statusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="130">
            <template #default="{ row }">{{ formatDate(row.updated_at || row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-tooltip content="查看详情">
                <el-button :icon="View" circle text @click.stop="openDetail(row)" />
              </el-tooltip>
              <el-tooltip content="编辑">
                <el-button :icon="Edit" circle text @click.stop="openEdit(row)" />
              </el-tooltip>
              <el-tooltip content="删除">
                <el-button :icon="Delete" circle text type="danger" @click.stop="removeResource(row)" />
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!loading && filteredResources.length === 0" description="暂无资源，请新增或调整筛选条件" />

        <div class="pagination-row">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next, total"
            @current-change="loadResources"
          />
        </div>
      </main>
    </section>

    <el-drawer v-model="detailVisible" title="资源详情" size="520px">
      <template v-if="selectedResource">
        <div class="detail-head">
          <div>
            <h2>{{ selectedResource.title }}</h2>
            <p>{{ typeText(selectedResource.resource_type) }} / {{ visibilityText(selectedResource.visibility) }}</p>
          </div>
          <el-tag effect="light">{{ statusText(selectedResource.status) }}</el-tag>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="链接">{{ selectedResource.url || '-' }}</el-descriptions-item>
          <el-descriptions-item label="文件路径">{{ selectedResource.file_path || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ selectedResource.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ selectedResource.updated_at }}</el-descriptions-item>
        </el-descriptions>
        <div class="json-block">
          <strong>资源元数据</strong>
          <pre>{{ prettyJson(selectedResource.metadata || {}) }}</pre>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="formVisible" :title="editingId ? '编辑资源' : '新增资源'" width="680px">
      <el-form label-position="top" :model="form">
        <div class="two-cols">
          <el-form-item label="资源名称" required>
            <el-input v-model="form.title" maxlength="200" />
          </el-form-item>
          <el-form-item label="资源类型" required>
            <el-select v-model="form.resource_type">
              <el-option v-for="item in typeOptions.slice(1)" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </div>
        <div class="two-cols">
          <el-form-item label="资源链接">
            <el-input v-model="form.url" placeholder="https://..." />
          </el-form-item>
          <el-form-item label="可见范围">
            <el-select v-model="form.visibility">
              <el-option v-for="item in visibilityOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="说明">
          <el-input v-model="description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="tags" multiple filterable allow-create default-first-option>
            <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
        <el-form-item label="元数据 JSON">
          <el-input v-model="metadataText" type="textarea" :rows="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Collection, Delete, Document, Edit, Files, Link, Plus, Refresh, Search, View, VideoCamera } from '@element-plus/icons-vue'
import { createResource, deleteResource, getResources, updateResource } from '@/api/resources'
import type { ResourceItem, ResourceMutation } from '@/api/resources'

const typeOptions = [
  { label: '全部资源', value: '', icon: Collection },
  { label: '教学设计', value: 'teaching_design', icon: Document },
  { label: '任务单', value: 'task_sheet', icon: Files },
  { label: '评价量规', value: 'rubric', icon: Document },
  { label: '课件', value: 'courseware', icon: Files },
  { label: '微课', value: 'micro_lesson', icon: VideoCamera },
  { label: '外部链接', value: 'link', icon: Link },
  { label: 'AI 建议', value: 'ai_suggested', icon: Collection }
]

const visibilityOptions = [
  { label: '个人', value: 'personal' },
  { label: '校本', value: 'school' },
  { label: '区域', value: 'region' },
  { label: '系统', value: 'system' }
] as const

const commonTags = ['七年级', '地理', '生物', '语文', 'PBL', '跨学科', '评价', '课堂实施']

const loading = ref(false)
const saving = ref(false)
const resources = ref<ResourceItem[]>([])
const selectedResource = ref<ResourceItem | null>(null)
const detailVisible = ref(false)
const formVisible = ref(false)
const editingId = ref('')
const keyword = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const description = ref('')
const tags = ref<string[]>([])
const metadataText = ref('{}')

const filters = reactive({
  resource_type: '',
  visibility: ''
})

const form = reactive<ResourceMutation>({
  title: '',
  resource_type: 'teaching_design',
  file_path: null,
  url: null,
  metadata: {},
  visibility: 'school'
})

const filteredResources = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return resources.value
  return resources.value.filter(item => {
    const haystack = [
      item.title,
      item.resource_type,
      item.url || '',
      item.file_path || '',
      item.metadata?.description || '',
      resourceTags(item).join(' ')
    ].join(' ').toLowerCase()
    return haystack.includes(kw)
  })
})

async function loadResources() {
  loading.value = true
  try {
    const res = await getResources({
      page: page.value,
      page_size: pageSize,
      resource_type: filters.resource_type || undefined,
      visibility: filters.visibility || undefined
    })
    resources.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function reloadFirstPage() {
  page.value = 1
  loadResources()
}

function selectType(value: string) {
  filters.resource_type = value
  reloadFirstPage()
}

function openDetail(resource: ResourceItem) {
  selectedResource.value = resource
  detailVisible.value = true
}

function openCreate() {
  editingId.value = ''
  Object.assign(form, {
    title: '',
    resource_type: filters.resource_type || 'teaching_design',
    file_path: null,
    url: null,
    metadata: {},
    visibility: 'school'
  })
  description.value = ''
  tags.value = []
  metadataText.value = '{}'
  formVisible.value = true
}

function openEdit(resource: ResourceItem) {
  editingId.value = resource.id
  Object.assign(form, {
    title: resource.title,
    resource_type: resource.resource_type,
    file_path: resource.file_path,
    url: resource.url,
    metadata: resource.metadata || {},
    visibility: resource.visibility as ResourceMutation['visibility']
  })
  description.value = String(resource.metadata?.description || '')
  tags.value = resourceTags(resource)
  metadataText.value = prettyJson(resource.metadata || {})
  formVisible.value = true
}

async function submitForm() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写资源名称')
    return
  }

  let metadata: Record<string, any>
  try {
    metadata = parseJsonObject(metadataText.value)
  } catch (error: any) {
    ElMessage.error(error.message)
    return
  }
  metadata.description = description.value
  metadata.tags = tags.value

  saving.value = true
  try {
    const payload: ResourceMutation = {
      title: form.title.trim(),
      resource_type: form.resource_type,
      file_path: form.file_path || null,
      url: form.url || null,
      visibility: form.visibility,
      metadata
    }
    if (editingId.value) {
      await updateResource(editingId.value, payload)
      ElMessage.success('资源已更新')
    } else {
      await createResource(payload)
      ElMessage.success('资源已创建')
    }
    formVisible.value = false
    await loadResources()
  } finally {
    saving.value = false
  }
}

async function removeResource(resource: ResourceItem) {
  await ElMessageBox.confirm(`确认删除“${resource.title}”？`, '删除资源', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await deleteResource(resource.id)
  ElMessage.success('资源已删除')
  await loadResources()
}

function resourceTags(resource: ResourceItem) {
  const raw = resource.metadata?.tags
  return Array.isArray(raw) ? raw.filter(Boolean).map(String) : []
}

function typeText(value: string) {
  return typeOptions.find(item => item.value === value)?.label || value
}

function visibilityText(value: string) {
  return visibilityOptions.find(item => item.value === value)?.label || value
}

function statusText(value: string) {
  const map: Record<string, string> = {
    active: '启用',
    published: '已发布',
    draft: '草稿',
    deleted: '已删除'
  }
  return map[value] || value
}

function parseJsonObject(value: string): Record<string, any> {
  const parsed = JSON.parse(value || '{}')
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error('元数据必须是 JSON 对象')
  }
  return parsed
}

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2)
}

function formatDate(value?: string) {
  return value ? value.slice(0, 10) : '-'
}

onMounted(loadResources)
</script>

<style scoped>
.resource-page {
  display: grid;
  gap: 16px;
}

.page-head,
.head-actions,
.toolbar,
.pagination-row,
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-head h1 {
  margin: 0 0 8px;
  color: #17233c;
  font-size: 24px;
}

.page-head p,
.muted,
.detail-head p,
.title-cell span {
  color: #64748b;
}

.resource-layout {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr);
  gap: 16px;
}

.type-panel,
.main-panel {
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #fff;
}

.type-panel {
  display: grid;
  align-content: start;
  gap: 6px;
  padding: 10px;
}

.type-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #334155;
  cursor: pointer;
  text-align: left;
}

.type-item.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.main-panel {
  padding: 16px;
}

.search {
  max-width: 340px;
}

.filter {
  width: 150px;
}

.title-cell {
  display: grid;
  gap: 4px;
}

.title-cell strong,
.detail-head h2,
.json-block strong {
  color: #1f3356;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pagination-row {
  justify-content: flex-end;
  margin-top: 14px;
}

.detail-head {
  align-items: flex-start;
  margin-bottom: 16px;
}

.json-block {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.json-block pre {
  max-height: 260px;
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
}

.two-cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.two-cols :deep(.el-select) {
  width: 100%;
}

@media (max-width: 920px) {
  .resource-layout,
  .two-cols {
    grid-template-columns: 1fr;
  }

  .toolbar {
    display: grid;
  }

  .search,
  .filter {
    max-width: none;
    width: 100%;
  }
}
</style>
