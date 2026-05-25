<template>
  <div class="agent-page">
    <section class="page-head">
      <div>
        <span class="eyebrow">AI Agent Admin</span>
        <h1>AI智能体配置</h1>
        <p>维护本地智能体契约、Provider配置和业务场景启用状态。</p>
      </div>
      <div class="head-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadAll">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建智能体</el-button>
      </div>
    </section>

    <section class="summary-row">
      <div class="summary-item">
        <strong>{{ total }}</strong>
        <span>智能体配置</span>
      </div>
      <div class="summary-item">
        <strong>{{ enabledCount }}</strong>
        <span>已启用</span>
      </div>
      <div class="summary-item">
        <strong>{{ contracts.length }}</strong>
        <span>本地契约</span>
      </div>
    </section>

    <section class="content-grid">
      <div class="main-panel">
        <div class="toolbar">
          <el-select v-model="filters.scenario" clearable placeholder="场景" class="filter">
            <el-option v-for="item in scenarioOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filters.provider" clearable placeholder="Provider" class="filter">
            <el-option v-for="item in providerOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filters.enabled" clearable placeholder="启用状态" class="filter">
            <el-option label="已启用" value="true" />
            <el-option label="已停用" value="false" />
          </el-select>
          <el-button :icon="Search" @click="loadAgents">筛选</el-button>
        </div>

        <el-table v-loading="loading" :data="agents" class="agent-table" row-key="id" @row-click="openDetail">
          <el-table-column label="智能体" min-width="210">
            <template #default="{ row }">
              <div class="agent-name">
                <strong>{{ row.name }}</strong>
                <span>{{ scenarioText(row.scenario) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="Provider" width="130">
            <template #default="{ row }">
              <el-tag effect="light">{{ providerText(row.provider) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="模型/端点" min-width="170">
            <template #default="{ row }">
              <span class="muted">{{ row.config?.model || row.config?.endpoint || '未配置' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-switch
                :model-value="row.enabled"
                :loading="switchingId === row.id"
                @click.stop
                @change="value => toggleEnabled(row, Boolean(value))"
              />
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="130">
            <template #default="{ row }">
              <span class="muted">{{ formatDate(row.updated_at || row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-tooltip content="查看详情">
                <el-button :icon="View" circle text @click.stop="openDetail(row)" />
              </el-tooltip>
              <el-tooltip content="编辑">
                <el-button :icon="Edit" circle text @click.stop="openEdit(row)" />
              </el-tooltip>
              <el-tooltip content="删除">
                <el-button :icon="Delete" circle text type="danger" @click.stop="removeAgent(row)" />
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-row">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next, total"
            @current-change="loadAgents"
          />
        </div>
      </div>

      <aside class="contract-panel">
        <div class="panel-title">
          <el-icon><Document /></el-icon>
          <span>本地契约</span>
        </div>
        <div class="contract-list">
          <button
            v-for="contract in contracts"
            :key="contract.scenario"
            class="contract-item"
            :class="{ active: selectedContractScenario === contract.scenario }"
            type="button"
            @click="selectedContractScenario = contract.scenario"
          >
            <strong>{{ scenarioText(contract.scenario) }}</strong>
            <span>{{ contract.version }}</span>
          </button>
        </div>
        <div v-if="selectedContract" class="contract-detail">
          <p>{{ selectedContract.adoption_rule }}</p>
          <div class="step-list">
            <div v-for="step in selectedContract.thinking_steps" :key="step.code">
              <span>{{ step.percent }}%</span>
              <strong>{{ step.title }}</strong>
            </div>
          </div>
        </div>
      </aside>
    </section>

    <el-drawer v-model="detailVisible" size="520px" title="智能体详情">
      <template v-if="selectedAgent">
        <div class="detail-head">
          <div>
            <h2>{{ selectedAgent.name }}</h2>
            <p>{{ scenarioText(selectedAgent.scenario) }} / {{ providerText(selectedAgent.provider) }}</p>
          </div>
          <el-tag :type="selectedAgent.enabled ? 'success' : 'info'" effect="light">
            {{ selectedAgent.enabled ? '已启用' : '已停用' }}
          </el-tag>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="模型">{{ selectedAgent.config?.model || '未配置' }}</el-descriptions-item>
          <el-descriptions-item label="端点">{{ selectedAgent.config?.endpoint || '未配置' }}</el-descriptions-item>
          <el-descriptions-item label="认证方式">{{ selectedAgent.config?.auth_type || '未配置' }}</el-descriptions-item>
          <el-descriptions-item label="超时/重试">
            {{ selectedAgent.config?.timeout_seconds || 30 }} 秒 / {{ selectedAgent.config?.max_retries || 1 }} 次
          </el-descriptions-item>
        </el-descriptions>
        <div class="json-block">
          <strong>Provider扩展配置</strong>
          <pre>{{ prettyJson(selectedAgent.config?.extra || {}) }}</pre>
        </div>
        <div class="json-block">
          <strong>输入契约</strong>
          <pre>{{ prettyJson(selectedAgent.input_schema || activeContract?.input_contract || {}) }}</pre>
        </div>
        <div class="json-block">
          <strong>输出契约</strong>
          <pre>{{ prettyJson(selectedAgent.output_schema || activeContract?.output_contract || {}) }}</pre>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="formVisible" :title="editingId ? '编辑智能体' : '新建智能体'" width="760px">
      <el-form ref="formRef" :model="form" label-position="top">
        <div class="two-cols">
          <el-form-item label="智能体名称" required>
            <el-input v-model="form.name" maxlength="128" />
          </el-form-item>
          <el-form-item label="业务场景" required>
            <el-select v-model="form.scenario" @change="applyContractDefaults">
              <el-option v-for="item in scenarioOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </div>
        <div class="two-cols">
          <el-form-item label="Provider" required>
            <el-select v-model="form.provider" @change="syncProvider">
              <el-option v-for="item in providerOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="启用状态">
            <el-switch v-model="form.enabled" />
          </el-form-item>
        </div>
        <div class="two-cols">
          <el-form-item label="模型名称">
            <el-input v-model="form.config.model" placeholder="mock、gjt-agent-id 等" />
          </el-form-item>
          <el-form-item label="接口端点">
            <el-input v-model="form.config.endpoint" placeholder="预留给桂教通 API" />
          </el-form-item>
        </div>
        <div class="three-cols">
          <el-form-item label="认证方式">
            <el-select v-model="form.config.auth_type" clearable placeholder="未配置">
              <el-option label="Bearer Token" value="bearer" />
              <el-option label="API Key" value="api_key" />
              <el-option label="平台单点登录" value="sso" />
            </el-select>
          </el-form-item>
          <el-form-item label="超时秒数">
            <el-input-number v-model="form.config.timeout_seconds" :min="1" :max="300" />
          </el-form-item>
          <el-form-item label="最大重试">
            <el-input-number v-model="form.config.max_retries" :min="0" :max="5" />
          </el-form-item>
        </div>
        <el-alert
          type="info"
          show-icon
          :closable="false"
          title="桂教通字段目前只做占位保存：endpoint、auth_type、extra，不在前端直接暴露密钥。"
        />
        <el-form-item label="Provider扩展配置 JSON">
          <el-input v-model="extraText" type="textarea" :rows="4" />
        </el-form-item>
        <div class="two-cols">
          <el-form-item label="输入 Schema JSON">
            <el-input v-model="inputSchemaText" type="textarea" :rows="8" />
          </el-form-item>
          <el-form-item label="输出 Schema JSON">
            <el-input v-model="outputSchemaText" type="textarea" :rows="8" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Delete, Document, Edit, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { createAgent, deleteAgent, getAgents, getAIContracts, updateAgent } from '@/api/ai'
import type { AgentConfig, AIAgent, AIAgentMutation, AIContract } from '@/api/ai'

type Provider = AIAgent['provider']

const scenarioOptions = [
  { label: 'AI教学方案', value: 'lesson_plan' },
  { label: '学情诊断', value: 'learning_diagnosis' },
  { label: '量规生成', value: 'rubric_generation' },
  { label: '资源推荐', value: 'resource_recommendation' },
  { label: '教学反思', value: 'teaching_reflection' }
]

const providerOptions: { label: string; value: Provider }[] = [
  { label: 'Mock 本地', value: 'mock' },
  { label: '桂教通 API', value: 'gjt_api' },
  { label: '桂教通链接', value: 'gjt_link' },
  { label: '人工导入', value: 'manual_import' }
]

const loading = ref(false)
const saving = ref(false)
const switchingId = ref('')
const agents = ref<AIAgent[]>([])
const contracts = ref<AIContract[]>([])
const selectedContractScenario = ref('lesson_plan')
const selectedAgent = ref<AIAgent | null>(null)
const detailVisible = ref(false)
const formVisible = ref(false)
const editingId = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const formRef = ref<FormInstance>()
const extraText = ref('{}')
const inputSchemaText = ref('{}')
const outputSchemaText = ref('{}')

const filters = reactive({
  scenario: '',
  provider: '',
  enabled: ''
})

const form = reactive<AIAgentMutation>({
  name: '',
  provider: 'mock',
  scenario: 'lesson_plan',
  config: makeDefaultConfig('mock'),
  input_schema: {},
  output_schema: {},
  enabled: true
})

const enabledCount = computed(() => agents.value.filter(item => item.enabled).length)
const selectedContract = computed(() => contracts.value.find(item => item.scenario === selectedContractScenario.value))
const activeContract = computed(() => selectedAgent.value ? contracts.value.find(item => item.scenario === selectedAgent.value?.scenario) : null)

function makeDefaultConfig(provider: Provider): AgentConfig {
  return {
    provider,
    model: provider === 'mock' ? 'mock' : null,
    endpoint: null,
    auth_type: null,
    timeout_seconds: 30,
    max_retries: 1,
    extra: {}
  }
}

async function loadAll() {
  await Promise.all([loadContracts(), loadAgents()])
}

async function loadContracts() {
  const res = await getAIContracts()
  contracts.value = res.data.items || []
  if (!selectedContractScenario.value && contracts.value.length) {
    selectedContractScenario.value = contracts.value[0].scenario
  }
}

async function loadAgents() {
  loading.value = true
  try {
    const res = await getAgents({
      scenario: filters.scenario || undefined,
      provider: filters.provider || undefined,
      enabled: filters.enabled === '' ? undefined : filters.enabled === 'true',
      page: page.value,
      page_size: pageSize
    })
    agents.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = ''
  Object.assign(form, {
    name: '',
    provider: 'mock',
    scenario: selectedContractScenario.value || 'lesson_plan',
    config: makeDefaultConfig('mock'),
    input_schema: {},
    output_schema: {},
    enabled: true
  })
  applyContractDefaults()
  formVisible.value = true
}

function openEdit(agent: AIAgent) {
  editingId.value = agent.id
  Object.assign(form, {
    name: agent.name,
    provider: agent.provider,
    scenario: agent.scenario,
    config: { ...makeDefaultConfig(agent.provider), ...(agent.config || {}) },
    input_schema: agent.input_schema || {},
    output_schema: agent.output_schema || {},
    enabled: agent.enabled
  })
  extraText.value = prettyJson(form.config.extra || {})
  inputSchemaText.value = prettyJson(form.input_schema || {})
  outputSchemaText.value = prettyJson(form.output_schema || {})
  formVisible.value = true
}

function openDetail(agent: AIAgent) {
  selectedAgent.value = agent
  selectedContractScenario.value = agent.scenario
  detailVisible.value = true
}

function applyContractDefaults() {
  const contract = contracts.value.find(item => item.scenario === form.scenario)
  selectedContractScenario.value = form.scenario
  inputSchemaText.value = prettyJson(contract?.input_contract || form.input_schema || {})
  outputSchemaText.value = prettyJson(contract?.output_contract || form.output_schema || {})
  extraText.value = prettyJson(form.config.extra || {})
}

function syncProvider() {
  form.config.provider = form.provider
  if (form.provider === 'mock' && !form.config.model) form.config.model = 'mock'
}

async function submitForm() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写智能体名称')
    return
  }

  let extra: Record<string, any>
  let inputSchema: Record<string, any>
  let outputSchema: Record<string, any>
  try {
    extra = parseJsonObject(extraText.value, 'Provider扩展配置')
    inputSchema = parseJsonObject(inputSchemaText.value, '输入 Schema')
    outputSchema = parseJsonObject(outputSchemaText.value, '输出 Schema')
  } catch (error: any) {
    ElMessage.error(error.message)
    return
  }

  saving.value = true
  try {
    const payload: AIAgentMutation = {
      name: form.name.trim(),
      provider: form.provider,
      scenario: form.scenario,
      config: { ...form.config, provider: form.provider, extra },
      input_schema: inputSchema,
      output_schema: outputSchema,
      enabled: form.enabled
    }
    if (editingId.value) {
      await updateAgent(editingId.value, payload)
      ElMessage.success('智能体已更新')
    } else {
      await createAgent(payload)
      ElMessage.success('智能体已创建')
    }
    formVisible.value = false
    await loadAgents()
  } finally {
    saving.value = false
  }
}

async function toggleEnabled(agent: AIAgent, enabled: boolean) {
  switchingId.value = agent.id
  try {
    await updateAgent(agent.id, { enabled })
    agent.enabled = enabled
    ElMessage.success(enabled ? '智能体已启用' : '智能体已停用')
  } finally {
    switchingId.value = ''
  }
}

async function removeAgent(agent: AIAgent) {
  await ElMessageBox.confirm(`确认删除“${agent.name}”？删除后列表不再显示。`, '删除智能体', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消'
  })
  await deleteAgent(agent.id)
  ElMessage.success('智能体已删除')
  await loadAgents()
}

function parseJsonObject(value: string, label: string): Record<string, any> {
  const parsed = JSON.parse(value || '{}')
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error(`${label} 必须是 JSON 对象`)
  }
  return parsed
}

function scenarioText(value: string) {
  return scenarioOptions.find(item => item.value === value)?.label || value
}

function providerText(value: string) {
  return providerOptions.find(item => item.value === value)?.label || value
}

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2)
}

function formatDate(value?: string) {
  return value ? value.slice(0, 10) : '-'
}

onMounted(loadAll)
</script>

<style scoped>
.agent-page {
  display: grid;
  gap: 16px;
}

.page-head,
.head-actions,
.toolbar,
.pagination-row,
.panel-title,
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.page-head h1 {
  margin: 6px 0 8px;
  color: #17233c;
  font-size: 24px;
}

.page-head p,
.muted,
.detail-head p,
.contract-detail p {
  color: #64748b;
  line-height: 1.6;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-item,
.main-panel,
.contract-panel {
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #fff;
}

.summary-item {
  display: grid;
  gap: 4px;
  padding: 16px;
}

.summary-item strong {
  color: #17233c;
  font-size: 26px;
}

.summary-item span {
  color: #64748b;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
}

.main-panel,
.contract-panel {
  padding: 16px;
}

.filter {
  width: 150px;
}

.agent-table {
  margin-top: 14px;
}

.agent-name {
  display: grid;
  gap: 4px;
}

.agent-name strong,
.panel-title,
.detail-head h2,
.json-block strong {
  color: #1f3356;
}

.agent-name span {
  color: #7b8ba6;
  font-size: 12px;
}

.pagination-row {
  justify-content: flex-end;
  margin-top: 14px;
}

.contract-panel {
  align-content: start;
  display: grid;
  gap: 14px;
}

.panel-title {
  justify-content: flex-start;
  font-weight: 700;
}

.contract-list {
  display: grid;
  gap: 8px;
}

.contract-item {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.contract-item.active {
  border-color: #2563eb;
  background: #eff6ff;
}

.contract-item span {
  color: #64748b;
  font-size: 12px;
}

.step-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.step-list div {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 8px;
  color: #334155;
}

.step-list span {
  color: #2563eb;
  font-weight: 700;
}

.detail-head {
  align-items: flex-start;
  margin-bottom: 16px;
}

.json-block {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.json-block pre {
  max-height: 240px;
  overflow: auto;
  padding: 12px;
  border-radius: 8px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
}

.two-cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.three-cols {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.two-cols :deep(.el-select),
.three-cols :deep(.el-select),
.three-cols :deep(.el-input-number) {
  width: 100%;
}

@media (max-width: 1100px) {
  .content-grid,
  .summary-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page-head,
  .head-actions,
  .toolbar,
  .two-cols,
  .three-cols {
    display: grid;
    width: 100%;
  }

  .filter {
    width: 100%;
  }
}
</style>
