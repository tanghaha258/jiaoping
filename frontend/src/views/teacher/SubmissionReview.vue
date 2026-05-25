<template>
  <div class="submission-review-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回项目详情</el-button>
      <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
    </div>

    <section class="task-band" v-loading="loading">
      <div>
        <p class="eyebrow">提交审阅</p>
        <h1>{{ taskInfo.title || '任务提交审阅' }}</h1>
        <p>{{ taskInfo.description || '查看学生提交内容，并基于量规完成教师评价。' }}</p>
      </div>
      <div class="task-meta">
        <StatusTag
          :status="taskInfo.status || 'draft'"
          :type-map="taskStatusTypeMap"
          :text-map="taskStatusTextMap"
        />
        <span>{{ taskInfo.rubric_name || '未绑定量规' }}</span>
      </div>
    </section>

    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">学生提交</span>
          <el-segmented
            v-model="filterStatus"
            :options="statusOptions"
            @change="handleFilterChange"
          />
        </div>
      </template>

      <el-table :data="submissions" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="64" align="center" />
        <el-table-column prop="student_name" label="学生" width="120" align="center" />
        <el-table-column label="小组" width="140" align="center">
          <template #default="{ row }">{{ row.group_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="提交内容" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">{{ summarize(row.content) }}</template>
        </el-table-column>
        <el-table-column label="提交时间" width="180" align="center">
          <template #default="{ row }">{{ formatDate(row.submitted_at) }}</template>
        </el-table-column>
        <el-table-column label="评价数" width="92" align="center">
          <template #default="{ row }">{{ row.evaluation_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="状态" width="104" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              :type-map="submissionStatusTypeMap"
              :text-map="submissionStatusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="176" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewSubmission(row)">
              详情
            </el-button>
            <el-button size="small" type="success" link @click="openEvaluation(row)">
              评价
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="submissions.length === 0 && !loading"
        description="暂无学生提交"
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

    <el-drawer v-model="drawerVisible" title="提交详情" size="560px" direction="rtl">
      <template v-if="selectedSubmission">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="学生">
            {{ selectedSubmission.student_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="小组">
            {{ selectedSubmission.group_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">
            {{ formatDate(selectedSubmission.submitted_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag
              :status="selectedSubmission.status"
              :type-map="submissionStatusTypeMap"
              :text-map="submissionStatusTextMap"
            />
          </el-descriptions-item>
          <el-descriptions-item label="提交内容">
            <div class="submission-content">{{ selectedSubmission.content || '-' }}</div>
          </el-descriptions-item>
        </el-descriptions>

        <div class="drawer-actions">
          <el-button type="primary" :icon="Edit" @click="openEvaluation(selectedSubmission)">
            进入评价
          </el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog
      v-model="evalDialogVisible"
      title="教师评价"
      width="720px"
      :close-on-click-modal="false"
      @closed="resetEvalForm"
    >
      <el-form
        ref="evalFormRef"
        :model="evalForm"
        :rules="evalFormRules"
        label-width="96px"
      >
        <el-form-item label="被评学生">
          <el-input :model-value="evalTarget?.student_name || '-'" disabled />
        </el-form-item>
        <el-form-item label="评价量规" prop="rubric_id">
          <el-select
            v-model="evalForm.rubric_id"
            placeholder="请选择评价量规"
            style="width: 100%"
            @change="applyRubricDimensions"
          >
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
              :label="`维度 ${index + 1}`"
              :prop="`dimension_scores.${index}.score`"
              :rules="[{ required: true, message: '请输入分数', trigger: 'change' }]"
            >
              <div class="dimension-row">
                <el-input
                  v-model="dim.dimension"
                  placeholder="维度名称"
                  class="dimension-name"
                />
                <el-input-number
                  v-model="dim.score"
                  :min="0"
                  :max="dim.max_score || 20"
                  class="score-input"
                />
                <span class="score-label">/ {{ dim.max_score || 20 }}</span>
                <el-input
                  v-model="dim.comment"
                  placeholder="维度评语"
                  class="comment-input"
                />
                <el-button
                  v-if="evalForm.dimension_scores.length > 1"
                  :icon="Delete"
                  circle
                  size="small"
                  @click="removeDimension(index)"
                />
              </div>
            </el-form-item>
          </div>
        </div>

        <el-button
          :icon="Plus"
          size="small"
          @click="addDimension"
          :disabled="evalForm.dimension_scores.length >= 8"
        >
          添加维度
        </el-button>

        <el-form-item label="综合评语" prop="comments" class="comments-item">
          <el-input
            v-model="evalForm.comments"
            type="textarea"
            :rows="4"
            placeholder="请写下可反馈给学生的具体建议"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="evalDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingEval" @click="handleSubmitEval">
          保存草稿评价
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
import { ArrowLeft, Delete, Edit, Plus, Refresh } from '@element-plus/icons-vue'
import { createEvaluation } from '@/api/evaluations'
import type { DimensionScore } from '@/api/evaluations'
import { getRubrics } from '@/api/rubrics'
import type { Rubric } from '@/api/rubrics'
import { getSubmissions, getTask } from '@/api/tasks'
import type { SubmissionItem, TaskItem } from '@/api/tasks'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id as string

const taskStatusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  draft: 'info',
  published: 'success',
  closed: 'warning'
}

const taskStatusTextMap: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  closed: '已关闭'
}

const submissionStatusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  submitted: 'info',
  reviewed: 'success'
}

const submissionStatusTextMap: Record<string, string> = {
  submitted: '待评价',
  reviewed: '已评价'
}

const statusOptions = [
  { label: '全部', value: '' },
  { label: '待评价', value: 'submitted' },
  { label: '已评价', value: 'reviewed' }
]

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

const taskInfo = ref<TaskItem>({ ...emptyTask })
const submissions = ref<SubmissionItem[]>([])
const rubrics = ref<Rubric[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('')

const drawerVisible = ref(false)
const selectedSubmission = ref<SubmissionItem | null>(null)

const evalDialogVisible = ref(false)
const evalTarget = ref<SubmissionItem | null>(null)
const submittingEval = ref(false)
const evalFormRef = ref<FormInstance>()

const evalForm = reactive({
  submission_id: '',
  rubric_id: '',
  dimension_scores: [] as DimensionScore[],
  comments: ''
})

const evalFormRules: FormRules = {
  rubric_id: [{ required: true, message: '请选择评价量规', trigger: 'change' }],
  comments: [{ required: true, message: '请填写综合评语', trigger: 'blur' }]
}

const selectedRubric = computed(() =>
  rubrics.value.find((rubric) => rubric.id === evalForm.rubric_id)
)

function goBack() {
  if (taskInfo.value.project_id) {
    router.push(`/teacher/projects/${taskInfo.value.project_id}`)
    return
  }
  router.back()
}

function summarize(value?: string) {
  if (!value) return '-'
  return value.length > 96 ? `${value.slice(0, 96)}...` : value
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function buildDefaultDimensions(rubric?: Rubric): DimensionScore[] {
  if (rubric?.items?.length) {
    return rubric.items.map((item) => ({
      dimension: item.dimension,
      score: 0,
      max_score: Math.max(1, Math.round(item.weight || 20)),
      comment: ''
    }))
  }
  return [
    { dimension: '任务理解', score: 0, max_score: 20, comment: '' },
    { dimension: '证据表达', score: 0, max_score: 20, comment: '' },
    { dimension: '跨学科迁移', score: 0, max_score: 20, comment: '' },
    { dimension: '合作表达', score: 0, max_score: 20, comment: '' },
    { dimension: '改进建议', score: 0, max_score: 20, comment: '' }
  ]
}

function applyRubricDimensions() {
  evalForm.dimension_scores = buildDefaultDimensions(selectedRubric.value)
}

async function loadData() {
  loading.value = true
  try {
    const [taskRes, subsRes, rubricRes] = await Promise.all([
      getTask(taskId),
      getSubmissions(taskId, {
        page: currentPage.value,
        page_size: pageSize.value,
        status: filterStatus.value || undefined
      }),
      getRubrics({ page: 1, page_size: 100 })
    ])
    taskInfo.value = taskRes.data
    submissions.value = subsRes.data?.items || []
    total.value = subsRes.data?.total || 0
    rubrics.value = rubricRes.data?.items || []
  } catch (e: any) {
    ElMessage.error(e?.message || '加载提交数据失败')
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

function viewSubmission(row: SubmissionItem) {
  selectedSubmission.value = row
  drawerVisible.value = true
}

function openEvaluation(row: SubmissionItem) {
  evalTarget.value = row
  evalForm.submission_id = row.id
  const preferredRubric =
    rubrics.value.find((rubric) => rubric.id === taskInfo.value.rubric_id) || rubrics.value[0]
  evalForm.rubric_id = preferredRubric?.id || ''
  evalForm.dimension_scores = buildDefaultDimensions(preferredRubric)
  evalForm.comments = ''
  evalDialogVisible.value = true
}

function addDimension() {
  evalForm.dimension_scores.push({
    dimension: '',
    score: 0,
    max_score: 20,
    comment: ''
  })
}

function removeDimension(index: number) {
  evalForm.dimension_scores.splice(index, 1)
}

function resetEvalForm() {
  evalTarget.value = null
  evalForm.submission_id = ''
  evalForm.rubric_id = ''
  evalForm.dimension_scores = []
  evalForm.comments = ''
  evalFormRef.value?.clearValidate()
}

async function handleSubmitEval() {
  if (!evalFormRef.value) return
  const valid = await evalFormRef.value.validate().catch(() => false)
  if (!valid) return

  const scores: Record<string, number> = {}
  evalForm.dimension_scores.forEach((dimension, index) => {
    const name = dimension.dimension.trim() || `维度${index + 1}`
    scores[name] = Number(dimension.score || 0)
  })

  submittingEval.value = true
  try {
    await createEvaluation({
      submission_id: evalForm.submission_id,
      rubric_id: evalForm.rubric_id,
      scores,
      comments: evalForm.comments,
      evaluator_type: 'teacher'
    })
    ElMessage.success('评价草稿已保存，可在评价中心确认后反馈给学生')
    evalDialogVisible.value = false
    drawerVisible.value = false
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '提交评价失败')
  } finally {
    submittingEval.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.submission-review-page {
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
  min-width: 160px;
  color: #606266;
  font-size: 13px;
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

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.submission-content {
  max-height: 400px;
  padding: 12px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.7;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.dimensions-list {
  width: 100%;
}

.dimension-item {
  margin-bottom: 6px;
}

.dimension-row {
  display: grid;
  grid-template-columns: minmax(112px, 160px) 128px auto minmax(160px, 1fr) 32px;
  gap: 8px;
  align-items: center;
  width: 100%;
}

.score-label {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}

.comments-item {
  margin-top: 16px;
}

@media (max-width: 860px) {
  .task-band,
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .task-meta {
    align-items: flex-start;
  }

  .dimension-row {
    grid-template-columns: 1fr;
  }

  .score-label {
    display: none;
  }
}
</style>
