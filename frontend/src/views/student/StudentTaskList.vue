<template>
  <div class="student-task-list-page">
    <section class="task-band">
      <div>
        <p class="eyebrow">学习任务</p>
        <h1>我的任务</h1>
        <p>查看老师发布的任务、提交状态和已确认反馈。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
    </section>

    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">任务列表</span>
          <el-segmented
            v-model="filterStatus"
            :options="statusOptions"
            @change="handleFilterChange"
          />
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="64" align="center" />
        <el-table-column prop="title" label="任务" min-width="220" show-overflow-tooltip />
        <el-table-column label="所属项目" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.project_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="任务类型" width="116" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ taskTypeMap[row.task_type] || row.task_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止时间" width="172" align="center">
          <template #default="{ row }">
            <span :class="{ 'due-overdue': isOverdue(row) }">
              {{ formatDate(row.due_at) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="提交状态" width="112" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.submission_status || 'pending'"
              :type-map="submissionStatusTypeMap"
              :text-map="submissionStatusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewTask(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="tasks.length === 0 && !loading"
        description="暂无学习任务"
      />

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="loadData"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getTasksForStudent } from '@/api/tasks'
import type { TaskItem } from '@/api/tasks'
import StatusTag from '@/components/StatusTag.vue'

type StudentTask = TaskItem & {
  project_name?: string
  submission_id?: string | null
  submission_status?: string | null
}

const router = useRouter()

const statusOptions = [
  { label: '全部', value: '' },
  { label: '未提交', value: 'pending' },
  { label: '已提交', value: 'submitted' },
  { label: '已反馈', value: 'reviewed' }
]

const submissionStatusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  pending: 'warning',
  submitted: 'info',
  reviewed: 'success'
}

const submissionStatusTextMap: Record<string, string> = {
  pending: '未提交',
  submitted: '已提交',
  reviewed: '已反馈'
}

const taskTypeMap: Record<string, string> = {
  individual: '个人任务',
  group: '小组任务',
  classroom: '课堂任务',
  homework: '课后任务'
}

const tasks = ref<StudentTask[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('')

function formatDate(value?: string | null) {
  if (!value) return '无截止时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function isOverdue(row: StudentTask): boolean {
  if (!row.due_at) return false
  return new Date(row.due_at) < new Date() && (row.submission_status || 'pending') === 'pending'
}

async function loadData() {
  loading.value = true
  try {
    const res = await getTasksForStudent({
      page: currentPage.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined
    })
    tasks.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '加载任务列表失败')
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

function viewTask(row: StudentTask) {
  router.push(`/student/tasks/${row.id}`)
}

onMounted(loadData)
</script>

<style scoped>
.student-task-list-page {
  padding: 0;
}

.task-band {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 24px;
  margin-bottom: 16px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.task-band h1 {
  margin: 4px 0 8px;
  color: #1f2f5f;
  font-size: 22px;
  line-height: 1.3;
}

.task-band p {
  margin: 0;
  color: #606266;
  line-height: 1.7;
}

.eyebrow {
  color: #245cff !important;
  font-size: 13px;
  font-weight: 700;
}

.page-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.card-title {
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.due-overdue {
  color: #f56c6c;
  font-weight: 600;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 760px) {
  .task-band,
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
