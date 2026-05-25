<template>
  <div class="student-task-detail-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回任务列表</el-button>
      <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
    </div>

    <section class="task-band" v-loading="loading">
      <div>
        <p class="eyebrow">任务详情</p>
        <h1>{{ task.title || '学习任务' }}</h1>
        <p>{{ task.description || '请按老师要求完成并提交任务。' }}</p>
      </div>
      <div class="task-meta">
        <StatusTag
          :status="task.status || 'published'"
          :type-map="taskStatusTypeMap"
          :text-map="taskStatusTextMap"
        />
        <StatusTag
          :status="submissionStatus"
          :type-map="submissionStatusTypeMap"
          :text-map="submissionStatusTextMap"
        />
      </div>
    </section>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="15">
        <el-card class="section-card">
          <template #header>
            <span class="card-title">任务要求</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务类型">
              {{ taskTypeMap[task.task_type] || task.task_type || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="提交方式">
              {{ submitTypeMap[task.submit_type] || task.submit_type || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="截止时间" :span="2">
              <span :class="{ 'due-overdue': isOverdue }">{{ formatDate(task.due_at) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="评价量规" :span="2">
              {{ task.rubric_name || '老师未绑定量规' }}
            </el-descriptions-item>
            <el-descriptions-item label="任务描述" :span="2">
              <div class="content-box">{{ task.description || '-' }}</div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">我的提交</span>
              <el-button
                v-if="canSubmit"
                type="primary"
                :icon="Upload"
                @click="openSubmitDialog"
              >
                {{ submission ? '重新提交' : '提交任务' }}
              </el-button>
            </div>
          </template>

          <template v-if="submission">
            <el-alert
              v-if="submission.status === 'submitted'"
              title="已提交，等待老师评价确认"
              type="info"
              show-icon
              :closable="false"
              class="state-alert"
            />
            <el-alert
              v-if="submission.status === 'reviewed'"
              title="老师已评价，请查看右侧反馈"
              type="success"
              show-icon
              :closable="false"
              class="state-alert"
            />
            <el-descriptions :column="1" border>
              <el-descriptions-item label="提交时间">
                {{ formatDate(submission.submitted_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="提交内容">
                <div class="content-box">{{ submission.content || '-' }}</div>
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty
            v-else
            description="尚未提交。任务发布期间可以提交。"
          />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="section-card feedback-card">
          <template #header>
            <span class="card-title">教师反馈</span>
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
          <el-empty
            v-else
            description="暂无已确认反馈"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog
      v-model="submitDialogVisible"
      :title="submission ? '重新提交任务' : '提交任务'"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="submitFormRef"
        :model="submitForm"
        :rules="submitFormRules"
        label-position="top"
      >
        <el-form-item label="提交内容" prop="content">
          <el-input
            v-model="submitForm.content"
            type="textarea"
            :rows="10"
            placeholder="请填写你的学习成果、证据或反思"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item v-if="task.task_type === 'group'" label="小组名称">
          <el-input v-model="submitForm.group_name" placeholder="如：第一小组" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="submitDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { ArrowLeft, Refresh, Upload } from '@element-plus/icons-vue'
import { getStudentEvaluations } from '@/api/evaluations'
import type { DimensionScore, EvaluationItem } from '@/api/evaluations'
import {
  getSubmissionsForStudent,
  getTask,
  submitTask,
  updateSubmission
} from '@/api/tasks'
import type { SubmissionItem, TaskItem } from '@/api/tasks'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id as string

const taskStatusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  published: 'success',
  closed: 'warning',
  draft: 'info'
}

const taskStatusTextMap: Record<string, string> = {
  published: '已发布',
  closed: '已关闭',
  draft: '草稿'
}

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

const submitTypeMap: Record<string, string> = {
  text: '文本',
  file: '文件',
  link: '链接'
}

const emptyTask: TaskItem = {
  id: '',
  project_id: '',
  title: '',
  description: '',
  task_type: '',
  submit_type: '',
  status: '',
  due_at: null,
  rubric_id: null,
  rubric_name: null,
  submission_count: 0,
  created_at: '',
  updated_at: ''
}

const task = ref<TaskItem>({ ...emptyTask })
const submission = ref<SubmissionItem | null>(null)
const feedback = ref<EvaluationItem[]>([])
const loading = ref(false)
const submitting = ref(false)
const submitDialogVisible = ref(false)
const submitFormRef = ref<FormInstance>()

const submitForm = reactive({
  content: '',
  group_name: ''
})

const submitFormRules: FormRules = {
  content: [
    { required: true, message: '请填写提交内容', trigger: 'blur' },
    { min: 10, message: '内容至少 10 个字', trigger: 'blur' }
  ]
}

const submissionStatus = computed(() => submission.value?.status || 'pending')

const canSubmit = computed(() => task.value.status === 'published')

const isOverdue = computed(() => {
  if (!task.value.due_at) return false
  return new Date(task.value.due_at) < new Date() && !submission.value
})

function goBack() {
  router.push('/student/tasks')
}

function formatDate(value?: string | null) {
  if (!value) return '无截止时间'
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

async function loadFeedback(submissionId: string) {
  const evalRes = await getStudentEvaluations({ page: 1, page_size: 100 })
  feedback.value = (evalRes.data?.items || []).filter(
    (item: EvaluationItem) => item.submission_id === submissionId
  )
}

async function loadData() {
  loading.value = true
  try {
    const [taskRes, submissionsRes] = await Promise.all([
      getTask(taskId),
      getSubmissionsForStudent({ page: 1, page_size: 100 })
    ])
    task.value = taskRes.data
    const ownSubmission =
      (submissionsRes.data?.items || []).find((item: SubmissionItem) => item.task_id === taskId) || null
    submission.value = ownSubmission
    feedback.value = []
    if (ownSubmission) {
      await loadFeedback(ownSubmission.id)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载任务详情失败')
  } finally {
    loading.value = false
  }
}

function openSubmitDialog() {
  submitForm.content = submission.value?.content || ''
  submitForm.group_name = submission.value?.group_name || ''
  submitDialogVisible.value = true
}

async function handleSubmit() {
  if (!submitFormRef.value) return
  const valid = await submitFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = {
      content: submitForm.content,
      group_name: submitForm.group_name || undefined
    }
    const res = submission.value
      ? await updateSubmission(submission.value.id, payload)
      : await submitTask(taskId, payload)
    submission.value = res.data
    feedback.value = []
    submitDialogVisible.value = false
    ElMessage.success('任务已提交')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.student-task-detail-page {
  padding: 0;
}

.page-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.task-band {
  display: flex;
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

.task-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  min-width: 112px;
}

.section-card {
  margin-bottom: 16px;
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
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
}

.due-overdue {
  color: #f56c6c;
  font-weight: 700;
}

.state-alert {
  margin-bottom: 16px;
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
  }
}

@media (max-width: 760px) {
  .task-band,
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .task-meta {
    align-items: flex-start;
  }
}
</style>
