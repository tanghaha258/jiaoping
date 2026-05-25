<template>
  <div class="student-task-detail-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回任务列表</el-button>
    </div>

    <!-- Task Info Card -->
    <el-card class="info-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">任务详情</span>
          <StatusTag
            v-if="submissionStatus"
            :status="submissionStatus"
            :type-map="statusTypeMap"
            :text-map="statusTextMap"
          />
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务标题" :span="2">
          {{ task.title }}
        </el-descriptions-item>
        <el-descriptions-item label="任务类型">
          <el-tag size="small" type="info">{{ taskTypeMap[task.task_type] || task.task_type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="提交方式">
          {{ submitTypeMap[task.submit_type] || task.submit_type }}
        </el-descriptions-item>
        <el-descriptions-item label="截止日期" :span="2">
          <span :class="{ 'due-overdue': isOverdue }">
            {{ task.due_at || '无截止日期' }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="任务描述" :span="2">
          <div class="description-content">{{ task.description }}</div>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Submission Section -->
    <el-card v-if="submissionStatus === 'pending'" class="submit-card">
      <template #header>
        <span class="card-title">提交作业</span>
      </template>

      <el-form
        ref="submitFormRef"
        :model="submitForm"
        :rules="submitFormRules"
        label-width="80px"
        label-position="top"
      >
        <el-form-item label="提交内容" prop="content">
          <el-input
            v-model="submitForm.content"
            type="textarea"
            :rows="10"
            placeholder="请输入你的作业内容..."
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <div class="submit-actions">
        <el-button
          type="primary"
          :loading="submitting"
          :icon="Upload"
          @click="handleSubmit"
        >
          提交作业
        </el-button>
      </div>
    </el-card>

    <!-- Submitted Content -->
    <el-card v-if="submissionStatus === 'submitted' || submissionStatus === 'reviewed'" class="submit-card">
      <template #header>
        <span class="card-title">已提交内容</span>
      </template>

      <el-alert
        v-if="submissionStatus === 'submitted'"
        title="作业已提交，等待教师批阅"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 16px"
      />

      <div class="submitted-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="提交时间">
            {{ submission?.submitted_at || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="提交内容">
            <div class="content-box">{{ submission?.content || '-' }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- Evaluation Section -->
    <el-card v-if="submissionStatus === 'reviewed' && evaluation" class="eval-card">
      <template #header>
        <span class="card-title">教师评价</span>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="评价人">
          {{ evaluation.evaluator_name }}
        </el-descriptions-item>
        <el-descriptions-item label="评价时间">
          {{ evaluation.created_at }}
        </el-descriptions-item>
        <el-descriptions-item label="总分" :span="2">
          <span class="score-display">
            {{ evalTotalScore }}
          </span>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">维度评分</el-divider>
      <el-table
        v-if="evalDimensionScores && evalDimensionScores.length > 0"
        :data="evalDimensionScores"
        border
        size="small"
      >
        <el-table-column prop="dimension" label="评分维度" />
        <el-table-column label="得分" width="120" align="center">
          <template #default="{ row }">
            {{ row.score }}
          </template>
        </el-table-column>
        <el-table-column prop="comment" label="评语" min-width="200" show-overflow-tooltip />
      </el-table>

      <el-divider content-position="left">综合评语</el-divider>
      <div class="comment-box">{{ evaluation.comments || '暂无评语' }}</div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { ArrowLeft, Upload } from '@element-plus/icons-vue'
import { getTask, submitTask, getSubmissionsForStudent } from '@/api/tasks'
import type { TaskItem, SubmissionItem } from '@/api/tasks'
import { getStudentEvaluations } from '@/api/evaluations'
import type { EvaluationItem } from '@/api/evaluations'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const router = useRouter()

const taskId = route.params.id as string

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

const submitTypeMap: Record<string, string> = {
  text: '文本',
  file: '文件',
  link: '链接'
}

const task = ref<TaskItem>({
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
})
const loading = ref(false)

const submission = ref<SubmissionItem | null>(null)
const submissionStatus = ref<'pending' | 'submitted' | 'reviewed'>('pending')
const evaluation = ref<EvaluationItem | null>(null)

const submitFormRef = ref<FormInstance>()
const submitting = ref(false)

const submitForm = reactive({
  content: ''
})

const submitFormRules: FormRules = {
  content: [
    { required: true, message: '请输入提交内容', trigger: 'blur' },
    { min: 10, message: '内容至少10个字符', trigger: 'blur' }
  ]
}

const isOverdue = computed(() => {
  if (!task.value.due_at) return false
  return new Date(task.value.due_at) < new Date()
})

const evalTotalScore = computed(() => {
  if (!evaluation.value?.scores) return 0
  return Object.values(evaluation.value.scores).reduce((a: number, b: number) => a + b, 0)
})

const evalDimensionScores = computed(() => {
  if (!evaluation.value?.scores) return []
  return Object.entries(evaluation.value.scores).map(([dimension, score]) => ({
    dimension,
    score,
    max_score: 100,
    comment: ''
  }))
})

function goBack() {
  router.push('/student/tasks')
}

async function loadData() {
  loading.value = true
  try {
    const taskRes = await getTask(taskId)
    task.value = taskRes.data

    // Try to get existing submissions for this task
    try {
      const subsRes = await getSubmissionsForStudent({ page: 1, page_size: 100 })
      const items = (subsRes.data?.items || []).filter((item: SubmissionItem) => item.task_id === taskId)
      if (items.length > 0) {
        submission.value = items[0]
        submissionStatus.value = items[0].status === 'reviewed' ? 'reviewed' : 'submitted'

        // Load evaluation if reviewed
        if (items[0].status === 'reviewed') {
          try {
            const evalRes = await getStudentEvaluations({ page: 1, page_size: 10 })
            const matchingEval = (evalRes.data?.items || []).find(
              (e: EvaluationItem) => e.submission_id === items[0].id
            )
            if (matchingEval) {
              evaluation.value = matchingEval
            }
          } catch {
            // Evaluation may not exist yet
          }
        }
      }
    } catch {
      // No submissions yet - stay in pending state
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载任务详情失败')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!submitFormRef.value) return
  const valid = await submitFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const res = await submitTask(taskId, { content: submitForm.content })
    submission.value = res.data
    submissionStatus.value = 'submitted'
    ElMessage.success('作业提交成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.student-task-detail-page {
  padding: 0;
}

.page-nav {
  margin-bottom: 16px;
}

.info-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.submit-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.eval-card {
  margin-bottom: 20px;
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

.description-content {
  white-space: pre-wrap;
  line-height: 1.8;
}

.submit-actions {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.submitted-content {
  padding: 0;
}

.content-box {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}

.score-display {
  color: #409eff;
  font-weight: 700;
  font-size: 16px;
}

.comment-box {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  line-height: 1.8;
  white-space: pre-wrap;
  min-height: 60px;
}
</style>
