<template>
  <div class="teacher-page">
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="head">
          <div>
            <h2>系统设置</h2>
            <p>教师端的个性化工作区与基础偏好</p>
          </div>
          <el-button type="primary">保存设置</el-button>
        </div>
      </template>

      <el-form label-width="140px" class="form">
        <el-form-item label="默认工作主题">
          <el-input v-model="form.theme" />
        </el-form-item>
        <el-form-item label="默认班级">
          <el-select v-model="form.className" style="width: 100%">
            <el-option label="七(1)班" value="七(1)班" />
            <el-option label="七(2)班" value="七(2)班" />
            <el-option label="八(1)班" value="八(1)班" />
          </el-select>
        </el-form-item>
        <el-form-item label="通知提醒">
          <el-switch v-model="form.notify" />
        </el-form-item>
        <el-form-item label="AI建议自动展示">
          <el-switch v-model="form.aiTips" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const form = reactive({
  theme: '海洋生态保护',
  className: '七(1)班',
  notify: true,
  aiTips: true
})
</script>

<style scoped>
.teacher-page {
  display: grid;
  gap: 16px;
}

.section-card {
  border-radius: 10px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.head h2 {
  color: #223555;
  font-size: 18px;
}

.head p {
  color: #7b8ba6;
  font-size: 12px;
  margin-top: 4px;
}

.form {
  max-width: 760px;
}
</style>
