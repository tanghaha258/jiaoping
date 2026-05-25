<template>
  <div class="submission-review-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回项目详情</el-button>
    </div>

    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">提交审核</span>
          <span class="task-info" v-if="taskInfo.title">
            任务：{{ taskInfo.title }}
          </span>
        </div>
      </template>

      <el-table :data="submissions" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="student_name" label="学生姓名" width="120" align="center" />
        <el-table-column label="提交时间" width="170" align="center">
          <template #default="{ row }">
            {{ row.submitted_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="内容预览" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.content ? row.content.substring(0, 100) + (row.content.length > 100 ? '...' : '') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              :type-map="submissionStatusTypeMap"
              :text-map="submissionStatusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewSubmission(row)">
              查看详情
            </el-button>
            <el-button
              v-if="row.status !== 'reviewed'"
              size="small"
              type="success"
              link
              @click="openEvaluation(row)"
            >
              评价
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="submissions.length === 0 && !loading" class="empty-hint">
        暂无学生提交
      </div>
    </el-card>

    <!-- Submission Detail Drawer -->
    <el-drawer
      v-model="drawerVisible"
      title="提交详情"
      size="560px"
      direction="rtl"
    >
      <template v-if="selectedSubmission">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="学生">
            {{ selectedSubmission.student_name }}
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">
            {{ selectedSubmission.submitted_at }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag
              :status="selectedSubmission.status"
              :type-map="submissionStatusTypeMap"
              :text-map="submissionStatusTextMap"
            />
          </el-descriptions-item>
          <el-descriptions-item label="提交内容">
            <div class="submission-content">{{ selectedSubmission.content }}</div>
          </el-descriptions-item>
        </el-descriptions>

        <div class="drawer-actions">
          <el-button
            v-if="selectedSubmission.status !== 'reviewed'"
            type="primary"
            :icon="Edit"
            @click="openEvaluation(selectedSubmission)"
          >
            评价
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- Evaluation Dialog -->
    <el-dialog
      v-model="evalDialogVisible"
      title="学生评价"
      width="640px"
      :close-on-click-modal="false"
      @closed="resetEvalForm"
    >
      <el-form
        ref="evalFormRef"
        :model="evalForm"
        :rules="evalFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="被评学生">
          <el-input :model-value="evalTarget?.student_name" disabled />
        </el-form-item>
        <el-form-item label="评价量规" prop="rubric_id">
          <el-select v-model="evalForm.rubric_id" placeholder="请选择评价量规" style="width: 100%">
            <el-option
              v-for="rubric in rubrics"
              :key="rubric.id"
              :label="rubric.name"
              :value="rubric.id"
            />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">维度评分</el-divider>

        <div class="dimensions-list">
          <div
            v-for="(dim, index) in evalForm.dimension_scores"
            :key="index"
            class="dimension-item"
          >
            <el-form-item
              :label="dim.dimension || `维度 ${index + 1}`"
              :prop="`dimension_scores.${index}.score`"
              :rules="[{ required: true, message: '请打分', trigger: 'change' }]"
            >
              <div class="dimension-row">
                <el-input
                  v-model="dim.dimension"
                  placeholder="维度名称"
                  style="width: 150px; margin-right: 8px"
                />
                <el-input-number
                  v-model="dim.score"
                  :min="0"
                  :max="dim.max_score || 10"
                  style="width: 120px; margin-right: 8px"
                />
                <span class="score-label">/ {{ dim.max_score || 10 }}</span>
                <el-input
                  v-model="dim.comment"
                  placeholder="评语"
                  style="flex: 1; margin-left: 8px"
                />
                <el-button
                  v-if="evalForm.dimension_scores.length > 1"
                  :icon="Delete"
                  circle
                  size="small"
                  style="margin-left: 8px"
                  @click="removeDimension(index)"
                />
              </div>
            </el-form-item>
          </div>
        </div>

        <el-button :icon="Plus" size="small" @click="addDimension" :disabled="evalForm.dimension_scores.length >= 8">
          添加维度
        </el-button>

        <el-form-item label="综合评语" prop="comments" style="margin-top: 16px">
          <el-input
            v-model="evalForm.comments"
            type="textarea"
            :rows="3"
            placeholder="请输入综合评语"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="evalDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingEval" @click="handleSubmitEval">
          提交评价
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { ArrowLeft, Edit, Plus, Delete } from '@element-plus/icons-vue'
import { getTask } from '@/api/tasks'
import { getSubmissions } from '@/api/tasks'
import { createEvaluation } from '@/api/evaluations'
import { getRubrics } from '@/api/rubrics'
import type { TaskItem, SubmissionItem } from '@/api/tasks'
import type { DimensionScore } from '@/api/evaluations'
import type { Rubric } from '@/api/rubrics'
import StatusTag from '@/components/StatusTag.vue'
import { onMounted } from 'vue'

const route = useRoute()
const router = useRouter()

const taskId = route.params.id as string

const submissionStatusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  submitted: 'info',
  reviewed: 'success'
}

const submissionStatusTextMap: Record<string, string> = {
  submitted: '待批阅',
  reviewed: '已批阅'
}

const taskInfo = ref<TaskItem>({
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
const submissions = ref<SubmissionItem[]>([])
const rubrics = ref<Rubric[]>([])
const loading = ref(false)

const drawerVisible = ref(false)
const selectedSubmission = ref<SubmissionItem | null>(null)

const evalDialogVisible = ref(false)
const evalTarget = ref<SubmissionItem | null>(null)
const submittingEval = ref(false)
const evalFormRef = ref<FormInstance>()

const evalForm = reactive({
  submission_id: '',
  rubric_id: '',
  dimension_scores: [
    { dimension: '知识理解', score: 0, max_score: 10, comment: '' },
    { dimension: '思维方法', score: 0, max_score: 10, comment: '' },
    { dimension: '实践能力', score: 0, max_score: 10, comment: '' }
  ] as DimensionScore[],
  comments: ''
})

const evalFormRules: FormRules = {
  rubric_id: [
    { required: true, message: '请选择评价量规', trigger: 'change' }
  ]
}

function goBack() {
  router.back()
}

async function loadData() {
  loading.value = true
  try {
    const [taskRes, subsRes, rubricRes] = await Promise.all([
      getTask(taskId),
      getSubmissions(taskId),
      getRubrics({ page: 1, page_size: 50 })
    ])
    taskInfo.value = taskRes.data
    submissions.value = subsRes.data?.items || []
    rubrics.value = rubricRes.data?.items || []
  } catch (e: any) {
    ElMessage.error(e?.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function viewSubmission(row: SubmissionItem) {
  selectedSubmission.value = row
  drawerVisible.value = true
}

function openEvaluation(row: SubmissionItem) {
  evalTarget.value = row
  evalForm.submission_id = row.id
  const preferredRubric = rubrics.value.find((rubric) => rubric.id === taskInfo.value.rubric_id) || rubrics.value[0]
  evalForm.rubric_id = preferredRubric?.id || ''
  evalForm.dimension_scores = preferredRubric?.items?.length
    ? preferredRubric.items.map((item) => ({
        dimension: item.dimension,
        score: 0,
        max_score: Math.round(item.weight || 20),
        comment: ''
      }))
    : [
        { dimension: '知识理解', score: 0, max_score: 20, comment: '' },
        { dimension: '探究能力', score: 0, max_score: 20, comment: '' },
        { dimension: '跨学科迁移', score: 0, max_score: 20, comment: '' },
        { dimension: '合作表达', score: 0, max_score: 20, comment: '' },
        { dimension: '行动方案', score: 0, max_score: 20, comment: '' }
      ]
  evalForm.comments = ''
  evalDialogVisible.value = true
}

function addDimension() {
  evalForm.dimension_scores.push({
    dimension: '',
    score: 0,
    max_score: 10,
    comment: ''
  })
}

function removeDimension(index: number) {
  evalForm.dimension_scores.splice(index, 1)
}

function resetEvalForm() {
  evalTarget.value = null
  evalFormRef.value?.resetFields()
}

async function handleSubmitEval() {
  if (!evalFormRef.value) return
  const valid = await evalFormRef.value.validate().catch(() => false)
  if (!valid) return

  submittingEval.value = true
  try {
    const scores: Record<string, number> = {}
    evalForm.dimension_scores.forEach(d => {
      scores[d.dimension || '未命名维度'] = d.score
    })
    await createEvaluation({
      submission_id: evalForm.submission_id,
      rubric_id: evalForm.rubric_id,
      scores,
      comments: evalForm.comments
    })
    ElMessage.success('评价提交成功')
    evalDialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '评价提交失败')
  } finally {
    submittingEval.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.submission-review-page {
  padding: 0;
}

.page-nav {
  margin-bottom: 16px;
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

.task-info {
  font-size: 14px;
  color: #606266;
}

.empty-hint {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}

.submission-content {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}

.drawer-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.dimensions-list {
  width: 100%;
}

.dimension-item {
  margin-bottom: 4px;
}

.dimension-row {
  display: flex;
  align-items: center;
  width: 100%;
}

.score-label {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}
</style>
