<template>
  <div class="forbidden-page">
    <div class="forbidden-content">
      <el-result :icon="resultIcon as any" :title="resultTitle" :sub-title="resultSubtitle">
        <template #extra>
          <el-button type="primary" @click="goHome">返回首页</el-button>
          <el-button @click="goBack">返回上页</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { WarningFilled, Warning } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const is403 = computed(() => route.path === '/403')
const resultIcon = computed(() => (is403.value ? WarningFilled : Warning))
const resultTitle = computed(() => (is403.value ? '403 无权限访问' : '404 页面未找到'))
const resultSubtitle = computed(() =>
  is403.value
    ? '抱歉，您没有权限访问此页面。如需帮助请联系管理员。'
    : '抱歉，您访问的页面不存在或已被移除。'
)

function goHome() {
  router.push('/')
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.forbidden-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.forbidden-content {
  max-width: 500px;
}
</style>
