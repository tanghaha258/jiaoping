<template>
  <div class="student-task-list-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">我的学习任务</span>
          <el-select
            v-model="filterStatus"
            placeholder="任务状态"
            clearable
            style="width: 160px"
            @change="handleFilterChange"
          >
            <el-option label="全部" value="" />
            <el-option label="待提交" value="pending" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已批改" value="reviewed" />
          </el-select>
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="title" label="任务标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="所属项目" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.project_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="任务类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ taskTypeMap[row.task_type] || row.task_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="140" align="center">
          <template #default="{ row }">
            <span :class="{ 'due-overdue': isOverdue(row) }">
              {{ row.due_at || '无截止' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.submission_status || 'pending'"
              :type-map="statusTypeMap"
              :text-map="statusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewTask(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="tasks.length === 0 && !loading" class="empty-hint">
        暂无学习任务
      </div>

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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTasksForStudent } from '@/api/tasks'
import type { TaskItem } from '@/api/tasks'
import StatusTag from '@/components/StatusTag.vue'

const router = useRouter()

const statusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  pending: 'warning',
  submitted: 'info',
  reviewed: 'success'
}

const statusTextMap: Record<string, string> = {
  pending: '未提交',
  submitted: '已提交',
  reviewed: '已批改'
}

const taskTypeMap: Record<string, string> = {
  reading: '阅读探究',
  experiment: '实验实践',
  discussion: '讨论合作',
  creation: '创作展示',
  reflection: '反思总结'
}

const tasks = ref<(TaskItem & { project_name?: string; submission_status?: string })[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('')

async function loadData() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterStatus.value) params.status = filterStatus.value

    const res = await getTasksForStudent(params)
    tasks.value = res.data.items
    total.value = res.data.total
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

function isOverdue(row: any): boolean {
  if (!row.due_at) return false
  return new Date(row.due_at) < new Date() && row.submission_status === 'pending'
}

function viewTask(row: TaskItem) {
  router.push(`/student/tasks/${row.id}`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.student-task-list-page {
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

.due-overdue {
  color: #f56c6c;
  font-weight: 600;
}

.empty-hint {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
