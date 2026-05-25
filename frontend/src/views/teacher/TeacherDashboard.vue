<template>
  <div class="teacher-dashboard">
    <section class="hero-band">
      <div class="hero-copy">
        <div class="eyebrow">AI赋能教学全链路 · 教学评一体化闭环</div>
        <h1>跨学科教学评一体化工作台</h1>
        <p>
          围绕备课、课堂、学情、评价和改进五个阶段，统一管理项目、任务、资源和智能体调用。
        </p>

        <div class="flow-strip">
          <div v-for="step in workflow" :key="step.title" class="flow-step" :style="{ '--step-color': step.color }">
            <div class="flow-icon">
              <el-icon :size="22"><component :is="step.icon" /></el-icon>
            </div>
            <strong>{{ step.title }}</strong>
            <span>{{ step.desc }}</span>
          </div>
        </div>
      </div>

      <div class="hero-panel">
        <div class="panel-title-row">
          <h2>快捷入口</h2>
          <span>常用任务直达</span>
        </div>
        <div class="quick-grid">
          <button v-for="item in quickActions" :key="item.label" class="quick-card" type="button" @click="go(item.path)">
            <span class="quick-icon" :style="{ background: item.bg }">
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
            </span>
            <strong>{{ item.label }}</strong>
          </button>
        </div>
      </div>

      <div class="hero-panel todo-panel">
        <div class="panel-title-row">
          <h2>待办事项</h2>
          <el-button text type="primary" :icon="ArrowRight" @click="go('/teacher/projects')">更多</el-button>
        </div>
        <div class="todo-list">
          <div v-for="todo in todos" :key="todo.title" class="todo-item">
            <span class="todo-dot" :style="{ background: todo.color }"></span>
            <div class="todo-main">
              <strong>{{ todo.title }}</strong>
              <span>{{ todo.subtitle }}</span>
            </div>
            <div class="todo-time">{{ todo.time }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <el-card v-for="item in stats" :key="item.label" class="stat-card" shadow="never">
        <div class="stat-label">{{ item.label }}</div>
        <div class="stat-value">{{ item.value }}</div>
        <div class="stat-delta">{{ item.delta }}</div>
      </el-card>
    </section>

    <section class="content-grid">
      <el-card class="section-card chart-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>学情总体趋势</h3>
            <p>近五周的学业表现、课堂参与和作业完成情况</p>
          </div>
          <el-tag effect="light">班级平均</el-tag>
        </div>
        <v-chart class="chart large-chart" :option="trendOption" autoresize />
      </el-card>

      <el-card class="section-card radar-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>能力维度雷达图</h3>
            <p>知识掌握、信息素养、合作表达等六项能力</p>
          </div>
          <el-tag effect="light" type="success">教学改进</el-tag>
        </div>
        <v-chart class="chart small-chart" :option="radarOption" autoresize />
      </el-card>

      <el-card class="section-card donut-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>学科融合结构</h3>
            <p>本周跨学科项目所覆盖的学科占比</p>
          </div>
          <el-tag effect="light" type="warning">78% 平均达成</el-tag>
        </div>
        <div class="donut-wrap">
          <v-chart class="chart donut-chart" :option="donutOption" autoresize />
          <div class="donut-center">
            <strong>78%</strong>
            <span>综合达成</span>
          </div>
        </div>
      </el-card>

      <el-card class="section-card list-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>最近教学活动</h3>
            <p>项目创建、任务发布、批阅和课堂实施的动态记录</p>
          </div>
          <el-button text type="primary" :icon="ArrowRight">更多</el-button>
        </div>
        <el-table :data="activities" size="small" border class="activity-table">
          <el-table-column prop="type" label="类型" width="96" />
          <el-table-column prop="name" label="活动名称" min-width="220" />
          <el-table-column prop="grade" label="年级学科" width="140" />
          <el-table-column prop="date" label="创建时间" width="120" />
          <el-table-column label="进度" width="150">
            <template #default="{ row }">
              <el-progress :percentage="row.progress" :stroke-width="8" :show-text="false" />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </section>

    <section class="bottom-grid">
      <el-card class="section-card assistant-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>AI助手</h3>
            <p>智能备课、任务生成、评价建议一键调用</p>
          </div>
          <el-button text type="primary" :icon="ArrowRight">更多</el-button>
        </div>
        <div class="assistant-greeting">
          <strong>您好，张老师</strong>
          <span>我可以继续帮您完成当前项目的教学设计、任务生成和评价草稿。</span>
        </div>
        <div class="assistant-actions">
          <button v-for="item in assistantActions" :key="item.label" class="assistant-action" type="button">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </button>
        </div>
        <div class="assistant-input">
          <el-input v-model="assistantPrompt" placeholder="输入您想让 AI 处理的内容..." />
          <el-button type="primary" :icon="Promotion">发送</el-button>
        </div>
      </el-card>

      <el-card class="section-card resource-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>资源推荐</h3>
            <p>围绕“海洋生态保护”主题的可复用资源</p>
          </div>
          <el-button text type="primary" :icon="ArrowRight">更多</el-button>
        </div>
        <div class="resource-list">
          <div v-for="item in resources" :key="item.title" class="resource-item">
            <div class="resource-thumb" :style="{ background: item.bg }"></div>
            <div class="resource-copy">
              <strong>{{ item.title }}</strong>
              <span>{{ item.meta }}</span>
            </div>
            <el-tag size="small" effect="light">{{ item.tag }}</el-tag>
          </div>
        </div>
      </el-card>

      <el-card class="section-card region-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>区域数据概览（钦州市）</h3>
            <p>聚合统计，不展示学生敏感个人信息</p>
          </div>
          <el-button text type="primary" :icon="ArrowRight">更多</el-button>
        </div>
        <div class="region-stats">
          <div v-for="item in regionStats" :key="item.label" class="region-stat">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <em>{{ item.delta }}</em>
          </div>
        </div>
        <v-chart class="chart region-chart" :option="regionOption" autoresize />
      </el-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Checked, DataAnalysis, DocumentAdd, Files, MagicStick, Monitor, Promotion, Reading, TrendCharts, UserFilled } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, RadarChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent, PolarComponent, RadarComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, RadarChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, PolarComponent, RadarComponent])

