<template>
  <div class="teacher-page">
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="head">
          <div>
            <h2>系统设置</h2>
            <p>维护教师端工作偏好和账号安全</p>
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
            <el-option label="七年级(1)班" value="七年级(1)班" />
            <el-option label="七年级(2)班" value="七年级(2)班" />
            <el-option label="八年级(1)班" value="八年级(1)班" />
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

    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="head">
          <div>
            <h2>账号安全</h2>
            <p>首次试运行前请修改默认密码</p>
          </div>
        </div>
      </template>

      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="140px"
        class="form"
      >
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password maxlength="100" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password maxlength="100" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password maxlength="100" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingPassword" @click="submitPassword">更新密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { changePassword } from '@/api/auth'

const form = reactive({
  theme: '海洋生态保护',
  className: '七年级(1)班',
  notify: true,
  aiTips: true
})

const passwordFormRef = ref<FormInstance>()
const savingPassword = ref(false)
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules: FormRules = {
  currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [{ required: true, min: 6, message: '新密码至少 6 位', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

async function submitPassword() {
  if (!passwordFormRef.value) return
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  savingPassword.value = true
  try {
    await changePassword({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    })
    ElMessage.success('密码已更新')
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (e: any) {
    ElMessage.error(e?.message || '更新密码失败')
  } finally {
    savingPassword.value = false
  }
}
</script>

<style scoped>
.teacher-page {
  display: grid;
  gap: 16px;
}

.section-card {
  border-radius: 8px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.head h2 {
  margin: 0;
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
