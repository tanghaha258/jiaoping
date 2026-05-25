<template>
  <div class="admin-dashboard">
    <section class="header-band">
      <div>
        <p class="eyebrow">运营概览</p>
        <h1>管理驾驶舱</h1>
        <p>面向部署试运行的学校、用户、项目、资源和 AI 调用概览。</p>
      </div>
      <el-button type="primary" :icon="Refresh" @click="loadData">刷新数据</el-button>
    </section>

    <section class="metric-grid">
      <el-card v-for="item in metrics" :key="item.label" shadow="never" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.hint }}</em>
      </el-card>
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
            <el-tag effect="light" type="warning">Mock 先行</el-tag>
          </div>
        </template>
        <div class="ai-note">
          <strong>{{ aiUsage.total_calls }}</strong>
          <span>当前 AI 调用次数。桂教通智能体后续接入时，仍沿用本平台的调用记录和契约。</span>
        </div>
        <el-table :data="aiProviderRows" size="small" border>
          <el-table-column prop="provider" label="Provider" />
          <el-table-column prop="count" label="调用数" width="120" align="center" />
        </el-table>
      </el-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getAIUsage, getDashboardOverview, getProjectTrends } from '@/api/dashboard'
import type { AIUsage, DashboardOverview, ProjectTrends } from '@/api/dashboard'

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

const metrics = computed(() => [
  { label: '学校数量', value: overview.value.schools, hint: '已接入机构' },
  { label: '教师数量', value: overview.value.teachers, hint: '可开展项目' },
  { label: '学生数量', value: overview.value.students, hint: '可参与任务' },
  { label: '项目数量', value: overview.value.projects, hint: '跨学科项目' },
  { label: '任务数量', value: overview.value.tasks, hint: '已建学习任务' },
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

async function loadData() {
  try {
    const [overviewRes, trendsRes, aiRes] = await Promise.all([
      getDashboardOverview(),
      getProjectTrends(),
      getAIUsage()
    ])
    overview.value = overviewRes.data
    trends.value = trendsRes.data
    aiUsage.value = aiRes.data
  } catch (e: any) {
    ElMessage.error(e?.message || '加载驾驶舱数据失败')
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
.section-card {
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

.header-band p {
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
  .content-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .header-band,
  .metric-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .header-band {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
