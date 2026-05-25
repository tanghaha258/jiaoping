<template>
  <div class="admin-page">
    <section class="header-band">
      <div>
        <p class="eyebrow">账号运营</p>
        <h1>用户管理</h1>
        <p>维护教师、学生、学校管理员和教研员账号，保障真实部署后的人员可用。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" :loading="loading" @click="loadUsers">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增用户</el-button>
      </div>
    </section>

    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="card-header">
          <strong>账号列表</strong>
          <div class="filters">
            <el-input
              v-model="filters.keyword"
              clearable
              placeholder="搜索用户名或姓名"
              style="width: 220px"
              @keyup.enter="reloadFirstPage"
              @clear="reloadFirstPage"
            />
            <el-select v-model="filters.role" clearable placeholder="角色" style="width: 150px" @change="reloadFirstPage">
              <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="filters.status" clearable placeholder="状态" style="width: 130px" @change="reloadFirstPage">
              <el-option label="启用" value="active" />
              <el-option label="停用" value="disabled" />
              <el-option label="锁定" value="locked" />
            </el-select>
            <el-button @click="reloadFirstPage">查询</el-button>
          </div>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" border stripe>
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column prop="name" label="姓名" min-width="140" />
        <el-table-column label="角色" width="130" align="center">
          <template #default="{ row }">
            <el-tag>{{ roleTextMap[row.role] || row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="school_name" label="学校" min-width="190" show-overflow-tooltip />
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTypeMap[row.status] || 'info'">{{ statusTextMap[row.status] || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最近登录" width="180" align="center">
          <template #default="{ row }">{{ formatDate(row.last_login_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="warning" link @click="toggleStatus(row)">
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && users.length === 0" description="暂无用户" />

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          background
          layout="total, sizes, prev, pager, next"
          @current-change="loadUsers"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="用户详情" size="520px">
      <el-descriptions v-if="selectedUser" :column="1" border>
        <el-descriptions-item label="用户名">{{ selectedUser.username }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ selectedUser.name }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ roleTextMap[selectedUser.role] || selectedUser.role }}</el-descriptions-item>
        <el-descriptions-item label="学校">{{ selectedUser.school_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="班级ID">{{ selectedUser.class_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusTextMap[selectedUser.status] || selectedUser.status }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(selectedUser.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="最近登录">{{ formatDate(selectedUser.last_login_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <el-dialog
      v-model="formVisible"
      :title="editingUser ? '编辑用户' : '新增用户'"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editingUser" maxlength="100" />
        </el-form-item>
        <el-form-item v-if="!editingUser" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password maxlength="100" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" maxlength="100" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="学校">
          <el-select v-model="form.school_id" clearable filterable style="width: 100%" @change="loadClasses">
            <el-option v-for="item in schools" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="form.class_id" clearable filterable style="width: 100%">
            <el-option v-for="item in classes" :key="item.id" :label="`${item.grade} ${item.name}`" :value="item.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import {
  createAdminUser,
  getAdminUsers,
  getClasses,
  getSchools,
  updateAdminUser,
  updateAdminUserStatus
} from '@/api/admin'
import type { AdminUserItem, ClassItem, SchoolItem } from '@/api/admin'
import type { UserRole } from '@/types/api'

const roleOptions: { label: string; value: UserRole }[] = [
  { label: '系统管理员', value: 'system_admin' },
  { label: '区域管理员', value: 'region_admin' },
  { label: '学校管理员', value: 'school_admin' },
  { label: '教研员', value: 'researcher' },
  { label: '教师', value: 'teacher' },
  { label: '学生', value: 'student' }
]

const roleTextMap = Object.fromEntries(roleOptions.map((item) => [item.value, item.label]))
const statusTextMap: Record<string, string> = { active: '启用', disabled: '停用', locked: '锁定' }
const statusTypeMap: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
  active: 'success',
  disabled: 'info',
  locked: 'danger'
}

const users = ref<AdminUserItem[]>([])
const schools = ref<SchoolItem[]>([])
const classes = ref<ClassItem[]>([])
const selectedUser = ref<AdminUserItem | null>(null)
const editingUser = ref<AdminUserItem | null>(null)
const loading = ref(false)
const saving = ref(false)
const detailVisible = ref(false)
const formVisible = ref(false)
const formRef = ref<FormInstance>()

const filters = reactive({ keyword: '', role: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const form = reactive<{
  username: string
  password: string
  name: string
  role: UserRole
  school_id: string | null
  class_id: string | null
}>({
  username: '',
  password: '',
  name: '',
  role: 'teacher',
  school_id: null,
  class_id: null
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function loadSchools() {
  const res = await getSchools({ page: 1, page_size: 100 })
  schools.value = res.data.items || []
}

async function loadClasses() {
  form.class_id = null
  if (!form.school_id) {
    classes.value = []
    return
  }
  const res = await getClasses({ page: 1, page_size: 100, school_id: form.school_id })
  classes.value = res.data.items || []
}

async function loadClassesForSchool(schoolId?: string | null) {
  if (!schoolId) {
    classes.value = []
    return
  }
  const res = await getClasses({ page: 1, page_size: 100, school_id: schoolId })
  classes.value = res.data.items || []
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getAdminUsers({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      role: filters.role || undefined,
      status: filters.status || undefined
    })
    users.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (e: any) {
    users.value = []
    pagination.total = 0
    ElMessage.error(e?.message || '加载用户失败')
  } finally {
    loading.value = false
  }
}

function reloadFirstPage() {
  pagination.page = 1
  loadUsers()
}

function handleSizeChange() {
  pagination.page = 1
  loadUsers()
}

function viewDetail(row: AdminUserItem) {
  selectedUser.value = row
  detailVisible.value = true
}

function resetForm() {
  form.username = ''
  form.password = ''
  form.name = ''
  form.role = 'teacher'
  form.school_id = null
  form.class_id = null
  classes.value = []
}

function openCreate() {
  editingUser.value = null
  resetForm()
  formVisible.value = true
}

async function openEdit(row: AdminUserItem) {
  editingUser.value = row
  form.username = row.username
  form.password = ''
  form.name = row.name
  form.role = row.role
  form.school_id = row.school_id
  await loadClassesForSchool(row.school_id)
  form.class_id = row.class_id || null
  formVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingUser.value) {
      await updateAdminUser(editingUser.value.id, {
        name: form.name,
        role: form.role,
        school_id: form.school_id,
        class_id: form.class_id
      })
      ElMessage.success('用户已更新')
    } else {
      await createAdminUser({
        username: form.username,
        password: form.password,
        name: form.name,
        role: form.role,
        school_id: form.school_id,
        class_id: form.class_id
      })
      ElMessage.success('用户已创建')
    }
    formVisible.value = false
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存用户失败')
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: AdminUserItem) {
  const nextStatus = row.status === 'active' ? 'disabled' : 'active'
  try {
    await ElMessageBox.confirm(
      `确认${nextStatus === 'active' ? '启用' : '停用'}用户「${row.name}」？`,
      '账号状态',
      { type: 'warning' }
    )
  } catch {
    return
  }
  await updateAdminUserStatus(row.id, nextStatus)
  ElMessage.success('用户状态已更新')
  await loadUsers()
}

onMounted(async () => {
  await loadSchools()
  await loadUsers()
})
</script>

<style scoped>
.admin-page {
  display: grid;
  gap: 16px;
}

.header-band,
.page-card {
  border-radius: 8px;
}

.header-band {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  background: #fff;
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

.header-actions,
.card-header,
.filters {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header {
  justify-content: space-between;
}

.filters {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 760px) {
  .header-band,
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filters {
    justify-content: flex-start;
  }
}
</style>
