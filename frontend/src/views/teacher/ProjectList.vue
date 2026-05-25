<template>
  <div class="project-list-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">跨学科项目管理</span>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            创建项目
          </el-button>
        </div>
      </template>

      <!-- Filters -->
      <div class="filter-bar">
        <el-select
          v-model="filterStatus"
          placeholder="项目状态"
          clearable
          style="width: 160px"
          @change="handleFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option label="草稿" value="draft" />
          <el-option label="进行中" value="active" />
          <el-option label="已完成" value="completed" />
          <el-option label="已归档" value="archived" />
        </el-select>
      </div>

      <!-- Table -->
      <el-table
        :data="items"
        v-loading="loading"
        border
        stripe
        empty-text="暂无项目，请创建项目或使用 AI 生成教学方案"
        style="width: 100%"
      >
        <el-table-column prop="name" label="项目名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="grade" label="年级" width="90" align="center" />
        <el-table-column label="学科" min-width="160">
          <template #default="{ row }">
            <el-tag
              v-for="subject in row.subjects"
              :key="subject.id"
              size="small"
              style="margin-right: 4px; margin-bottom: 2px"
            >
              {{ subject.name }}
            </el-tag>
            <span v-if="!row.subjects || row.subjects.length === 0">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag :status="row.status" :type-map="statusTypeMap" :text-map="statusTextMap" />
          </template>
        </el-table-column>
        <el-table-column label="课时" width="70" align="center">
          <template #default="{ row }">
            {{ row.lesson_count }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center" />
        <el-table-column label="操作" width="280" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="viewDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              type="success"
              link
              @click="handleActivate(row)"
            >
              激活
            </el-button>
            <el-button
              v-if="row.status === 'active'"
              size="small"
              type="warning"
              link
              @click="handleComplete(row)"
            >
              完成
            </el-button>
            <el-button
              v-if="row.status === 'completed'"
              size="small"
              type="info"
              link
              @click="handleArchive(row)"
            >
              归档
            </el-button>
            <el-button
              v-if="row.status === 'archived'"
              size="small"
              type="danger"
              link
              disabled
            >
              已归档
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="loadData"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- Create Project Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建跨学科项目"
      width="680px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="年级" prop="grade">
          <el-select v-model="form.grade" placeholder="请选择年级" style="width: 100%">
            <el-option label="七年级" value="七年级" />
            <el-option label="八年级" value="八年级" />
            <el-option label="九年级" value="九年级" />
          </el-select>
        </el-form-item>
        <el-form-item label="涉及学科" prop="subject_ids">
          <el-select
            v-model="form.subject_ids"
            multiple
            placeholder="请选择涉及学科"
            style="width: 100%"
          >
            <el-option label="语文" value="subject-00000000-0000-0000-0001" />
            <el-option label="数学" value="subject-00000000-0000-0000-0002" />
            <el-option label="英语" value="subject-00000000-0000-0000-0003" />
            <el-option label="地理" value="subject-00000000-0000-0000-0004" />
            <el-option label="生物" value="subject-00000000-0000-0000-0005" />
            <el-option label="道法" value="subject-00000000-0000-0000-0006" />
            <el-option label="信息科技" value="subject-00000000-0000-0000-0007" />
          </el-select>
        </el-form-item>
        <el-form-item label="参与班级" prop="class_ids">
          <el-select
            v-model="form.class_ids"
            multiple
            placeholder="请选择参与班级"
            style="width: 100%"
          >
            <el-option label="七年级(1)班" value="class-00000000-0000-0000-0001" />
          </el-select>
        </el-form-item>
        <el-form-item label="驱动性问题" prop="driving_question">
          <el-input
            v-model="form.driving_question"
            type="textarea"
            :rows="3"
            placeholder="请输入驱动性问题，如：如何设计一个既美观又稳固的桥梁模型？"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="课时数量" prop="lesson_count">
          <el-input-number v-model="form.lesson_count" :min="1" :max="40" style="width: 160px" />
          <span class="form-hint">节（1-40）</span>
        </el-form-item>
        <el-form-item label="教学目标" prop="objectives">
          <div class="objectives-list">
            <div
              v-for="(obj, index) in form.objectives"
              :key="index"
              class="objective-item"
            >
              <el-input
                v-model="form.objectives[index]"
                :placeholder="`目标 ${index + 1}`"
                style="flex: 1"
              >
                <template #append>
                  <el-button
                    v-if="form.objectives.length > 1"
                    :icon="Delete"
                    @click="removeObjective(index)"
                  />
                </template>
              </el-input>
            </div>
            <el-button
              :icon="Plus"
              size="small"
              @click="addObjective"
              :disabled="form.objectives.length >= 10"
            >
              添加目标
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { getProjects, createProject, activateProject, completeProject, archiveProject } from '@/api/projects'
import type { ProjectItem, ProjectCreate } from '@/api/projects'
import StatusTag from '@/components/StatusTag.vue'

const router = useRouter()

// Status configs
const statusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  draft: 'info',
  active: 'success',
  completed: 'warning',
  archived: 'danger'
}

