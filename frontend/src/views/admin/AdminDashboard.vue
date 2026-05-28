<template>
  <div class="admin-dashboard">
    <section class="header-band">
      <div>
        <p class="eyebrow">运营总览</p>
        <h1>管理驾驶舱</h1>
        <p>面向试运行的学校、用户、项目、资源、AI 调用和 readiness 检查。</p>
      </div>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="loadData">
        刷新数据
      </el-button>
    </section>

    <section class="metric-grid">
      <el-card v-for="item in metrics" :key="item.label" shadow="never" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.hint }}</em>
      </el-card>
    </section>

    <section class="readiness-panel">
      <div class="readiness-head">
        <div>
          <p class="eyebrow">试运行检查</p>
          <h2>试运行检查清单</h2>
          <p>把能否部署、能否演示、能否真实运转拆成可处理的检查项。</p>
        </div>
        <div class="readiness-summary">
          <el-tag :type="overallTagType" effect="dark">
            {{ readinessStatusText }}
          </el-tag>
          <span>正常 {{ readiness.summary.ok }}</span>
          <span>提醒 {{ readiness.summary.warning }}</span>
          <span>阻断 {{ readiness.summary.error }}</span>
        </div>
      </div>

      <el-empty
        v-if="!readiness.items.length"
        description="暂无检查数据"
        :image-size="80"
      />
      <div v-else class="checklist">
        <article v-for="item in readiness.items" :key="item.key" class="check-item">
          <div class="check-main">
            <el-tag :type="itemTagType(item.status)" effect="light">
              {{ itemStatusText(item.status) }}
            </el-tag>
            <div>
              <h3>{{ item.label }}</h3>
              <p>{{ item.description }}</p>
              <span>{{ item.metric }}</span>
            </div>
          </div>
          <el-button
            v-if="item.route"
            text
            type="primary"
            :icon="ArrowRight"
            @click="goTo(item.route)"
          >
            {{ item.action }}
          </el-button>
        </article>
      </div>
    </section>

    <section class="runbook-panel">
      <div class="runbook-head">
        <div>
          <p class="eyebrow">试运行演练台</p>
          <h2>演练阶段</h2>
          <p>按运营顺序串联 readiness 证据、责任角色和下一步处理入口。</p>
        </div>
        <div class="readiness-summary">
          <span>Provider演练</span>
          <el-tag :type="runbookTagType" effect="dark">
            {{ trialRunbook.status === 'ready' ? '演练可继续' : '需要处理' }}
          </el-tag>
          <span>正常 {{ trialRunbook.summary.ok }}</span>
          <span>提醒 {{ trialRunbook.summary.warning }}</span>
          <span>阻断 {{ trialRunbook.summary.error }}</span>
        </div>
      </div>

      <div class="runbook-list">
        <article v-for="stage in trialRunbook.stages" :key="stage.key" class="runbook-stage">
          <div class="stage-top">
            <el-tag :type="itemTagType(stage.status)" effect="light">
              {{ itemStatusText(stage.status) }}
            </el-tag>
            <h3>{{ stage.title }}</h3>
          </div>
          <dl>
            <div>
              <dt>责任角色</dt>
              <dd>{{ stage.owner }}</dd>
            </div>
            <div>
              <dt>证据</dt>
              <dd>
                <span v-for="evidence in stage.evidence" :key="evidence">{{ evidence }}</span>
              </dd>
            </div>
            <div>
              <dt>下一步</dt>
              <dd>{{ stage.next_step }}</dd>
            </div>
          </dl>
          <div class="stage-actions">
            <el-button text type="primary" :icon="ArrowRight" @click="goTo(stage.route)">
              {{ stage.primary_action }}
            </el-button>
            <el-button text type="primary" :icon="DocumentChecked" @click="openRecordDialog(stage)">
              记录演练
            </el-button>
          </div>
        </article>
      </div>

      <div class="recent-runbook-records">
        <div class="recent-head">
          <h3>最近演练记录</h3>
          <span>{{ recentRunbookRecords.length }} 条</span>
        </div>
        <div v-if="recentRunbookRecords.length" class="record-list">
          <article v-for="record in recentRunbookRecords" :key="record.id" class="record-item">
            <div class="record-meta">
              <strong>{{ stageTitle(record.stage_key) }}</strong>
              <span>{{ record.operator_name || '管理员' }}</span>
            </div>
            <el-tag :type="recordTagType(record.status)" effect="light">
              {{ recordStatusText(record.status) }}
            </el-tag>
            <p>{{ record.note || '未填写备注' }}</p>
          </article>
        </div>
        <el-empty v-else description="暂无演练记录" :image-size="72" />
      </div>
    </section>

    <section class="content-grid">
      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-head">
            <strong>项目状态分布</strong>
            <el-tag effect="light">实时聚合</el-tag>
          </div>
        </template>
        <el-table :data="statusRows" size="small" border>
          <el-table-column prop="statusText" label="状态" />
          <el-table-column prop="count" label="数量" width="120" align="center" />
        </el-table>
      </el-card>

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-head">
            <strong>项目趋势</strong>
            <el-tag effect="light" type="success">按月</el-tag>
          </div>
        </template>
        <el-table :data="trendRows" size="small" border>
          <el-table-column prop="month" label="月份" />
          <el-table-column prop="count" label="项目数" width="120" align="center" />
        </el-table>
      </el-card>

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-head">
            <strong>AI 使用状态</strong>
            <el-tag effect="light" type="warning">契约优先</el-tag>
          </div>
        </template>
        <div class="ai-note">
          <strong>{{ aiUsage.total_calls }}</strong>
          <span>当前 AI 调用次数。桂教通智能体接入后，仍沿用本平台的调用记录和契约。</span>
        </div>
        <el-table :data="aiProviderRows" size="small" border>
          <el-table-column prop="provider" label="Provider" />
          <el-table-column prop="count" label="调用数" width="120" align="center" />
        </el-table>
      </el-card>
    </section>

    <el-dialog v-model="recordDialogVisible" title="记录演练" width="560px">
      <div v-if="selectedRunbookStage" class="record-dialog">
        <h3>{{ selectedRunbookStage.title }}</h3>
        <el-form label-position="top">
          <el-form-item label="演练结论">
            <el-radio-group v-model="recordForm.status">
              <el-radio-button value="checked">已检查</el-radio-button>
              <el-radio-button value="blocked">有阻断</el-radio-button>
              <el-radio-button value="skipped">已跳过</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="recordForm.note"
              type="textarea"
              :rows="4"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="证据">
            <div class="dialog-evidence">
              <span v-for="item in recordForm.evidence" :key="item">{{ item }}</span>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="recordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="recordSubmitting" @click="submitRunbookRecord">
          保存记录
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, DocumentChecked, Refresh } from '@element-plus/icons-vue'
import {
  createTrialRunbookRecord,
  getAIUsage,
  getDashboardOverview,
  getProjectTrends,
  getTrialOperationsRunbook,
  getTrialReadiness,
  getTrialRunbookRecords
} from '@/api/dashboard'
import type {
  AIUsage,
  DashboardOverview,
  ProjectTrends,
  TrialOperationsRunbook,
  TrialOperationsStage,
  TrialReadiness,
  TrialReadinessItemStatus,
  TrialRunbookRecord,
  TrialRunbookRecordCreate,
  TrialRunbookRecordStatus
} from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)

