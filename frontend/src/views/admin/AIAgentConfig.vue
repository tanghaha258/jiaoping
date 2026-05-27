<template>
  <div class="agent-page">
    <section class="page-head">
      <div>
        <span class="eyebrow">AI智能体治理</span>
        <h1>AI智能体与契约治理</h1>
        <p>统一维护本地契约层、Provider适配和教师采纳门槛，让桂教通、Mock、本地模型预留能力后续都能接入同一套业务闭环。</p>
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
        <span>本地契约层</span>
      </div>
      <div class="summary-item">
        <strong>{{ providerModeCount }}</strong>
        <span>Provider适配</span>
      </div>
    </section>

    <section class="governance-strip">
      <div class="governance-item">
        <span>本地契约层</span>
        <strong>业务工作流只认标准 JSON 输入输出</strong>
        <p>桂教通、Mock 或后续本地模型都要转换为同一份场景契约。</p>
      </div>
      <div class="governance-item">
        <span>Provider适配</span>
        <strong>外部能力只做适配，不绑死平台核心</strong>
        <p>当前可用 Mock开发模式，桂教通预留、国内智能体预设和本地模型预留按同一网关扩展。</p>
      </div>
      <div class="governance-item">
        <span>教师采纳门槛</span>
        <strong>AI 结果必须经教师确认后进入业务数据</strong>
        <p>生成内容先形成草案、思考进度和调用记录，不直接发布给学生。</p>
      </div>
    </section>

    <section class="provider-band">
      <div v-for="item in providerStatusCards" :key="item.label" class="provider-status">
        <el-tag :type="item.type" effect="light">{{ item.label }}</el-tag>
        <span>{{ item.description }}</span>
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
              <el-tag :type="providerTagType(row.provider)" effect="light">{{ providerText(row.provider) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="模型/端点" min-width="170">
            <template #default="{ row }">
              <span class="muted">{{ row.config?.model || row.config?.endpoint || '未配置' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="配置自检" min-width="150">
            <template #default="{ row }">
              <div class="readiness-cell">
                <el-tag :type="readinessTagType(readinessMap[row.id]?.status)" effect="light">
                  {{ readinessMap[row.id]?.label || '未自检' }}
                </el-tag>
                <span v-if="readinessMap[row.id]?.status === 'not_configured'" class="readiness-hint">
                  环境变量未设置
                </span>
              </div>
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
          <el-table-column label="操作" width="190" fixed="right">
            <template #default="{ row }">
              <el-tooltip content="查看详情">
                <el-button :icon="View" circle text @click.stop="openDetail(row)" />
              </el-tooltip>
              <el-tooltip content="配置自检">
                <el-button
                  :icon="CircleCheck"
                  circle
                  text
                  :loading="readinessLoadingId === row.id"
                  @click.stop="runReadiness(row)"
                />
              </el-tooltip>
              <el-tooltip content="编辑">
                <el-button :icon="Edit" circle text @click.stop="openEdit(row)" />
              </el-tooltip>
              <el-tooltip content="删除">
                <el-button :icon="Delete" circle text type="danger" @click.stop="removeAgent(row)" />
              </el-tooltip>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="暂无智能体配置">
              <el-button type="primary" :icon="Plus" @click="openCreate">新建智能体</el-button>
            </el-empty>
          </template>
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
          <span>本地契约层</span>
        </div>
        <p class="panel-intro">场景契约定义输入、输出、思考进度和采纳规则，是后续接入桂教通或本地模型的稳定接口。</p>
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
          <div class="contract-meta">
            <span>Provider适配</span>
            <div>
              <el-tag v-for="mode in selectedContract.provider_modes" :key="mode" size="small" effect="light">
                {{ providerText(mode) }}
              </el-tag>
            </div>
          </div>
          <div class="contract-meta">
            <span>教师采纳门槛</span>
            <p>{{ selectedContract.adoption_rule }}</p>
          </div>
          <div class="step-list">
            <div v-for="step in selectedContract.thinking_steps" :key="step.code">
              <span>{{ step.percent }}%</span>
              <div>
                <strong>{{ step.title }}</strong>
                <p>{{ step.description }}</p>
              </div>
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
        <div class="detail-section">
          <h3>Provider配置</h3>
          <p class="muted">这里保存的是适配信息和非敏感参数；密钥、Token 等敏感值应放在后端环境变量或 Provider 服务端配置中。</p>
        </div>
        <div class="readiness-panel">
          <div class="readiness-head">
            <div>
              <h3>配置自检</h3>
              <p>{{ currentReadiness?.summary || '运行自检后可查看接口端点、模型标识、密钥来源等本地配置状态。' }}</p>
            </div>
            <el-button
              size="small"
              :icon="CircleCheck"
              :loading="readinessLoadingId === selectedAgent.id"
              @click="runReadiness(selectedAgent)"
            >
              配置自检
            </el-button>
          </div>
          <el-tag :type="readinessTagType(currentReadiness?.status)" effect="light">
            {{ currentReadiness?.label || '未自检' }}
          </el-tag>
          <div class="readiness-legend">
            <el-tag type="success" size="small" effect="light">配置可运行</el-tag>
            <el-tag type="danger" size="small" effect="light">缺少配置</el-tag>
            <el-tag type="warning" size="small" effect="light">需要人工回填</el-tag>
          </div>
          <div v-if="currentReadiness" class="readiness-checks">
            <div v-for="check in currentReadiness.checks" :key="check.key" class="readiness-check">
              <span>{{ check.label }}</span>
              <el-tag size="small" :type="checkTagType(check.status)" effect="plain">{{ checkStatusText(check.status) }}</el-tag>
              <p>{{ check.message }}</p>
            </div>
          </div>
          <div v-if="currentReadiness?.actions.length" class="readiness-actions">
            <strong>建议动作</strong>
            <p v-for="action in currentReadiness.actions" :key="`${action.field}-${action.label}`">
              {{ action.label }}
            </p>
          </div>
          <p v-if="!currentReadiness" class="muted">缺少配置时请优先补齐接口端点、模型标识、密钥来源；环境变量未设置会阻断真实 Provider 调用。</p>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="模型">{{ selectedAgent.config?.model || '未配置' }}</el-descriptions-item>
          <el-descriptions-item label="端点">{{ selectedAgent.config?.endpoint || '未配置' }}</el-descriptions-item>
          <el-descriptions-item label="认证方式">{{ selectedAgent.config?.auth_type || '未配置' }}</el-descriptions-item>
          <el-descriptions-item label="超时/重试">
            {{ selectedAgent.config?.timeout_seconds || 30 }} 秒 / {{ selectedAgent.config?.max_retries || 1 }} 次
          </el-descriptions-item>
        </el-descriptions>
        <div class="detail-section" v-if="activeContract">
          <h3>思考进度</h3>
          <div class="step-list compact">
            <div v-for="step in activeContract.thinking_steps" :key="step.code">
              <span>{{ step.percent }}%</span>
              <div>
                <strong>{{ step.title }}</strong>
                <p>{{ step.description }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="detail-section" v-if="activeContract">
          <h3>采纳规则</h3>
          <p class="muted">{{ activeContract.adoption_rule }}</p>
        </div>
        <div class="json-block">
          <strong>Provider扩展配置</strong>
          <pre>{{ prettyJson(selectedAgent.config?.extra || {}) }}</pre>
        </div>
        <div class="detail-section">
          <h3>调用契约</h3>
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
            <div class="form-help">Provider 只负责适配外部能力，输出仍需转换成本地契约结构。</div>
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
        <el-form-item label="密钥环境变量名">
          <el-input v-model="form.config.api_key_env" placeholder="例如 OPENAI_COMPATIBLE_API_KEY，不填写真实密钥" />
          <div class="form-help">国内智能体和本地网关建议只保存环境变量名；真实 API Key 放在后端 .env 或部署平台密钥中。</div>
        </el-form-item>
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
          title="桂教通和国内智能体 Provider 只保存 endpoint、model、api_key_env、extra 等非敏感配置；真实密钥不要写入浏览器可见 JSON。"
        />
        <el-form-item label="Provider扩展配置 JSON">
          <el-input v-model="extraText" type="textarea" :rows="4" />
          <div class="form-help">可放 agent_id、租户标识、模型别名等非密钥字段；正式对接桂教通时由后端 Provider 读取环境变量完成认证。</div>
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
import { CircleCheck, Delete, Document, Edit, Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { createAgent, deleteAgent, getAgentReadiness, getAgents, getAIContracts, updateAgent } from '@/api/ai'
import type { AgentConfig, AIAgent, AIAgentMutation, AIAgentReadiness, AIContract } from '@/api/ai'

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
  { label: 'OpenAI兼容本地网关', value: 'openai_compatible_local' },
  { label: '通义千问', value: 'qwen_agent' },
  { label: 'DeepSeek', value: 'deepseek_agent' },
  { label: '智谱GLM', value: 'zhipu_agent' },
  { label: '豆包', value: 'doubao_agent' },
  { label: '百度千帆', value: 'qianfan_agent' },
  { label: '讯飞星火', value: 'spark_agent' },
  { label: 'Kimi', value: 'kimi_agent' },
  { label: '桂教通链接', value: 'gjt_link' },
  { label: '人工导入', value: 'manual_import' }
]

const providerStatusCards = [
  { label: 'Mock开发模式', description: '用于开发、演示和无外网部署的稳定兜底。', type: 'success' },
  { label: '桂教通预留', description: '后续接入比赛智能体 API，仍输出本地标准契约。', type: 'warning' },
  { label: '国内智能体预设', description: '通义千问、DeepSeek、智谱GLM、豆包、百度千帆、讯飞星火、Kimi 统一走本地契约。', type: 'warning' },
  { label: '本地模型预留', description: '可接 OpenAI兼容本地网关或校内部署模型。', type: 'info' },
  { label: '人工导入', description: '支持线下智能体结果手工入库并走审核采纳。', type: 'info' }
] as const

const domesticProviderValues = new Set<Provider>([
  'openai_compatible_local',
  'qwen_agent',
  'deepseek_agent',
  'zhipu_agent',
  'doubao_agent',
  'qianfan_agent',
  'spark_agent',
  'kimi_agent'
])

const loading = ref(false)
const saving = ref(false)
const switchingId = ref('')
const readinessLoadingId = ref('')
const agents = ref<AIAgent[]>([])
const contracts = ref<AIContract[]>([])
const readinessMap = reactive<Record<string, AIAgentReadiness>>({})
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
const providerModeCount = computed(() => providerStatusCards.length)
const selectedContract = computed(() => contracts.value.find(item => item.scenario === selectedContractScenario.value))
const activeContract = computed(() => selectedAgent.value ? contracts.value.find(item => item.scenario === selectedAgent.value?.scenario) : null)
const currentReadiness = computed(() => selectedAgent.value ? readinessMap[selectedAgent.value.id] : null)

function makeDefaultConfig(provider: Provider): AgentConfig {
  return {
    provider,
    model: provider === 'mock' ? 'mock' : defaultModel(provider),
    endpoint: null,
    auth_type: null,
    api_key_env: domesticProviderValues.has(provider) ? 'OPENAI_COMPATIBLE_API_KEY' : null,
    timeout_seconds: 30,
    max_retries: 1,
    extra: {}
  }
}

function defaultModel(provider: Provider) {
  const modelMap: Partial<Record<Provider, string>> = {
    openai_compatible_local: 'local-json-agent',
    qwen_agent: 'qwen-plus',
    deepseek_agent: 'deepseek-chat',
    zhipu_agent: 'glm-4',
    doubao_agent: 'doubao-pro',
    qianfan_agent: 'ernie-4.0',
    spark_agent: 'spark-max',
    kimi_agent: 'moonshot-v1'
  }
  return modelMap[provider] || null
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
  if (domesticProviderValues.has(form.provider)) {
    if (!form.config.model) form.config.model = defaultModel(form.provider)
    if (!form.config.api_key_env) form.config.api_key_env = 'OPENAI_COMPATIBLE_API_KEY'
    if (!form.config.auth_type) form.config.auth_type = 'bearer'
  }
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

async function runReadiness(agent: AIAgent) {
  readinessLoadingId.value = agent.id
  try {
    const res = await getAgentReadiness(agent.id)
    readinessMap[agent.id] = res.data
    ElMessage.success(`配置自检：${res.data.label}`)
  } finally {
    readinessLoadingId.value = ''
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

function providerTagType(value: string) {
  if (value === 'mock') return 'success'
  if (value === 'gjt_api' || value === 'gjt_link') return 'warning'
  if (domesticProviderValues.has(value as Provider)) return 'warning'
  return 'info'
}

function readinessTagType(status?: AIAgentReadiness['status']) {
  if (status === 'ready') return 'success'
  if (status === 'manual_required') return 'warning'
  if (status === 'not_configured' || status === 'unsupported') return 'danger'
  return 'info'
}

function checkTagType(status: AIAgentReadiness['checks'][number]['status']) {
  if (status === 'ok') return 'success'
  if (status === 'warning') return 'warning'
  return 'danger'
}

function checkStatusText(status: AIAgentReadiness['checks'][number]['status']) {
  if (status === 'ok') return '正常'
  if (status === 'warning') return '提醒'
  return '阻断'
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
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

.governance-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.governance-item,
.provider-status {
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #fff;
}

.governance-item {
  display: grid;
  gap: 8px;
  padding: 16px;
}

.governance-item span {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
}

.governance-item strong {
  color: #1f3356;
  font-size: 15px;
}

.governance-item p,
.panel-intro,
.contract-meta p,
.step-list p,
.form-help {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}

.provider-band {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.provider-status {
  display: grid;
  gap: 8px;
  padding: 12px;
}

.provider-status span:last-child {
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
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

.readiness-cell {
  display: grid;
  gap: 4px;
  justify-items: start;
}

.readiness-hint {
  color: #dc2626;
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

.contract-meta {
  display: grid;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #edf2f7;
}

.contract-meta > span {
  color: #1f3356;
  font-weight: 700;
}

.contract-meta > div {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.step-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.step-list > div {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 8px;
  color: #334155;
}

.step-list span {
  color: #2563eb;
  font-weight: 700;
}

.step-list strong {
  color: #1f3356;
}

.step-list.compact {
  margin-top: 0;
}

.detail-head {
  align-items: flex-start;
  margin-bottom: 16px;
}

.detail-section {
  display: grid;
  gap: 6px;
  margin-top: 16px;
}

.detail-section h3 {
  margin: 0;
  color: #1f3356;
  font-size: 15px;
}

.readiness-panel {
  display: grid;
  gap: 12px;
  margin: 16px 0;
  padding: 14px;
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #f8fafc;
}

.readiness-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.readiness-head h3 {
  margin: 0 0 4px;
  color: #1f3356;
  font-size: 15px;
}

.readiness-head p,
.readiness-actions p,
.readiness-check p {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}

.readiness-checks {
  display: grid;
  gap: 8px;
}

.readiness-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.readiness-check {
  display: grid;
  grid-template-columns: minmax(84px, auto) auto;
  gap: 4px 8px;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #e5edf7;
}

.readiness-check span {
  color: #1f3356;
  font-weight: 700;
}

.readiness-check p {
  grid-column: 1 / -1;
}

.readiness-actions {
  display: grid;
  gap: 4px;
}

.readiness-actions strong {
  color: #1f3356;
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

.form-help {
  margin-top: 6px;
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
  .summary-row,
  .governance-strip,
  .provider-band {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page-head,
  .head-actions,
  .toolbar,
  .two-cols,
  .three-cols,
  .provider-status {
    display: grid;
    width: 100%;
  }

  .filter {
    width: 100%;
  }
}
</style>
