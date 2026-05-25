<template>
  <div class="teacher-page">
    <div class="metrics">
      <el-card v-for="item in metrics" :key="item.label" shadow="never" class="metric-card">
        <div class="label">{{ item.label }}</div>
        <div class="value">{{ item.value }}</div>
        <div class="delta">{{ item.delta }}</div>
      </el-card>
    </div>

    <div class="charts">
      <el-card class="section-card" shadow="never">
        <div class="card-head">
          <div>
            <h2>班级活跃趋势</h2>
            <p>本月课堂活跃度与作业完成情况</p>
          </div>
          <el-tag type="success" effect="light">持续上升</el-tag>
        </div>
        <v-chart class="chart" :option="lineOption" autoresize />
      </el-card>

      <el-card class="section-card" shadow="never">
        <div class="card-head">
          <div>
            <h2>学科分布</h2>
            <p>跨学科项目覆盖结构</p>
          </div>
          <el-tag type="warning" effect="light">多学科协同</el-tag>
        </div>
        <v-chart class="chart" :option="pieOption" autoresize />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const metrics = [
  { label: '活跃班级', value: '6', delta: '较上周 ↑1' },
  { label: '课堂参与率', value: '92.3%', delta: '较上周 ↑5.7%' },
  { label: '作业完成率', value: '89.6%', delta: '较上周 ↑6.2%' },
  { label: '待评价提交', value: '45', delta: '今日新增 8' }
]

const lineOption = computed(() => ({
  grid: { left: 36, right: 20, top: 18, bottom: 24 },
  tooltip: { trigger: 'axis' },
  legend: { bottom: 0 },
  xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
  yAxis: { type: 'value' },
  series: [
    { name: '课堂活跃', type: 'line', smooth: true, data: [58, 64, 68, 74, 82, 85] },
    { name: '作业完成', type: 'line', smooth: true, data: [54, 60, 66, 72, 79, 84] }
  ]
}))

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '42%'],
      label: { show: false },
      data: [
        { value: 32, name: '地理' },
        { value: 28, name: '生物' },
        { value: 18, name: '语文' },
        { value: 14, name: '信息技术' },
        { value: 8, name: '其他' }
      ]
    }
  ]
}))
</script>

<style scoped>
.teacher-page {
  display: grid;
  gap: 16px;
}

.metrics,
.charts {
  display: grid;
  gap: 12px;
}

.metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-card,
.section-card {
  border-radius: 10px;
}

.label {
  color: #7b8ba6;
}

.value {
  margin-top: 8px;
  color: #173b82;
  font-size: 28px;
  font-weight: 800;
}

.delta {
  margin-top: 6px;
  color: #20a464;
  font-size: 12px;
}

.charts {
  grid-template-columns: 1.2fr 0.8fr;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-head h2 {
  color: #223555;
  font-size: 18px;
}

.card-head p {
  color: #7b8ba6;
  font-size: 12px;
  margin-top: 4px;
}

.chart {
  height: 280px;
}

@media (max-width: 980px) {
  .metrics,
  .charts {
    grid-template-columns: 1fr;
  }
}
</style>