const router = useRouter()
const assistantPrompt = ref('')

const workflow = [
  { title: '备课设计', desc: 'AI生成教学草案', color: '#2965ff', icon: DocumentAdd },
  { title: '课堂实施', desc: '任务与互动同步', color: '#19b48f', icon: Monitor },
  { title: '学情诊断', desc: '数据驱动研判', color: '#7f5af0', icon: DataAnalysis },
  { title: '智能评价', desc: '多元反馈汇总', color: '#ff8f1f', icon: Checked },
  { title: '改进提升', desc: '生成反思建议', color: '#2e7dff', icon: TrendCharts }
]

const quickActions = [
  { label: '新建课件', path: '/teacher/projects', icon: Files, bg: 'linear-gradient(135deg, #2f80ff, #6ea8ff)' },
  { label: 'AI备课助手', path: '/teacher/ai/lesson-plan', icon: MagicStick, bg: 'linear-gradient(135deg, #16b38f, #63d0b7)' },
  { label: '跨学科任务', path: '/teacher/projects', icon: Reading, bg: 'linear-gradient(135deg, #8f5cff, #ba8dff)' },
  { label: '学情分析', path: '/teacher/evaluations', icon: DataAnalysis, bg: 'linear-gradient(135deg, #ff9c2f, #ffbf63)' },
  { label: '智能评价', path: '/teacher/evaluations', icon: Checked, bg: 'linear-gradient(135deg, #1f7cff, #4ea5ff)' },
  { label: '教研空间', path: '/teacher/resources', icon: UserFilled, bg: 'linear-gradient(135deg, #5e6bff, #8d97ff)' }
]

