<template>
  <div class="admin-page">
    <section class="header-band">
      <div>
        <p class="eyebrow">操作追踪</p>
        <h1>审计日志</h1>
        <p>查看账号登录、智能体调用、业务操作等关键事件，支撑部署后的追责与排查。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadLogs">刷新</el-button>
    </section>

    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="card-header">
          <strong>日志记录</strong>
          <div class="filters">
            <el-input v-model="filters.action" clearable placeholder="操作 action" @keyup.enter="reloadFirstPage" @clear="reloadFirstPage" />
            <el-input v-model="filters.target_type" clearable placeholder="对象类型" @keyup.enter="reloadFirstPage" @clear="reloadFirstPage" />
            <el-button @click="reloadFirstPage">查询</el-button>
          </div>
        </div>
      </template>

      <el-table :data="logs" v-loading="loading" border stripe>
        <el-table-column prop="action" label="操作" min-width="180" />
        <el-table-column prop="target_type" label="对象" width="120" />
        <el-table-column prop="target_id" label="对象ID" min-width="220" show-overflow-tooltip />
        <el-table-column prop="user_name" label="操作者" width="140" />
        <el-table-column label="时间" width="180" align="center">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && logs.length === 0" description="暂无审计日志" />
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          background
          layout="total, sizes, prev, pager, next"
          @current-change="loadLogs"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="日志详情" size="560px">
      <el-descriptions v-if="selected" :column="1" border>
        <el-descriptions-item label="操作">{{ selected.action }}</el-descriptions-item>
        <el-descriptions-item label="对象类型">{{ selected.target_type }}</el-descriptions-item>
        <el-descriptions-item label="对象ID">{{ selected.target_id }}</el-descriptions-item>
        <el-descriptions-item label="操作者">{{ selected.user_name || selected.user_id }}</el-descriptions-item>
        <el-descriptions-item label="IP">{{ selected.ip || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ formatDate(selected.created_at) }}</el-descriptions-item>
      </el-descriptions>
      <pre v-if="selected" class="json-block">{{ JSON.stringify(selected.detail || {}, null, 2) }}</pre>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getAuditLogs } from '@/api/admin'
import type { AuditLogItem } from '@/api/admin'

const logs = ref<AuditLogItem[]>([])
const selected = ref<AuditLogItem | null>(null)
const detailVisible = ref(false)
const loading = ref(false)
const filters = reactive({ action: '', target_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function loadLogs() {
  loading.value = true
  try {
    const res = await getAuditLogs({
      page: pagination.page,
      page_size: pagination.pageSize,
      action: filters.action || undefined,
      target_type: filters.target_type || undefined
    })
    logs.value = res.data.items || []
    pagination.total = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function reloadFirstPage() {
  pagination.page = 1
  loadLogs()
}

function handleSizeChange() {
  pagination.page = 1
  loadLogs()
}

function viewDetail(row: AuditLogItem) {
  selected.value = row
  detailVisible.value = true
}

onMounted(loadLogs)
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

.filters .el-input {
  width: 180px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.json-block {
  padding: 14px;
  margin-top: 16px;
  overflow: auto;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 12px;
}
</style>