const overview = ref<DashboardOverview>({
  schools: 0,
  teachers: 0,
  students: 0,
  projects: 0,
  tasks: 0,
  resources: 0,
  ai_calls: 0
})

const trends = ref<ProjectTrends>({ by_month: [], by_status: [] })
const aiUsage = ref<AIUsage>({ by_provider: [], by_scenario: [], total_calls: 0 })
const readiness = ref<TrialReadiness>({
  status: 'action_required',
  checked_at: '',
  summary: { ok: 0, warning: 0, error: 0 },
  items: []
})
const trialRunbook = ref<TrialOperationsRunbook>({
  status: 'action_required',
  checked_at: '',
  summary: { ok: 0, warning: 0, error: 0 },
  stages: []
})
const recentRunbookRecords = ref<TrialRunbookRecord[]>([])
const recordDialogVisible = ref(false)
const recordSubmitting = ref(false)
const selectedRunbookStage = ref<TrialOperationsStage | null>(null)
const recordForm = ref<TrialRunbookRecordCreate>({
  status: 'checked',
  note: '',
  evidence: []
})

const metrics = computed(() => [
  { label: '学校数量', value: overview.value.schools, hint: '已接入机构' },
  { label: '教师数量', value: overview.value.teachers, hint: '可发起项目' },
  { label: '学生数量', value: overview.value.students, hint: '可参与任务' },
  { label: '项目数量', value: overview.value.projects, hint: '教学评项目' },
  { label: '任务数量', value: overview.value.tasks, hint: '已创建学习任务' },
  { label: '资源数量', value: overview.value.resources, hint: '校本资源沉淀' }
])