const todos = [
  { title: '七年级地理《海洋生态保护》备课待完善', subtitle: '今天 09:00 截止', time: '待审阅', color: '#ff6a5f' },
  { title: '跨学科项目《湿地与生物多样性》评价待批阅', subtitle: '今天 12:00 截止', time: '进行中', color: '#ff9d2f' },
  { title: '周测作业（共45份）待批改', subtitle: '今天 18:00 截止', time: '高优先级', color: '#7e5cff' },
  { title: '区域教研活动报名', subtitle: '明天 09:00 截止', time: '待确认', color: '#2ca7a4' }
]

const stats = [
  { label: '我的班级数', value: '6', delta: '较上周 ↑1' },
  { label: '学生总数', value: '256', delta: '较上周 ↑12' },
  { label: '本周课堂数', value: '18', delta: '较上周 ↑3' },
  { label: '作业完成率', value: '89.6%', delta: '较上周 ↑6.2%' },
  { label: '学生参与度', value: '92.3%', delta: '较上周 ↑5.7%' }
]

const activities = [
  { type: '备课', name: '七年级地理《海洋生态保护》教学设计', grade: '七年级 地理/生物', date: '2026-05-20', progress: 80 },
  { type: '任务', name: '跨学科项目《湿地与生物多样性》', grade: '七年级 地理/生物/语文', date: '2026-05-19', progress: 60 },
  { type: '评价', name: '周测：海洋知识综合测评', grade: '七年级 地理', date: '2026-05-18', progress: 100 },
  { type: '课堂', name: '海洋污染调查与治理课堂活动', grade: '七年级 地理/信息技术', date: '2026-05-17', progress: 70 }
]

const assistantActions = [
  { label: '生成教案设计', icon: DocumentAdd },
  { label: '跨学科任务设计', icon: Reading },
  { label: '学情分析报告', icon: DataAnalysis },
  { label: '智能出题组卷', icon: Files },
  { label: '课堂活动建议', icon: Monitor },
  { label: '评价规则生成', icon: Checked }
]

const resources = [
  { title: '海洋生态系统保护（跨学科案例）', meta: '七年级 地理/生物 · 1.2k', tag: '案例', bg: 'linear-gradient(135deg, #3a87ff, #77b2ff)' },
  { title: '湿地与生物多样性PBL任务', meta: '七年级 地理/生物/语文 · 856', tag: '任务', bg: 'linear-gradient(135deg, #16b38f, #6ad8bc)' },
  { title: '海洋污染与治理 微课程', meta: '七年级 地理 · 2.1k', tag: '微课', bg: 'linear-gradient(135deg, #4d6dff, #9aa7ff)' },
  { title: '海洋生态保护 习题集', meta: '七年级 地理/生物 · 1.5k', tag: '习题', bg: 'linear-gradient(135deg, #ff9e2c, #ffcb71)' }
]

const regionStats = [
  { label: '学校接入数', value: '128 所', delta: '较上月 ↑8' },
  { label: '教师使用数', value: '3,256 人', delta: '较上月 ↑256' },
  { label: '学生使用数', value: '58,742 人', delta: '较上月 ↑4,256' },
  { label: '资源总量', value: '126,845 个', delta: '较上月 ↑12,568' }
]

const trendOption = computed(() => ({
  grid: { left: 36, right: 20, top: 28, bottom: 28 },
  tooltip: { trigger: 'axis' },
  legend: { top: 0, data: ['优秀率', '良好率', '合格率'] },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['第12周', '第13周', '第14周', '第15周', '第16周']
  },
  yAxis: { type: 'value', max: 100 },
  series: [
    { name: '优秀率', type: 'line', smooth: true, data: [74, 78, 79, 71, 77], lineStyle: { width: 3 }, symbolSize: 8 },
    { name: '良好率', type: 'line', smooth: true, data: [58, 60, 63, 52, 61], lineStyle: { width: 3 }, symbolSize: 8 },
    { name: '合格率', type: 'line', smooth: true, data: [40, 38, 45, 33, 41], lineStyle: { width: 3 }, symbolSize: 8 }
  ]
}))

const donutOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, left: 'center' },
  series: [
    {
      name: '学科融合',
      type: 'pie',
      radius: ['52%', '75%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: false,
      label: { show: false },
      data: [
        { value: 82, name: '语文' },
        { value: 75, name: '数学' },
        { value: 79, name: '英语' },
        { value: 73, name: '地理' },
        { value: 81, name: '生物' },
        { value: 76, name: '其他学科' }
      ]
    }
  ]
}))

const radarOption = computed(() => ({
  tooltip: {},
  radar: {
    center: ['50%', '48%'],
    radius: '64%',
    indicator: [
      { name: '知识掌握', max: 100 },
      { name: '应用能力', max: 100 },
      { name: '探究能力', max: 100 },
      { name: '合作能力', max: 100 },
      { name: '创新能力', max: 100 },
      { name: '信息素养', max: 100 }
    ]
  },
  series: [
    {
      type: 'radar',
      data: [
        {
          value: [82, 76, 88, 79, 71, 84],
          name: '班级平均'
        },
        {
          value: [78, 69, 81, 73, 66, 77],
          name: '区域平均'
        }
      ]
    }
  ]
}))

const regionOption = computed(() => ({
  grid: { left: 36, right: 20, top: 26, bottom: 24 },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0, data: ['教师活跃数', '学生活跃数'] },
  xAxis: { type: 'category', boundaryGap: false, data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
  yAxis: { type: 'value' },
  series: [
    { name: '教师活跃数', type: 'line', smooth: true, data: [2800, 3100, 3400, 3800, 4200, 4300], symbolSize: 7 },
    { name: '学生活跃数', type: 'line', smooth: true, data: [2100, 2500, 2900, 3400, 4100, 4090], symbolSize: 7 }
  ]
}))

function go(path: string) {
  router.push(path)
}
</script>

<style scoped>
.teacher-dashboard {
  display: grid;
  gap: 16px;
}

.hero-band,
.content-grid,
.bottom-grid {
  display: grid;
  gap: 16px;
}

.hero-band {
  grid-template-columns: minmax(0, 1.7fr) minmax(300px, 1fr) minmax(300px, 0.95fr);
}

.hero-copy,
.hero-panel,
.section-card {
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 10px 30px rgba(40, 78, 130, 0.06);
}

.hero-copy {
  padding: 22px 22px 18px;
}

.eyebrow {
  color: #1a4fa3;
  font-size: 14px;
  font-weight: 700;
}

.hero-copy h1 {
  margin-top: 10px;
  color: #173b82;
  font-size: 26px;
  line-height: 1.2;
}

.hero-copy p {
  max-width: 760px;
  margin-top: 10px;
  color: #5a6d8f;
  line-height: 1.65;
}

.flow-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.flow-step {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 14px 10px 12px;
  border: 1px solid #e6eefb;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(245, 249, 255, 0.9), #fff);
  text-align: center;
}

.flow-icon {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border-radius: 16px;
  color: var(--step-color);
  background: color-mix(in srgb, var(--step-color) 12%, white);
}

.flow-step strong {
  color: #243655;
  font-size: 15px;
}

.flow-step span {
  color: #7183a7;
  font-size: 12px;
}

.hero-panel {
  padding: 18px;
}

.panel-title-row,
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-title-row h2,
.card-header h3 {
  color: #223555;
  font-size: 17px;
}

.panel-title-row span,
.card-header p {
  color: #7b8ba6;
  font-size: 12px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.quick-card {
  display: grid;
  justify-items: center;
  gap: 8px;
  min-height: 92px;
  padding: 12px 8px;
  border: 1px solid #e7eef9;
  border-radius: 10px;
  background: #fbfdff;
  cursor: pointer;
}

.quick-card strong {
  color: #304060;
  font-size: 13px;
}

.quick-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: #fff;
}

