<template>
  <div class="student-profile-page">
    <!-- Profile Info Card -->
    <el-card class="profile-card" v-loading="profileLoading">
      <template #header>
        <span class="card-title">我的档案</span>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="姓名">
          {{ studentInfo.name }}
        </el-descriptions-item>
        <el-descriptions-item label="用户名">
          {{ studentInfo.username }}
        </el-descriptions-item>
        <el-descriptions-item label="学校">
          {{ studentInfo.school_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="班级">
          {{ studentInfo.class_name || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Statistics Cards -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon total-icon">
            <el-icon :size="32"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.totalTasks }}</div>
            <div class="stat-label">全部任务</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon completed-icon">
            <el-icon :size="32"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.completedTasks }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon pending-icon">
            <el-icon :size="32"><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.pendingTasks }}</div>
            <div class="stat-label">待完成</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon score-icon">
            <el-icon :size="32"><Trophy /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.averageScore.toFixed(1) }}</div>
            <div class="stat-label">平均分</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Completed Tasks History -->
    <el-card class="history-card">
      <template #header>
        <span class="card-title">已完成任务</span>
      </template>

      <el-table :data="completedSubmissions" v-loading="historyLoading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column label="任务标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.task_title || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="170" align="center">
          <template #default="{ row }">
            {{ row.submitted_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="批阅状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              :type-map="statusTypeMap"
              :text-map="statusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="得分" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.score !== undefined" class="score-text">
              {{ row.score }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewSubmission(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="completedSubmissions.length === 0 && !historyLoading" class="empty-hint">
        暂无已完成的任务
      </div>

      <div v-if="totalHistory > pageSize" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="historyPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="totalHistory"
          layout="total, prev, pager, next"
          background
          @current-change="loadHistory"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, CircleCheck, Clock, Trophy } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'
import { getSubmissionsForStudent } from '@/api/tasks'
import { getStudentEvaluations } from '@/api/evaluations'
import StatusTag from '@/components/StatusTag.vue'

const router = useRouter()
const authStore = useAuthStore()
const { user } = storeToRefs(authStore)

const profileLoading = ref(false)

const studentInfo = reactive({
  name: user.value?.name || '',
  username: user.value?.username || '',
  school_name: user.value?.school_name || '',
  class_name: ''
})

const stats = reactive({
  totalTasks: 0,
  completedTasks: 0,
  pendingTasks: 0,
  averageScore: 0
})

const statusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  submitted: 'info',
  reviewed: 'success'
}

const statusTextMap: Record<string, string> = {
  submitted: '待批阅',
  reviewed: '已批阅'
}

const completedSubmissions = ref<any[]>([])
const historyLoading = ref(false)
const historyPage = ref(1)
const pageSize = ref(10)
const totalHistory = ref(0)

async function loadHistory() {
  historyLoading.value = true
  try {
    const [subsRes, evalRes] = await Promise.all([
      getSubmissionsForStudent({ page: historyPage.value, page_size: pageSize.value }),
      getStudentEvaluations({ page: 1, page_size: 100 })
    ])

    const submissions = subsRes.data.items || []
    totalHistory.value = subsRes.data.total

    // Map evaluations to submissions
    const evalMap = new Map<string, any>()
    ;(evalRes.data.items || []).forEach((e: any) => {
      evalMap.set(e.submission_id, e)
    })

    completedSubmissions.value = submissions.map((s: any) => {
      const evalItem = evalMap.get(s.id)
      return {
        ...s,
        score: evalItem ? evalItem.total_score : undefined,
        max_score: evalItem ? evalItem.max_score : undefined
      }
    })

    // Update stats
    stats.totalTasks = totalHistory.value
    stats.completedTasks = submissions.filter((s: any) => s.status === 'reviewed').length
    stats.pendingTasks = submissions.filter((s: any) => s.status === 'submitted').length

    // Calculate average score
    const reviewedEvals = (evalRes.data.items || []).filter((e: any) => e.status === 'confirmed')
    if (reviewedEvals.length > 0) {
      const totalScore = reviewedEvals.reduce((sum: number, e: any) => sum + e.total_score, 0)
      const totalMax = reviewedEvals.reduce((sum: number, e: any) => sum + e.max_score, 0)
      stats.averageScore = totalMax > 0 ? (totalScore / totalMax) * 100 : 0
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

function viewSubmission(row: any) {
  router.push(`/student/submissions/${row.id}`)
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.student-profile-page {
  padding: 0;
}

.profile-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.total-icon {
  background: #e6f4ff;
  color: #409eff;
}

.completed-icon {
  background: #f0f9eb;
  color: #67c23a;
}

.pending-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.score-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 6px;
}

.history-card {
  border-radius: 8px;
}

.score-text {
  color: #409eff;
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
