<template>
  <div class="evaluation-center-page">
    <section class="ledger-band">
      <div>
        <p class="eyebrow">评价账本</p>
        <h1>评价中心</h1>
        <p>集中查看教师评价草稿与已确认反馈，确认后学生端才可见。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadData">刷新</el-button>
    </section>

    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">评价记录</span>
          <div class="filter-bar">
            <el-select
              v-model="filterStatus"
              placeholder="评价状态"
              clearable
              style="width: 132px"
              @change="handleFilterChange"
            >
              <el-option label="全部状态" value="" />
              <el-option label="草稿" value="draft" />
              <el-option label="已确认" value="confirmed" />
            </el-select>
            <el-select
              v-model="filterEvaluatorType"
              placeholder="评价方式"
              clearable
              style="width: 132px"
              @change="handleFilterChange"
            >
              <el-option label="全部方式" value="" />
              <el-option label="教师评价" value="teacher" />
              <el-option label="AI评价" value="ai" />
              <el-option label="自评" value="self" />
              <el-option label="互评" value="peer" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="evaluations" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="64" align="center" />
        <el-table-column prop="student_name" label="学生" width="120" align="center" />
        <el-table-column prop="task_title" label="任务" min-width="220" show-overflow-tooltip />
        <el-table-column label="总分" width="118" align="center">
          <template #default="{ row }">
            <span class="score-display">{{ getTotalScore(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="评价方式" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="evaluatorTypeMap[row.evaluator_type]">
              {{ evaluatorTextMap[row.evaluator_type] || row.evaluator_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="108" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              :type-map="evalStatusTypeMap"
              :text-map="evalStatusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180" align="center">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="148" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewDetail(row)">
              详情
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

      <el-empty
        v-if="evaluations.length === 0 && !loading"
        description="暂无评价记录。可从任务提交审阅页创建教师评价。"
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

    <el-drawer v-model="detailVisible" title="评价详情" size="620px" direction="rtl">
      <template v-if="selectedEval">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="学生">
            {{ selectedEval.student_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="任务">
            {{ selectedEval.task_title || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="量规">
            {{ selectedEval.rubric_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="评价方式">
            {{ evaluatorTextMap[selectedEval.evaluator_type] || selectedEval.evaluator_type }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag
              :status="selectedEval.status"
              :type-map="evalStatusTypeMap"
              :text-map="evalStatusTextMap"
            />
          </el-descriptions-item>
          <el-descriptions-item label="总分">
            <span class="score-display large">{{ getTotalScore(selectedEval) }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">维度评分</el-divider>
        <el-table :data="getDimensionScores(selectedEval)" border size="small">
          <el-table-column prop="dimension" label="维度" />
          <el-table-column prop="score" label="得分" width="100" align="center" />
        </el-table>

        <el-divider content-position="left">综合评语</el-divider>
        <div class="comment-box">{{ selectedEval.comments || '暂无评语' }}</div>

        <div class="drawer-actions">
          <el-button
            v-if="selectedEval.status === 'draft'"
            type="primary"
            :loading="confirmingId === selectedEval.id"
            @click="handleConfirm(selectedEval)"
          >
            确认并反馈给学生
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { confirmEvaluation, getEvaluations } from '@/api/evaluations'
import type { DimensionScore, EvaluationItem } from '@/api/evaluations'
import StatusTag from '@/components/StatusTag.vue'

const evaluatorTypeMap: Record<string, 'success' | 'warning' | 'info' | 'danger'> = {
  teacher: 'info',
  ai: 'success',
  self: 'warning',
  peer: 'warning'
}

const evaluatorTextMap: Record<string, string> = {
  teacher: '教师评价',
  ai: 'AI评价',
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
const filterStatus = ref('')
const filterEvaluatorType = ref('')

const detailVisible = ref(false)
const selectedEval = ref<EvaluationItem | null>(null)
const confirmingId = ref('')

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
  const totalScore =
    row.total_score ?? Object.values(row.scores || {}).reduce((sum, score) => sum + Number(score || 0), 0)
  return `${totalScore}`
}

async function loadData() {
  loading.value = true
  try {
    const res = await getEvaluations({
      page: currentPage.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      evaluator_type: filterEvaluatorType.value || undefined
    })
    evaluations.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e: any) {
    evaluations.value = []
    total.value = 0
    ElMessage.error(e?.message || '加载评价记录失败')
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
    await ElMessageBox.confirm(
      '确认后该评价会作为正式反馈展示给学生，是否继续？',
      '确认评价',
      { type: 'warning' }
    )
  } catch {
    return
  }

  confirmingId.value = row.id
  try {
    await confirmEvaluation(row.id)
    ElMessage.success('评价已确认，学生端可查看反馈')
    await loadData()
    if (selectedEval.value?.id === row.id) {
      selectedEval.value = evaluations.value.find((item) => item.id === row.id) || null
      if (!selectedEval.value) detailVisible.value = false
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '确认评价失败')
  } finally {
    confirmingId.value = ''
  }
}

onMounted(loadData)
</script>

<style scoped>
.evaluation-center-page {
  padding: 0;
}

.ledger-band {
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

.ledger-band h1 {
  margin: 4px 0 8px;
  color: #1f2f5f;
  font-size: 22px;
  line-height: 1.3;
}

.ledger-band p {
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

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.score-display {
  color: #245cff;
  font-weight: 700;
}

.score-display.large {
  font-size: 18px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.comment-box {
  min-height: 72px;
  padding: 16px;
  color: #303133;
  white-space: pre-wrap;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 760px) {
  .ledger-band,
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-bar {
    justify-content: flex-start;
  }
}
</style>
