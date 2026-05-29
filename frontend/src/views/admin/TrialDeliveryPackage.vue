<template>
  <div class="trial-delivery-page">
    <section class="header-band">
      <div>
        <p class="eyebrow">试运行交付</p>
        <h1>试点交付包</h1>
        <p>把 readiness、演练记录、演示脚本和测试账号交付材料汇总成现场验收清单。</p>
      </div>
      <div class="header-actions">
        <el-tag :type="packageStatusTag" effect="dark">
          {{ packageData.status === 'ready' ? '可交付' : '需要处理' }}
        </el-tag>
        <el-button :icon="Refresh" :loading="loading" @click="loadPackage">刷新</el-button>
      </div>
    </section>

    <section class="summary-grid">
      <article v-for="item in summaryCards" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.hint }}</em>
      </article>
    </section>

    <section class="delivery-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">现场验收清单</p>
          <h2>现场验收清单</h2>
        </div>
      </div>
      <el-table :data="packageData.acceptance_checklist" border>
        <el-table-column label="阶段" min-width="170">
          <template #default="{ row }">
            <strong>{{ row.title }}</strong>
            <p class="muted">{{ row.owner }}</p>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" effect="light">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="证据" min-width="240">
          <template #default="{ row }">
            <div class="evidence-list">
              <span v-for="item in row.evidence" :key="item">{{ item }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="最新演练" min-width="220">
          <template #default="{ row }">
            <div v-if="row.latest_record" class="record-note">
              <el-tag :type="recordTag(row.latest_record.status)" effect="light">
                {{ recordText(row.latest_record.status) }}
              </el-tag>
              <span>{{ row.latest_record.operator_name || '管理员' }}</span>
              <p>{{ row.latest_record.note || '未填写备注' }}</p>
            </div>
            <span v-else class="muted">尚无演练记录</span>
          </template>
        </el-table-column>
        <el-table-column label="入口" width="140" align="center">
          <template #default="{ row }">
            <el-button text type="primary" :icon="ArrowRight" @click="go(row.route)">
              {{ row.primary_action }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="delivery-grid">
      <article class="delivery-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">演示脚本</p>
            <h2>演示脚本</h2>
          </div>
        </div>
        <ol class="script-list">
          <li v-for="step in packageData.demo_script" :key="step.step">
            <strong>{{ step.step }}. {{ step.title }}</strong>
            <span>{{ step.role }} · {{ step.route }}</span>
            <p>{{ step.expected_evidence }}</p>
          </li>
        </ol>
      </article>

      <article class="delivery-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">测试账号交付</p>
            <h2>测试账号交付</h2>
          </div>
        </div>
        <div class="account-list">
          <div v-for="account in packageData.accounts" :key="account.username" class="account-item">
            <strong>{{ account.username }}</strong>
            <span>{{ account.role }}</span>
            <p>{{ account.purpose }}</p>
            <em>{{ account.password_hint }}</em>
          </div>
        </div>
      </article>
    </section>

    <section class="delivery-grid">
      <article class="delivery-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">打印验收说明</p>
            <h2>打印验收说明</h2>
          </div>
        </div>
        <div class="printable-block">
          <strong>{{ packageData.printable_acceptance.title }}</strong>
          <p>{{ packageData.printable_acceptance.purpose }}</p>
          <span>需确认角色：{{ packageData.printable_acceptance.required_signoffs.join('、') }}</span>
          <ul>
            <li v-for="statement in packageData.printable_acceptance.statements" :key="statement">
              {{ statement }}
            </li>
          </ul>
        </div>
      </article>

      <article class="delivery-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">异常处置流程</p>
            <h2>异常处置流程</h2>
          </div>
        </div>
        <div class="procedure-list">
          <div v-for="procedure in packageData.fallback_procedures" :key="procedure.key" class="procedure-item">
            <strong>{{ procedure.title }}</strong>
            <span>{{ procedure.owner }} · {{ procedure.trigger }}</span>
            <ol>
              <li v-for="step in procedure.steps" :key="step">{{ step }}</li>
            </ol>
            <p>留存证据：{{ procedure.evidence.join('、') }}</p>
          </div>
        </div>
      </article>
    </section>

    <section class="delivery-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">分角色交接卡</p>
          <h2>分角色交接卡</h2>
        </div>
      </div>
      <div class="handoff-grid">
        <article v-for="handoff in packageData.role_handoffs" :key="handoff.role" class="handoff-card">
          <strong>{{ handoff.title }}</strong>
          <span>{{ handoff.route }}</span>
          <p>{{ handoff.handoff_note }}</p>
          <ul>
            <li v-for="item in handoff.checklist" :key="item">{{ item }}</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="delivery-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">交付材料</p>
          <h2>交付材料</h2>
        </div>
        <div class="material-actions">
          <el-button :icon="CopyDocument" @click="copyMarkdown">复制交付材料</el-button>
          <el-button :icon="Download" @click="downloadMarkdown">下载 Markdown</el-button>
          <el-button type="primary" :icon="Download" @click="downloadJson">下载 JSON</el-button>
        </div>
      </div>
      <el-input v-model="packageData.materials.markdown" type="textarea" :rows="12" readonly />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, CopyDocument, Download, Refresh } from '@element-plus/icons-vue'
import { getTrialDeliveryPackage } from '@/api/dashboard'
import type {
  TrialDeliveryPackage,
  TrialReadinessItemStatus,
  TrialRunbookRecordStatus
} from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)
const packageData = ref<TrialDeliveryPackage>({
  status: 'action_required',
  generated_at: '',
  summary: {
    readiness_ok: 0,
    readiness_warning: 0,
    readiness_error: 0,
    runbook_checked: 0,
    runbook_blocked: 0,
    runbook_skipped: 0
  },
  audience_sections: [],
  acceptance_checklist: [],
  demo_script: [],
  accounts: [],
  printable_acceptance: {
    title: '',
    purpose: '',
    required_signoffs: [],
    statements: []
  },
  fallback_procedures: [],
  role_handoffs: [],
  materials: {
    markdown: '',
    json: ''
  }
})

