<template>
  <div class="call-page">
    <section class="page-head">
      <div>
        <span class="eyebrow">AI调用观测</span>
        <h1>AI调用记录与链路观测</h1>
        <p>跟踪每一次智能体调用的场景、Provider链路、思考进度、采纳状态和错误排查信息，支撑后续桂教通与本地模型统一接入。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadCalls">刷新</el-button>
    </section>

    <section class="summary-row">
      <div class="summary-item">
        <strong>{{ pagination.total }}</strong>
        <span>调用总数</span>
      </div>
      <div class="summary-item">
        <strong>{{ succeededCount }}</strong>
        <span>本页成功</span>
      </div>
      <div class="summary-item">
        <strong>{{ adoptedCount }}</strong>
        <span>本页已采纳</span>
      </div>
      <div class="summary-item">
        <strong>{{ failedCount }}</strong>
        <span>本页失败</span>
      </div>
    </section>

    <section class="diagnostics-row">
      <div class="summary-item">
        <strong>{{ diagnosticsSummary?.total_failed || 0 }}</strong>
        <span>失败诊断</span>
      </div>
      <div class="summary-item">
        <strong>{{ topFailureCategoryLabel }}</strong>
        <span>最高失败类别</span>
      </div>
      <div class="summary-item">
        <strong>{{ affectedProviderCount }}</strong>
        <span>受影响 Provider</span>
      </div>
      <div class="summary-item recent-failures">
        <strong>近期失败</strong>
        <span v-if="recentFailureText">{{ recentFailureText }}</span>
        <span v-else>暂无失败记录</span>
      </div>
    </section>

    <section class="observability-strip">
      <div class="observability-item">
        <span>调用链路</span>
        <strong>场景 -> Provider -> 状态 -> 教师审阅/采纳</strong>
        <p>管理员可按场景、Provider 和状态筛选，快速定位一次 AI 能力进入业务系统的位置。</p>
      </div>
      <div class="observability-item">
        <span>思考进度</span>
        <strong>读取 / 生成 / 标准化 / 等待教师审阅</strong>
        <p>详情抽屉会读取调用进度接口，展示智能体思考读条和每一步状态。</p>
      </div>
      <div class="observability-item">
        <span>错误排查</span>
        <strong>失败调用保留 Provider、状态、错误信息</strong>
        <p>只展示排障所需的非敏感信息，密钥和 Token 不进入浏览器可见数据。</p>
      </div>
    </section>

    <section class="ledger-panel">
      <div class="toolbar">
        <strong>调用台账</strong>
        <div class="filters">
          <el-select v-model="filters.scenario" clearable placeholder="场景" class="filter" @change="reloadFirstPage">
            <el-option v-for="item in scenarioOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filters.provider" clearable placeholder="Provider" class="filter" @change="reloadFirstPage">
            <el-option v-for="item in providerOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filters.status" clearable placeholder="调用状态" class="filter" @change="reloadFirstPage">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filters.error_category" clearable placeholder="失败类别" class="filter" @change="reloadFirstPage">
            <el-option v-for="item in errorCategoryOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
      </div>

      <el-table :data="calls" v-loading="loading" class="call-table" row-key="id" @row-click="viewDetail">
        <el-table-column label="场景" width="150">
          <template #default="{ row }">{{ scenarioText(row.scenario) }}</template>
        </el-table-column>
        <el-table-column label="智能体" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="agent-name">
              <strong>{{ row.agent_name || '未命名智能体' }}</strong>
              <span>{{ row.agent_id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Provider链路" width="140">
          <template #default="{ row }">
            <el-tag :type="providerTagType(row.provider)" effect="light">{{ providerText(row.provider) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="调用状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="失败类别" width="150" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.error_category" type="danger" effect="light">{{ errorCategoryText(row.error_category) }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="采纳状态" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="adoptionTagType(row)" effect="light">{{ adoptionText(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="输入摘要" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ row.input_summary || '-' }}</template>
        </el-table-column>
        <el-table-column label="输出摘要" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ row.output_summary || '-' }}</template>
        </el-table-column>
        <el-table-column label="时间" width="170" align="center">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="viewDetail(row)">查看链路</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无 AI 调用记录">
            <el-button :icon="Refresh" @click="loadCalls">刷新台账</el-button>
          </el-empty>
        </template>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          background
          layout="total, sizes, prev, pager, next"
          @current-change="loadCalls"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <el-drawer v-model="detailVisible" title="调用详情" size="680px">
      <template v-if="selected">
        <div class="detail-head">
          <div>
            <h2>{{ selected.agent_name || '未命名智能体' }}</h2>
            <p>{{ scenarioText(selected.scenario) }} / {{ providerText(selected.provider) }}</p>
          </div>
          <el-tag :type="statusTagType(selected.status)" effect="light">{{ statusText(selected.status) }}</el-tag>
        </div>

        <section class="detail-section">
          <h3>Provider链路</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="调用ID">{{ selected.id }}</el-descriptions-item>
            <el-descriptions-item label="场景">{{ scenarioText(selected.scenario) }}</el-descriptions-item>
            <el-descriptions-item label="Provider">{{ providerText(selected.provider) }}</el-descriptions-item>
            <el-descriptions-item label="调用状态">{{ statusText(selected.status) }}</el-descriptions-item>
            <el-descriptions-item label="采纳状态">{{ adoptionText(selected) }}</el-descriptions-item>
            <el-descriptions-item label="项目ID">{{ selected.project_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(selected.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="detail-section">
          <h3>思考进度</h3>
          <div v-loading="progressLoading" class="progress-panel">
            <template v-if="progress">
              <div class="progress-head">
                <span>{{ progress.percent }}%</span>
                <el-progress :percentage="progress.percent" :stroke-width="8" />
              </div>
              <div v-if="progress.steps.length" class="step-list">
                <div v-for="step in progress.steps" :key="step.id">
                  <span>{{ step.percent }}%</span>
                  <div>
                    <strong>{{ step.title }}</strong>
                    <p>{{ step.description || statusText(step.status) }}</p>
                  </div>
                  <el-tag size="small" :type="stepStatusTagType(step.status)" effect="light">
                    {{ stepStatusText(step.status) }}
                  </el-tag>
                </div>
              </div>
              <el-empty v-else description="该调用暂无思考进度记录" />
            </template>
            <el-empty v-else description="打开详情后会读取思考进度" />
          </div>
        </section>

        <section class="detail-section">
          <h3>教师采纳门槛</h3>
          <p class="muted">AI 输出不能直接发布给学生；只有教师审阅并采纳后，才会进入项目、任务、量规或资源等业务对象。</p>
        </section>

        <section class="detail-section">
          <h3>失败诊断</h3>
          <div v-if="hasSelectedDiagnostics" class="diagnostic-panel">
            <div>
              <span>失败类别</span>
              <strong>{{ errorCategoryText(selectedErrorCategory) }}</strong>
            </div>
            <div>
              <span>可重试</span>
              <strong>{{ retryableText(selectedDiagnostics.retryable) }}</strong>
            </div>
            <div>
              <span>处理建议</span>
              <strong>{{ selectedDiagnostics.remediation || selected.error_message || '查看 Provider 配置和调用记录后处理。' }}</strong>
            </div>
            <div>
              <span>上游状态</span>
              <strong>{{ selectedDiagnostics.upstream_status ?? '-' }}</strong>
            </div>
            <pre v-if="hasSelectedSafeMetadata" class="json-block compact">{{ prettyJson(selectedSafeMetadata) }}</pre>
          </div>
          <el-alert
            v-if="selected.error_message"
            type="error"
            :title="selected.error_message"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            type="success"
            title="当前调用未记录错误信息"
            show-icon
            :closable="false"
          />
        </section>

        <section class="detail-section">
          <h3>请求载荷</h3>
          <pre class="json-block">{{ prettyJson(selected.request_payload || {}) }}</pre>
        </section>

        <section class="detail-section">
          <h3>响应载荷</h3>
          <pre class="json-block">{{ prettyJson(selected.response_payload || {}) }}</pre>
        </section>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getAdminAICalls } from '@/api/admin'
import { getAICallDiagnosticsSummary, getAICallProgress } from '@/api/ai'
import type { AICallDiagnosticMetadata, AICallDiagnosticsSummary, AICallItem, AICallProgress } from '@/api/ai'

const scenarioOptions = [
  { label: 'AI教学方案', value: 'lesson_plan' },
  { label: '学情诊断', value: 'learning_diagnosis' },
  { label: '量规生成', value: 'rubric_generation' },
  { label: '资源推荐', value: 'resource_recommendation' },
  { label: '教学反思', value: 'teaching_reflection' }
]

const providerOptions = [
  { label: 'Mock 本地', value: 'mock' },
  { label: '桂教通 API', value: 'gjt_api' },
  { label: '桂教通链接', value: 'gjt_link' },
  { label: '人工导入', value: 'manual_import' }
]

const statusOptions = [
  { label: '已创建', value: 'created' },
  { label: '运行中', value: 'running' },
  { label: '成功', value: 'succeeded' },
  { label: '已导入', value: 'imported' },
  { label: '已审阅', value: 'reviewed' },
  { label: '已采纳', value: 'adopted' },
  { label: '失败', value: 'failed' }
]

const errorCategoryOptions = [
  { label: '配置缺失', value: 'configuration_missing' },
  { label: 'Provider未支持', value: 'provider_unsupported' },
  { label: '上游不可达', value: 'upstream_unreachable' },
  { label: '上游超时', value: 'upstream_timeout' },
  { label: '上游响应异常', value: 'upstream_bad_response' },
  { label: '契约校验失败', value: 'contract_validation_failed' },
  { label: '未知错误', value: 'unknown_error' }
]

const calls = ref<AICallItem[]>([])
const selected = ref<AICallItem | null>(null)
const progress = ref<AICallProgress | null>(null)
const diagnosticsSummary = ref<AICallDiagnosticsSummary | null>(null)
const loading = ref(false)
const progressLoading = ref(false)
const detailVisible = ref(false)
const filters = reactive({ scenario: '', provider: '', status: '', error_category: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const succeededCount = computed(() => calls.value.filter(item => item.status === 'succeeded').length)
const adoptedCount = computed(() => calls.value.filter(item => item.status === 'adopted').length)
const failedCount = computed(() => calls.value.filter(item => item.status === 'failed').length)
const affectedProviderCount = computed(() => diagnosticsSummary.value?.by_provider.length || 0)
const topFailureCategoryLabel = computed(() => {
  const top = diagnosticsSummary.value?.by_category[0]
  return top ? `${errorCategoryText(top.category)} ${top.count}` : '-'
})
const recentFailureText = computed(() => {
  const item = diagnosticsSummary.value?.recent_failures[0]
  if (!item) return ''
  return `${providerText(item.provider)} / ${errorCategoryText(item.error_category)} / ${formatDate(item.created_at)}`
})
const selectedDiagnostics = computed<AICallDiagnosticMetadata>(() => selected.value?.diagnostic_metadata || {})
const selectedErrorCategory = computed(() => selected.value?.error_category || selectedDiagnostics.value.error_category || '')
const hasSelectedDiagnostics = computed(() => Boolean(
  selectedErrorCategory.value ||
  selectedDiagnostics.value.remediation ||
  selected.value?.error_message
))
const selectedSafeMetadata = computed(() => selectedDiagnostics.value.safe_metadata || {})
const hasSelectedSafeMetadata = computed(() => Object.keys(selectedSafeMetadata.value).length > 0)

async function loadCalls() {
  loading.value = true
  try {
    const [callsRes, summaryRes] = await Promise.all([
      getAdminAICalls({
        page: pagination.page,
        page_size: pagination.pageSize,
        scenario: filters.scenario || undefined,
        provider: filters.provider || undefined,
        status: filters.status || undefined,
        error_category: filters.error_category || undefined
      }),
      getAICallDiagnosticsSummary()
    ])
    calls.value = callsRes.data.items || []
    pagination.total = callsRes.data.total || 0
    diagnosticsSummary.value = summaryRes.data
  } finally {
    loading.value = false
  }
}

function reloadFirstPage() {
  pagination.page = 1
  loadCalls()
}

function handleSizeChange() {
  pagination.page = 1
  loadCalls()
}

async function viewDetail(row: AICallItem) {
  selected.value = row
  progress.value = null
  detailVisible.value = true
  progressLoading.value = true
  try {
    const res = await getAICallProgress(row.id)
    progress.value = res.data
  } catch (error) {
    ElMessage.warning('思考进度暂时不可用')
  } finally {
    progressLoading.value = false
  }
}

function scenarioText(value?: string) {
  return scenarioOptions.find(item => item.value === value)?.label || value || '-'
}

function providerText(value?: string) {
  return providerOptions.find(item => item.value === value)?.label || value || '-'
}

function statusText(value?: string) {
  return statusOptions.find(item => item.value === value)?.label || value || '-'
}

function errorCategoryText(value?: string | null) {
  return errorCategoryOptions.find(item => item.value === value)?.label || value || '-'
}

function retryableText(value?: boolean) {
  if (value === true) return '可重试'
  if (value === false) return '不可重试'
  return '-'
}

function stepStatusText(value?: string) {
  const mapping: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return value ? mapping[value] || value : '-'
}

function adoptionText(row: AICallItem) {
  if (row.status === 'adopted') return '已采纳'
  if (row.review_status === 'approved') return '已审阅待采纳'
  if (row.review_status === 'rejected') return '已驳回'
  return '待教师确认'
}

function providerTagType(value?: string) {
  if (value === 'mock') return 'success'
  if (value === 'gjt_api' || value === 'gjt_link') return 'warning'
  return 'info'
}

function statusTagType(value?: string) {
  if (value === 'succeeded' || value === 'imported' || value === 'reviewed') return 'success'
  if (value === 'adopted') return 'primary'
  if (value === 'failed') return 'danger'
  return 'info'
}

function adoptionTagType(row: AICallItem) {
  if (row.status === 'adopted') return 'success'
  if (row.review_status === 'approved') return 'warning'
  if (row.review_status === 'rejected') return 'danger'
  return 'info'
}

function stepStatusTagType(value?: string) {
  if (value === 'completed') return 'success'
  if (value === 'running') return 'warning'
  if (value === 'failed') return 'danger'
  return 'info'
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2)
}

onMounted(loadCalls)
</script>

<style scoped>
.call-page {
  display: grid;
  gap: 16px;
}

.page-head,
.toolbar,
.filters,
.pagination-wrapper,
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-head,
.summary-item,
.observability-item,
.ledger-panel {
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #fff;
}

.page-head {
  align-items: flex-start;
  padding: 20px 24px;
}

.eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.page-head h1 {
  margin: 6px 0 8px;
  color: #17233c;
  font-size: 24px;
}

.page-head p,
.observability-item p,
.muted,
.step-list p {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.diagnostics-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-item {
  display: grid;
  gap: 4px;
  padding: 16px;
  min-width: 0;
}

.summary-item strong {
  color: #17233c;
  font-size: 26px;
}

.summary-item span {
  color: #64748b;
}

.recent-failures strong,
.recent-failures span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.observability-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.observability-item {
  display: grid;
  gap: 8px;
  padding: 16px;
}

.observability-item span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
}

.observability-item strong {
  color: #1f3356;
}

.ledger-panel {
  padding: 16px;
}

.toolbar {
  align-items: flex-start;
}

.toolbar > strong,
.detail-section h3,
.detail-head h2,
.agent-name strong {
  color: #1f3356;
}

.filters {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.filter {
  width: 150px;
}

.call-table {
  margin-top: 14px;
}

.agent-name {
  display: grid;
  gap: 4px;
}

.agent-name span {
  color: #94a3b8;
  font-size: 12px;
}

.pagination-wrapper {
  justify-content: flex-end;
  margin-top: 16px;
}

.detail-head {
  align-items: flex-start;
  margin-bottom: 16px;
}

.detail-head h2 {
  margin: 0 0 6px;
  font-size: 20px;
}

.detail-head p {
  margin: 0;
  color: #64748b;
}

.detail-section {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.detail-section h3 {
  margin: 0;
  font-size: 15px;
}

.progress-panel {
  min-height: 96px;
  padding: 12px;
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #f8fafc;
}

.progress-head {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
}

.progress-head span,
.step-list > div > span {
  color: #2563eb;
  font-weight: 700;
}

.step-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.step-list > div {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: start;
  padding: 10px;
  border-radius: 8px;
  background: #fff;
}

.step-list strong {
  color: #1f3356;
}

.diagnostic-panel {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid #fee2e2;
  border-radius: 8px;
  background: #fff7f7;
}

.diagnostic-panel > div {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.diagnostic-panel span {
  color: #991b1b;
  font-size: 12px;
  font-weight: 700;
}

.diagnostic-panel strong {
  min-width: 0;
  color: #334155;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.json-block {
  max-height: 260px;
  overflow: auto;
  padding: 14px;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
}

.json-block.compact {
  max-height: 180px;
  margin: 0;
}

@media (max-width: 1100px) {
  .summary-row,
  .diagnostics-row,
  .observability-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page-head,
  .toolbar,
  .filters {
    display: grid;
    width: 100%;
  }

  .filter {
    width: 100%;
  }
}
</style>