const statusTextMap: Record<string, string> = {
  draft: '草稿',
  active: '进行中',
  completed: '已结项',
  archived: '已归档'
}

const statusRows = computed(() => trends.value.by_status.map((item) => ({
  ...item,
  statusText: statusTextMap[item.status] || item.status
})))

const trendRows = computed(() => trends.value.by_month)
const aiProviderRows = computed(() => (
  aiUsage.value.by_provider.length ? aiUsage.value.by_provider : [{ provider: 'mock', count: 0 }]
))

const readinessStatusText = computed(() => (
  readiness.value.status === 'ready' ? '可试运行' : '需要处理'
))
const overallTagType = computed(() => (
  readiness.value.status === 'ready' ? 'success' : 'danger'
))
const runbookTagType = computed(() => (
  trialRunbook.value.status === 'ready' ? 'success' : 'danger'
))

function itemTagType(status: TrialReadinessItemStatus) {
  if (status === 'ok') return 'success'
  if (status === 'warning') return 'warning'
  return 'danger'
}

function itemStatusText(status: TrialReadinessItemStatus) {
  if (status === 'ok') return '正常'
  if (status === 'warning') return '提醒'
  return '阻断'
}

function recordStatusText(status: TrialRunbookRecordStatus) {
  const map: Record<TrialRunbookRecordStatus, string> = {
    checked: '已检查',
    blocked: '有阻断',
    skipped: '已跳过'
  }
  return map[status]
}

function recordTagType(status: TrialRunbookRecordStatus) {
  if (status === 'checked') return 'success'
  if (status === 'blocked') return 'warning'
  return 'info'
}

function stageTitle(stageKey: string) {
  return trialRunbook.value.stages.find((stage) => stage.key === stageKey)?.title || stageKey
}

function openRecordDialog(stage: TrialOperationsStage) {
  selectedRunbookStage.value = stage
  recordForm.value = {
    status: stage.status === 'error' ? 'blocked' : 'checked',
    note: '',
    evidence: [...stage.evidence]
  }
  recordDialogVisible.value = true
}

async function submitRunbookRecord() {
  if (!selectedRunbookStage.value) return
  recordSubmitting.value = true
  try {
    await createTrialRunbookRecord(selectedRunbookStage.value.key, recordForm.value)
    ElMessage.success('演练记录已保存')
    recordDialogVisible.value = false
    const recordsRes = await getTrialRunbookRecords({ page: 1, page_size: 6 })
    recentRunbookRecords.value = recordsRes.data.items
  } catch (error) {
    ElMessage.error('演练记录保存失败')
  } finally {
    recordSubmitting.value = false
  }
}

function goTo(route: string) {
  router.push(route)
}

