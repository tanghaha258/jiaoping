<template>
  <div class="admin-page">
    <section class="header-band">
      <div>
        <p class="eyebrow">部署配置</p>
        <h1>系统设置</h1>
        <p>维护平台级 JSON 配置，用于部署开关、智能体配置说明和运营参数。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadSettings">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openSetting()">新增设置</el-button>
      </div>
    </section>

    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="card-header">
          <strong>配置列表</strong>
          <div class="filters">
            <el-input v-model="keyword" clearable placeholder="搜索 key 或说明" @keyup.enter="reloadFirstPage" @clear="reloadFirstPage" />
            <el-button @click="reloadFirstPage">查询</el-button>
          </div>
        </div>
      </template>

      <el-table :data="settings" v-loading="loading" border stripe>
        <el-table-column prop="key" label="Key" min-width="220" />
        <el-table-column prop="description" label="说明" min-width="220" show-overflow-tooltip />
        <el-table-column label="值摘要" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">{{ summarize(row.value) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="openSetting(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && settings.length === 0" description="暂无系统设置" />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.originalKey ? '编辑设置' : '新增设置'" width="680px">
      <el-form label-width="80px">
        <el-form-item label="Key" required>
          <el-input v-model="form.key" :disabled="!!form.originalKey" placeholder="如：ai.provider.gjt" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" maxlength="500" />
        </el-form-item>
        <el-form-item label="JSON值" required>
          <el-input v-model="form.valueText" type="textarea" :rows="12" spellcheck="false" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSetting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { getSystemSettings, saveSystemSetting } from '@/api/admin'
import type { SystemSettingItem } from '@/api/admin'

const settings = ref<SystemSettingItem[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const keyword = ref('')
const pagination = reactive({ page: 1, pageSize: 50 })
const form = reactive({
  originalKey: '',
  key: '',
  description: '',
  valueText: '{}'
})

function summarize(value: unknown) {
  const text = JSON.stringify(value)
  return text.length > 120 ? `${text.slice(0, 120)}...` : text
}

async function loadSettings() {
  loading.value = true
  try {
    const res = await getSystemSettings({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: keyword.value || undefined
    })
    settings.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

function reloadFirstPage() {
  pagination.page = 1
  loadSettings()
}

function openSetting(row?: SystemSettingItem) {
  form.originalKey = row?.key || ''
  form.key = row?.key || ''
  form.description = row?.description || ''
  form.valueText = JSON.stringify(row?.value ?? {}, null, 2)
  dialogVisible.value = true
}

async function saveSetting() {
  let parsed: unknown
  try {
    parsed = JSON.parse(form.valueText)
  } catch {
    ElMessage.error('JSON 格式不正确')
    return
  }
  if (!form.key.trim()) {
    ElMessage.error('请输入 Key')
    return
  }
  saving.value = true
  try {
    await saveSystemSetting(form.key.trim(), {
      value: parsed,
      description: form.description || null
    })
    ElMessage.success('设置已保存')
    dialogVisible.value = false
    await loadSettings()
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.admin-page {
  display: grid;
  gap: 16px;
}

.header-band,
.page-card {
  border-radius: 8px;
}

.header-band {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  background: #fff;
  border: 1px solid #e4e7ed;
}

.header-band h1 {
  margin: 4px 0 8px;
  color: #1f2f5f;
  font-size: 24px;
}

.header-band p {
  margin: 0;
  color: #606266;
}

.eyebrow {
  color: #245cff !important;
  font-size: 13px;
  font-weight: 700;
}

.header-actions,
.card-header,
.filters {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header {
  justify-content: space-between;
}

.filters .el-input {
  width: 240px;
}
</style>
