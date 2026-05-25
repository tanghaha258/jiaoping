<template>
  <div class="submission-detail-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回任务</el-button>
      <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="15">
        <el-card class="detail-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span class="card-title">提交详情</span>
              <StatusTag
                v-if="submission"
                :status="submission.status"
                :type-map="statusTypeMap"
                :text-map="statusTextMap"
              />
            </div>
          </template>

          <template v-if="submission">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="任务">
                {{ submission.task_title || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="提交时间">
                {{ formatDate(submission.submitted_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="小组">
                {{ submission.group_name || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="提交内容">
                <div class="content-box">{{ submission.content || '-' }}</div>
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty
            v-else-if="!loading"
            description="未找到提交记录"
          />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="feedback-card">
          <template #header>
            <span class="card-title">已确认反馈</span>
          </template>

          <template v-if="feedback.length">
            <div
              v-for="item in feedback"
              :key="item.id"
              class="feedback-item"
            >
              <div class="feedback-head">
                <strong>{{ item.evaluator_name || '教师' }}</strong>
                <span>{{ formatDate(item.created_at) }}</span>
              </div>
              <div class="score-line">总分：{{ getTotalScore(item) }}</div>
              <div class="comment-box">{{ item.comments || '暂无评语' }}</div>
              <el-table :data="getDimensionScores(item)" size="small" border>
                <el-table-column prop="dimension" label="维度" />
                <el-table-column prop="score" label="得分" width="76" align="center" />
              </el-table>
            </div>
          </template>
          <el-empty v-else description="暂无已确认反馈" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { getStudentEvaluations } from '@/api/evaluations'
import type { DimensionScore, EvaluationItem } from '@/api/evaluations'
import { getSubmission } from '@/api/tasks'
import type { SubmissionItem } from '@/api/tasks'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const router = useRouter()
const submissionId = route.params.id as string

const statusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  submitted: 'info',
  reviewed: 'success'
}

const statusTextMap: Record<string, string> = {
  submitted: '已提交',
  reviewed: '已反馈'
}

const submission = ref<SubmissionItem | null>(null)
const feedback = ref<EvaluationItem[]>([])
const loading = ref(false)

function goBack() {
  if (submission.value?.task_id) {
    router.push(`/student/tasks/${submission.value.task_id}`)
    return
  }
  router.push('/student/tasks')
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function getDimensionScores(row: EvaluationItem): DimensionScore[] {
  if (row.dimension_scores?.length) return row.dimension_scores
  return Object.entries(row.scores || {}).map(([dimension, score]) => ({
    dimension,
    score: Number(score),
    max_score: 0,
    comment: ''
  }))
}

function getTotalScore(row: EvaluationItem) {
  return Object.values(row.scores || {}).reduce((sum, score) => sum + Number(score || 0), 0)
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSubmission(submissionId)
    submission.value = res.data
    const evalRes = await getStudentEvaluations({ page: 1, page_size: 100 })
    feedback.value = (evalRes.data?.items || []).filter(
      (item: EvaluationItem) => item.submission_id === submissionId
    )
  } catch (e: any) {
    submission.value = null
    feedback.value = []
    ElMessage.error(e?.message || '加载提交详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.submission-detail-page {
  padding: 0;
}

.page-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-card,
.feedback-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.card-title {
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.content-box {
  max-height: 420px;
  padding: 14px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
}

.feedback-card {
  position: sticky;
  top: 80px;
}

.feedback-item + .feedback-item {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.feedback-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: #303133;
}

.feedback-head span {
  color: #909399;
  font-size: 13px;
}

.score-line {
  margin-bottom: 10px;
  color: #245cff;
  font-weight: 700;
}

.comment-box {
  padding: 12px;
  margin-bottom: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
}

@media (max-width: 992px) {
  .feedback-card {
    position: static;
    margin-top: 16px;
  }
}
</style>