.todo-panel .todo-list {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.todo-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #edf2fa;
}

.todo-item:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.todo-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.todo-main {
  display: grid;
  gap: 4px;
}

.todo-main strong {
  color: #243655;
  font-size: 14px;
}

.todo-main span,
.todo-time {
  color: #7c8ba4;
  font-size: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  border: 1px solid #e7eef7;
  border-radius: 10px;
}

.stat-label {
  color: #7183a7;
  font-size: 13px;
}

.stat-value {
  margin-top: 8px;
  color: #173b82;
  font-size: 32px;
  font-weight: 800;
}

.stat-delta {
  margin-top: 8px;
  color: #20a464;
  font-size: 12px;
}

.content-grid {
  grid-template-columns: 1.4fr 0.9fr 0.9fr;
}

.chart-card {
  min-height: 360px;
  padding: 18px;
}

.radar-card,
.donut-card {
  min-height: 360px;
  padding: 18px;
}

.list-card {
  grid-column: 1 / span 2;
  padding: 18px;
}

.activity-table {
  margin-top: 14px;
}

.chart {
  width: 100%;
}

.large-chart {
  height: 280px;
}

.small-chart,
.region-chart {
  height: 270px;
}

.donut-wrap {
  position: relative;
  height: 290px;
}

.donut-chart {
  height: 290px;
}

.donut-center {
  position: absolute;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -54%);
  display: grid;
  justify-items: center;
  gap: 4px;
}

.donut-center strong {
  color: #173b82;
  font-size: 28px;
  font-weight: 800;
}

.donut-center span {
  color: #7b8ba6;
  font-size: 12px;
}

.bottom-grid {
  grid-template-columns: 1fr 1.05fr 1.1fr;
}

.assistant-card,
.resource-card,
.region-card {
  padding: 18px;
}

.assistant-greeting {
  display: grid;
  gap: 6px;
  margin-top: 14px;
  padding: 14px;
  border-radius: 10px;
  background: #f3f8ff;
}

.assistant-greeting strong {
  color: #173b82;
}

.assistant-greeting span {
  color: #6d7f9f;
  line-height: 1.5;
}

.assistant-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.assistant-action {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid #e4ecf8;
  border-radius: 8px;
  color: #274060;
  background: #fff;
}

.assistant-input {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  margin-top: 14px;
}

.resource-list {
  display: grid;
  gap: 12px;
  margin-top: 14px;
}

.resource-item {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 8px;
  border: 1px solid #edf3fb;
  border-radius: 10px;
}

.resource-thumb {
  width: 76px;
  height: 54px;
  border-radius: 8px;
}

.resource-copy {
  display: grid;
  gap: 4px;
}

.resource-copy strong {
  color: #243655;
  font-size: 14px;
}

.resource-copy span {
  color: #7c8ba4;
  font-size: 12px;
}

.region-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.region-stat {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid #edf3fb;
  border-radius: 10px;
  background: #fbfdff;
}

.region-stat span {
  color: #7c8ba4;
  font-size: 12px;
}

.region-stat strong {
  color: #173b82;
  font-size: 20px;
  font-weight: 800;
}

.region-stat em {
  color: #20a464;
  font-style: normal;
  font-size: 12px;
}

@media (max-width: 1400px) {
  .hero-band {
    grid-template-columns: 1fr 1fr;
  }

  .todo-panel {
    grid-column: 1 / -1;
  }

  .content-grid,
  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .list-card {
    grid-column: auto;
  }
}

@media (max-width: 1100px) {
  .flow-strip,
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .assistant-actions {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .hero-band,
  .flow-strip,
  .stats-grid,
  .region-stats,
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .assistant-input,
  .resource-item {
    grid-template-columns: 1fr;
  }
}
</style>
