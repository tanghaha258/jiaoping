<template>
  <div class="evaluation-center-page">
    <el-card class="page-card">
      <template #header>
        <span class="card-title">评价中心</span>
      </template>

      <!-- Filters -->
      <div class="filter-bar">
        <el-select
          v-model="filterProject"
          placeholder="按项目筛选"
          clearable
          style="width: 200px"
          @change="handleFilterChange"
        >
          <el-option label="全部项目" value="" />
          <el-option
            v-for="p in projectOptions"
            :key="p.value"
            :label="p.label"
            :value="p.value"
          />
        </el-select>
        <el-input
          v-model="filterStudent"
          placeholder="按学生姓名筛选"
          clearable
          style="width: 200px"
          @input="handleFilterChange"
        />
        <el-select
          v-model="filterStatus"
          placeholder="评价状态"
          clearable
          style="width: 140px"
          @change="handleFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option label="草稿" value="draft" />
          <el-option label="已确认" value="confirmed" />
        </el-select>
      </div>

      <!-- Table -->
      <el-table :data="evaluations" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="student_name" label="学生姓名" width="110" align="center" />
        <el-table-column prop="task_title" label="任务标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="总分" width="120" align="center">
          <template #default="{ row }">
            <span class="score-display">
              {{ row.total_score }} / {{ row.max_score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="评价方式" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="evaluatorTypeMap[row.evaluator_type]">
              {{ evaluatorTextMap[row.evaluator_type] || row.evaluator_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              :type-map="evalStatusTypeMap"
              :text-map="evalStatusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="评价时间" width="170" align="center">
          <template #default="{ row }">
            {{ row.created_at }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewDetail(row)">
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              type="success"
              link
              @click="handleConfirm(row)"
            >
              确认
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- Evaluation Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      title="评价详情"
      width="680px"
    >
      <template v-if="selectedEval">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学生">
            {{ selectedEval.student_name }}
          </el-descriptions-item>
          <el-descriptions-item label="任务">
            {{ selectedEval.task_title }}
          </el-descriptions-item>
          <el-descriptions-item label="评价量规">
            {{ selectedEval.rubric_name }}
          </el-descriptions-item>
          <el-descriptions-item label="评价方式">
            {{ evaluatorTextMap[selectedEval.evaluator_type] || selectedEval.evaluator_type }}
          </el-descriptions-item>
          <el-descriptions-item label="总分" :span="2">
            <span class="score-display" style="font-size: 18px; font-weight: 700">
              {{ selectedEval.total_score }} / {{ selectedEval.max_score }}
            </span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">维度评分</el-divider>
        <el-table :data="selectedEval.dimension_scores" border size="small">
          <el-table-column prop="dimension" label="维度" />
          <el-table-column label="得分" width="120" align="center">
            <template #default="{ row }">
              {{ row.score }} / {{ row.max_score }}
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="评语" min-width="200" show-overflow-tooltip />
        </el-table>

        <el-divider content-position="left">综合评语</el-divider>
        <div class="comment-box">{{ selectedEval.comments || '暂无评语' }}</div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getEvaluations, confirmEvaluation } from '@/api/evaluations'
import type { EvaluationItem } from '@/api/evaluations'
import { getProjects } from '@/api/projects'
import StatusTag from '@/components/StatusTag.vue'
import { demoEvaluations, demoProjects } from '@/mocks/teacherDemo'

const evaluatorTypeMap: Record<string, 'success' | 'warning' | 'info' | 'danger'> = {
  teacher: 'info',
  ai: 'success',
  self: 'info',
  peer: 'warning'
}

const evaluatorTextMap: Record<string, string> = {
  teacher: '教师',
  ai: 'AI',
  self: '自评',
  peer: '互评'
}

const evalStatusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  draft: 'info',
  confirmed: 'success'
}

const evalStatusTextMap: Record<string, string> = {
  draft: '草稿',
  confirmed: '已确认'
}

const evaluations = ref<EvaluationItem[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const filterProject = ref('')
const filterStudent = ref('')
const filterStatus = ref('')

const projectOptions = ref<{ label: string; value: string }[]>([])

const detailVisible = ref(false)
const selectedEval = ref<EvaluationItem | null>(null)

async function loadProjectOptions() {
  try {
    const res = await getProjects({ page_size: 100 })
    const projects = res.data.items?.length ? res.data.items : demoProjects
    projectOptions.value = projects.map((p: any) => ({
      label: p.name,
      value: p.id
    }))
  } catch {
    projectOptions.value = demoProjects.map((p) => ({ label: p.name, value: p.id }))
  }
}

async function loadData() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterProject.value) params.project_id = filterProject.value
    if (filterStudent.value) params.student_id = filterStudent.value
    if (filterStatus.value) params.status = filterStatus.value

    const res = await getEvaluations(params)
    const source = res.data.items?.length ? res.data.items : demoEvaluations
    evaluations.value = source.map(item => ({
      ...item,
      total_score: item.total_score ?? Object.values(item.scores || {}).reduce((a: number, b: number) => a + b, 0),
      max_score: item.max_score ?? 100,
      dimension_scores: item.dimension_scores ?? Object.entries(item.scores || {}).map(([dim, score]) => ({
        dimension: dim, score, max_score: 100, comment: ''
      }))
    }))
    total.value = res.data.total || demoEvaluations.length
  } catch (e: any) {
    evaluations.value = demoEvaluations
    total.value = demoEvaluations.length
    ElMessage.warning(e?.message || '评价数据暂不可用，已加载演示评价')
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

function viewDetail(row: EvaluationItem) {
  selectedEval.value = row
  detailVisible.value = true
}

async function handleConfirm(row: EvaluationItem) {
  try {
    if (row.id.startsWith('demo-')) {
      row.status = 'confirmed'
      row.confirmed_by = 'user-teacher-0000-0000-0000-0001'
      row.confirmer_name = '张老师'
      ElMessage.success('演示评价已确认')
      return
    }
    await confirmEvaluation(row.id)
    ElMessage.success('评价已确认')
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '确认失败')
  }
}

onMounted(() => {
  loadProjectOptions()
  loadData()
})
</script>

<style scoped>
.evaluation-center-page {
  padding: 0;
}

.page-card {
  border-radius: 8px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.score-display {
  color: #409eff;
  font-weight: 600;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
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
