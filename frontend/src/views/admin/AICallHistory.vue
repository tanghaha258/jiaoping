<template>
  <div class="admin-page">
    <section class="header-band">
      <div>
        <p class="eyebrow">智能体观测</p>
        <h1>AI 调用记录</h1>
        <p>查看本校或系统内智能体调用、Provider 状态和审核状态，便于后续桂教通对接排障。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadCalls">刷新</el-button>
    </section>

    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="card-header">
          <strong>调用台账</strong>
          <div class="filters">
            <el-select v-model="filters.scenario" clearable placeholder="场景" style="width: 160px" @change="reloadFirstPage">
              <el-option label="备课生成" value="lesson_plan" />
              <el-option label="学情诊断" value="learning_diagnosis" />
              <el-option label="量规生成" value="rubric_generation" />
              <el-option label="资源推荐" value="resource_recommendation" />
              <el-option label="教学反思" value="teaching_reflection" />
            </el-select>
            <el-select v-model="filters.provider" clearable placeholder="Provider" style="width: 140px" @change="reloadFirstPage">
              <el-option label="mock" value="mock" />
              <el-option label="gjt_api" value="gjt_api" />
              <el-option label="manual_import" value="manual_import" />
            </el-select>
            <el-select v-model="filters.status" clearable placeholder="状态" style="width: 130px" @change="reloadFirstPage">
              <el-option label="成功" value="succeeded" />
              <el-option label="运行中" value="running" />
              <el-option label="失败" value="failed" />
              <el-option label="已采纳" value="adopted" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="calls" v-loading="loading" border stripe>
        <el-table-column prop="scenario" label="场景" width="160" />
        <el-table-column prop="agent_name" label="智能体" min-width="180" show-overflow-tooltip />
        <el-table-column prop="provider" label="Provider" width="120" />
        <el-table-column label="调用状态" width="110" align="center">
          <template #default="{ row }"><el-tag>{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="审核状态" width="110" align="center">
          <template #default="{ row }"><el-tag type="info">{{ row.review_status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="input_summary" label="输入摘要" min-width="220" show-overflow-tooltip />
        <el-table-column label="时间" width="180" align="center">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && calls.length === 0" description="暂无 AI 调用记录" />
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          background
          layout="total, sizes, prev, pager, next"
          @current-change="loadCalls"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="调用详情" size="640px">
      <template v-if="selected">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="智能体">{{ selected.agent_name || selected.agent_id }}</el-descriptions-item>
          <el-descriptions-item label="场景">{{ selected.scenario }}</el-descriptions-item>
          <el-descriptions-item label="Provider">{{ selected.provider }}</el-descriptions-item>
          <el-descriptions-item label="调用状态">{{ selected.status }}</el-descriptions-item>
          <el-descriptions-item label="审核状态">{{ selected.review_status }}</el-descriptions-item>
          <el-descriptions-item label="项目ID">{{ selected.project_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selected.created_at) }}</el-descriptions-item>
        </el-descriptions>
        <el-divider content-position="left">请求</el-divider>
        <pre class="json-block">{{ JSON.stringify(selected.request_payload || {}, null, 2) }}</pre>
        <el-divider content-position="left">响应</el-divider>
        <pre class="json-block">{{ JSON.stringify(selected.response_payload || {}, null, 2) }}</pre>
        <el-alert v-if="selected.error_message" type="error" :title="selected.error_message" show-icon :closable="false" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getAdminAICalls } from '@/api/admin'
import type { AICallItem } from '@/api/ai'

const calls = ref<AICallItem[]>([])
const selected = ref<AICallItem | null>(null)
const loading = ref(false)
const detailVisible = ref(false)
const filters = reactive({ scenario: '', provider: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function loadCalls() {
  loading.value = true
  try {
    const res = await getAdminAICalls({
      page: pagination.page,
      page_size: pagination.pageSize,
      scenario: filters.scenario || undefined,
      provider: filters.provider || undefined,
      status: filters.status || undefined
    })
    calls.value = res.data.items || []
    pagination.total = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function reloadFirstPage() {
  pagination.page = 1
  loadCalls()
}

function handleSizeChange() {
  pagination.page = 1
  loadCalls()
}

function viewDetail(row: AICallItem) {
  selected.value = row
  detailVisible.value = true
}

onMounted(loadCalls)
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

.card-header,
.filters {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header {
  justify-content: space-between;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.json-block {
  padding: 14px;
  overflow: auto;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 12px;
}
</style>