async function loadData() {
  loading.value = true
  try {
    const [overviewRes, trendsRes, aiRes, readinessRes, runbookRes, recordsRes] = await Promise.all([
      getDashboardOverview(),
      getProjectTrends(),
      getAIUsage(),
      getTrialReadiness(),
      getTrialOperationsRunbook(),
      getTrialRunbookRecords({ page: 1, page_size: 6 })
    ])
    overview.value = overviewRes.data
    trends.value = trendsRes.data
    aiUsage.value = aiRes.data
    readiness.value = readinessRes.data
    trialRunbook.value = runbookRes.data
    recentRunbookRecords.value = recordsRes.data.items
  } catch (e: any) {
    ElMessage.error(e?.message || '加载驾驶舱数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.admin-dashboard {
  display: grid;
  gap: 16px;
}

.header-band,
.metric-card,
.section-card,
.readiness-panel,
.runbook-panel {
  border-radius: 8px;
  background: #fff;
}

.header-band {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border: 1px solid #e4e7ed;
}

.header-band h1 {
  margin: 4px 0 8px;
  color: #1f2f5f;
  font-size: 24px;
}

.header-band p,
.readiness-head p {
  margin: 0;
  color: #606266;
}

.eyebrow {
  color: #245cff !important;
  font-size: 13px;
  font-weight: 700;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  border: 1px solid #e4e7ed;
}

.metric-card span,
.metric-card em {
  color: #606266;
  font-style: normal;
  font-size: 12px;
}

.metric-card strong {
  display: block;
  margin: 8px 0;
  color: #1f2f5f;
  font-size: 28px;
}

.readiness-panel {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid #e4e7ed;
}

.readiness-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.readiness-head h2 {
  margin: 4px 0 8px;
  color: #1f2f5f;
  font-size: 20px;
}

.runbook-panel {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid #e4e7ed;
}

.runbook-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.runbook-head h2 {
  margin: 4px 0 8px;
  color: #1f2f5f;
  font-size: 20px;
}

.runbook-head p {
  margin: 0;
  color: #606266;
}

.runbook-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.runbook-stage {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fbfcff;
}

.stage-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-top h3 {
  margin: 0;
  color: #1f2f5f;
  font-size: 15px;
}

.runbook-stage dl {
  display: grid;
  gap: 8px;
  margin: 0;
}

.runbook-stage dt {
  color: #6b7280;
  font-size: 12px;
}

.runbook-stage dd {
  margin: 2px 0 0;
  color: #303133;
  font-size: 13px;
}

.runbook-stage dd span {
  display: block;
  line-height: 1.5;
}

.stage-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recent-runbook-records {
  padding-top: 14px;
  border-top: 1px solid #e4e7ed;
}

.recent-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.recent-head h3 {
  margin: 0;
  color: #1f2f5f;
  font-size: 15px;
}

.recent-head span {
  color: #606266;
  font-size: 13px;
}

.record-list {
  display: grid;
  gap: 8px;
}

.record-item {
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
}

.record-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.record-meta strong,
.record-dialog h3 {
  color: #1f2f5f;
  font-size: 14px;
}

.record-meta span,
.record-item p {
  color: #606266;
  font-size: 13px;
}

.record-item p {
  margin: 0;
}

.dialog-evidence {
  display: grid;
  gap: 6px;
  width: 100%;
}

.dialog-evidence span {
  padding: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  color: #303133;
  font-size: 13px;
}

.readiness-summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  color: #606266;
  font-size: 13px;
}

.checklist {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.check-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-height: 112px;
  padding: 14px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fbfcff;
}

.check-main {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
}

.check-main h3 {
  margin: 0 0 6px;
  color: #1f2f5f;
  font-size: 15px;
}

.check-main p {
  margin: 0 0 8px;
  color: #606266;
  line-height: 1.5;
}

.check-main span {
  color: #303133;
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ai-note {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
  padding: 14px;
  border-radius: 8px;
  background: #f5f7fa;
}

.ai-note strong {
  color: #245cff;
  font-size: 26px;
}

.ai-note span {
  color: #606266;
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .metric-grid,
  .content-grid,
  .checklist {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .header-band,
  .readiness-head,
  .runbook-head,
  .check-item {
    flex-direction: column;
    align-items: stretch;
  }

  .metric-grid,
  .content-grid,
  .checklist {
    grid-template-columns: 1fr;
  }

  .readiness-summary {
    justify-content: flex-start;
  }
}
</style>