const statusTextMap: Record<string, string> = {
  draft: '草稿',
  active: '进行中',
  completed: '已完成',
  archived: '已归档'
}

// Data state
const items = ref<ProjectItem[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('')

// Create dialog
const showCreateDialog = ref(false)
const creating = ref(false)
const formRef = ref<FormInstance>()

const form = reactive<ProjectCreate>({
  name: '',
  grade: '',
  subject_ids: [],
  class_ids: [],
  driving_question: '',
  lesson_count: 4,
  objectives: ['']
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '项目名称长度在2到100个字符', trigger: 'blur' }
  ],
  grade: [
    { required: true, message: '请选择年级', trigger: 'change' }
  ],
  subject_ids: [
    { required: true, message: '请至少选择一个学科', trigger: 'change', type: 'array' }
  ],
  class_ids: [
    { required: true, message: '请至少选择一个班级', trigger: 'change', type: 'array' }
  ],
  driving_question: [
    { required: true, message: '请输入驱动性问题', trigger: 'blur' }
  ]
}

function resetForm() {
  form.name = ''
  form.grade = ''
  form.subject_ids = []
  form.class_ids = []
  form.driving_question = ''
  form.lesson_count = 4
  form.objectives = ['']
  formRef.value?.resetFields()
}

async function loadData() {
  loading.value = true
  try {
    const res = await getProjects({
      page: currentPage.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined
    })
    items.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e: any) {
    items.value = []
    total.value = 0
    ElMessage.error(e?.message || '项目数据加载失败')
  } finally {
    loading.value = false
  }
}

function handleFilterChange() {
  currentPage.value = 1
  loadData()
}

function handleSizeChange() {
  currentPage.value = 1
  loadData()
}

function viewDetail(row: ProjectItem) {
  router.push(`/teacher/projects/${row.id}`)
}

async function handleActivate(row: ProjectItem) {
  try {
    await activateProject(row.id)
    ElMessage.success('项目已激活')
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '激活失败')
  }
}

async function handleComplete(row: ProjectItem) {
  try {
    await ElMessageBox.confirm('确定要将该项目标记为已完成吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await completeProject(row.id)
    ElMessage.success('项目已完成')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '操作失败')
    }
  }
}

async function handleArchive(row: ProjectItem) {
  try {
    await ElMessageBox.confirm('归档后项目将变为只读，确定要归档吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await archiveProject(row.id)
    ElMessage.success('项目已归档')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.message || '操作失败')
    }
  }
}

function addObjective() {
  form.objectives.push('')
}

function removeObjective(index: number) {
  form.objectives.splice(index, 1)
}

async function handleCreate() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await createProject({ ...form })
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

// Initial load
loadData()
</script>

<style scoped>
.project-list-page {
  padding: 0;
}

.page-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.form-hint {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}

.objectives-list {
  width: 100%;
}

.objective-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
</style>