const packageStatusTag = computed(() => packageData.value.status === 'ready' ? 'success' : 'danger')
const summaryCards = computed(() => [
  { label: '正常项', value: packageData.value.summary.readiness_ok, hint: 'readiness ok' },
  { label: '提醒项', value: packageData.value.summary.readiness_warning, hint: 'readiness warning' },
  { label: '阻断项', value: packageData.value.summary.readiness_error, hint: 'readiness error' },
  { label: '演练已检查', value: packageData.value.summary.runbook_checked, hint: 'checked records' },
  { label: '演练阻断', value: packageData.value.summary.runbook_blocked, hint: 'blocked records' },
  { label: '演练跳过', value: packageData.value.summary.runbook_skipped, hint: 'skipped records' }
])

function statusTag(status: TrialReadinessItemStatus) {
  return status === 'ok' ? 'success' : status === 'warning' ? 'warning' : 'danger'
}

function statusText(status: TrialReadinessItemStatus) {
  return status === 'ok' ? '正常' : status === 'warning' ? '提醒' : '阻断'
}

function recordTag(status: TrialRunbookRecordStatus) {
  return status === 'checked' ? 'success' : status === 'blocked' ? 'danger' : 'info'
}

function recordText(status: TrialRunbookRecordStatus) {
  return status === 'checked' ? '已检查' : status === 'blocked' ? '有阻断' : '已跳过'
}

function go(path: string) {
  router.push(path)
}

function downloadText(filename: string, text: string, type: string) {
  const blob = new Blob([text], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function copyMarkdown() {
  try {
    await navigator.clipboard.writeText(packageData.value.materials.markdown)
    ElMessage.success('交付材料已复制')
  } catch {
    ElMessage.error('复制失败，请手动选择文本')
  }
}

function downloadMarkdown() {
  downloadText(
    'trial-delivery-package.md',
    packageData.value.materials.markdown,
    'text/markdown;charset=utf-8'
  )
}

function downloadJson() {
  downloadText(
    'trial-delivery-package.json',
    packageData.value.materials.json,
    'application/json;charset=utf-8'
  )
}

async function loadPackage() {
  loading.value = true
  try {
    const res = await getTrialDeliveryPackage()
    packageData.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.message || '试点交付包加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadPackage)
</script>

<style scoped>
.trial-delivery-page {
  display: grid;
  gap: 18px;
}

.header-band,
.delivery-section,
.summary-card {
  border: 1px solid #dce7f5;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(20, 60, 120, 0.06);
}

.header-band {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px;
}

.header-band h1,
.section-head h2 {
  margin: 0;
  color: #152b4a;
}

.header-band p,
.muted,
.script-list p,
.account-item p,
.account-item em {
  margin: 4px 0 0;
  color: #5f7391;
}

.eyebrow {
  margin: 0 0 6px;
  color: #1f6feb;
  font-size: 12px;
  font-weight: 700;
}

.header-actions,
.material-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  display: grid;
  gap: 6px;
  padding: 16px;
}

.summary-card span,
.summary-card em {
  color: #60728a;
  font-size: 13px;
}

.summary-card strong {
  color: #152b4a;
  font-size: 28px;
}

.delivery-section {
  padding: 18px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.evidence-list,
.account-list,
.procedure-list {
  display: grid;
  gap: 8px;
}

.evidence-list span {
  display: block;
  color: #344966;
}

.record-note {
  display: grid;
  gap: 6px;
}

.record-note p {
  margin: 0;
  color: #344966;
}

.delivery-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 18px;
}

.script-list {
  display: grid;
  gap: 12px;
  margin: 0;
  padding-left: 20px;
}

.script-list li {
  padding-left: 4px;
}

.script-list span,
.account-item span {
  display: block;
  margin-top: 4px;
  color: #1f6feb;
  font-size: 13px;
}

.account-item {
  padding: 12px;
  border: 1px solid #e3ebf6;
  border-radius: 8px;
  background: #f8fbff;
}

.account-item strong {
  color: #152b4a;
}

.printable-block,
.procedure-item,
.handoff-card {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e3ebf6;
  border-radius: 8px;
  background: #f8fbff;
}

.printable-block strong,
.procedure-item strong,
.handoff-card strong {
  color: #152b4a;
}

.printable-block p,
.procedure-item p,
.handoff-card p {
  margin: 0;
  color: #344966;
}

.printable-block span,
.procedure-item span,
.handoff-card span {
  color: #1f6feb;
  font-size: 13px;
}

.printable-block ul,
.procedure-item ol,
.handoff-card ul {
  margin: 0;
  padding-left: 20px;
  color: #344966;
}

.handoff-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 1100px) {
  .summary-grid,
  .delivery-grid,
  .handoff-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 760px) {
  .header-band,
  .section-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-grid,
  .delivery-grid,
  .handoff-grid {
    grid-template-columns: 1fr;
  }
}
</style>
