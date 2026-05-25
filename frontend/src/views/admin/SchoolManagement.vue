<template>
  <div class="admin-page">
    <section class="header-band">
      <div>
        <p class="eyebrow">基础数据</p>
        <h1>学校管理</h1>
        <p>维护区域、学校、班级和学科，并支持试运行前批量导入基础数据包。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" :loading="loading" @click="reloadCurrent">刷新</el-button>
        <el-button @click="downloadTemplate">下载模板</el-button>
        <el-button @click="downloadExport">导出数据</el-button>
        <el-button type="primary" @click="openImportDialog">导入数据包</el-button>
      </div>
    </section>

    <el-card shadow="never" class="page-card">
      <el-tabs v-model="activeTab" @tab-change="reloadCurrent">
        <el-tab-pane label="学校" name="schools">
          <div class="toolbar">
            <el-input
              v-model="schoolKeyword"
              clearable
              placeholder="搜索学校名称或代码"
              @keyup.enter="loadSchools"
              @clear="loadSchools"
            />
            <el-button @click="loadSchools">查询</el-button>
            <el-button type="primary" :icon="Plus" @click="openSchool()">新增学校</el-button>
          </div>
          <el-table :data="schools" v-loading="loading" border stripe>
            <el-table-column prop="name" label="学校名称" min-width="190" />
            <el-table-column prop="code" label="代码" width="130" />
            <el-table-column prop="region_name" label="区域" min-width="150" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status === 'active' ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="openSchool(row)">编辑</el-button>
                <el-button type="danger" link @click="removeSchool(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="班级" name="classes">
          <div class="toolbar">
            <el-select v-model="classSchoolId" clearable filterable placeholder="学校" style="width: 220px" @change="loadClasses">
              <el-option v-for="item in schools" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
            <el-input
              v-model="classKeyword"
              clearable
              placeholder="搜索班级或学年"
              @keyup.enter="loadClasses"
              @clear="loadClasses"
            />
            <el-button @click="loadClasses">查询</el-button>
            <el-button type="primary" :icon="Plus" @click="openClass()">新增班级</el-button>
          </div>
          <el-table :data="classes" v-loading="loading" border stripe>
            <el-table-column prop="name" label="班级名称" min-width="150" />
            <el-table-column prop="grade" label="年级" width="120" />
            <el-table-column prop="academic_year" label="学年" width="130" />
            <el-table-column prop="school_name" label="学校" min-width="180" />
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="openClass(row)">编辑</el-button>
                <el-button type="danger" link @click="removeClass(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="学科" name="subjects">
          <div class="toolbar">
            <el-input v-model="subjectKeyword" clearable placeholder="搜索学科" @keyup.enter="loadSubjects" @clear="loadSubjects" />
            <el-button @click="loadSubjects">查询</el-button>
            <el-button type="primary" :icon="Plus" @click="openSubject()">新增学科</el-button>
          </div>
          <el-table :data="subjects" v-loading="loading" border stripe>
            <el-table-column prop="name" label="学科名称" min-width="180" />
            <el-table-column prop="stage" label="学段" width="160" />
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="openSubject(row)">编辑</el-button>
                <el-button type="danger" link @click="removeSubject(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="区域" name="regions">
          <div class="toolbar">
            <el-input
              v-model="regionKeyword"
              clearable
              placeholder="搜索区域名称或代码"
              @keyup.enter="loadRegions"
              @clear="loadRegions"
            />
            <el-button @click="loadRegions">查询</el-button>
            <el-button type="primary" :icon="Plus" @click="openRegion()">新增区域</el-button>
          </div>
          <el-table :data="regions" v-loading="loading" border stripe>
            <el-table-column prop="name" label="区域名称" min-width="180" />
            <el-table-column prop="code" label="代码" width="140" />
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link @click="openRegion(row)">编辑</el-button>
                <el-button type="danger" link @click="removeRegion(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="schoolDialog" :title="schoolForm.id ? '编辑学校' : '新增学校'" width="560px">
      <el-form :model="schoolForm" label-width="86px">
        <el-form-item label="学校名称" required><el-input v-model="schoolForm.name" /></el-form-item>
        <el-form-item label="学校代码" required><el-input v-model="schoolForm.code" /></el-form-item>
        <el-form-item label="区域" required>
          <el-select v-model="schoolForm.region_id" filterable style="width: 100%">
            <el-option v-for="item in regions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="schoolForm.status">
            <el-radio-button label="active">启用</el-radio-button>
            <el-radio-button label="inactive">停用</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="schoolDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSchool">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="classDialog" :title="classForm.id ? '编辑班级' : '新增班级'" width="560px">
      <el-form :model="classForm" label-width="86px">
        <el-form-item label="学校" required>
          <el-select v-model="classForm.school_id" filterable style="width: 100%">
            <el-option v-for="item in schools" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="年级" required><el-input v-model="classForm.grade" /></el-form-item>
        <el-form-item label="班级名称" required><el-input v-model="classForm.name" /></el-form-item>
        <el-form-item label="学年" required><el-input v-model="classForm.academic_year" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveClass">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="subjectDialog" :title="subjectForm.id ? '编辑学科' : '新增学科'" width="480px">
      <el-form :model="subjectForm" label-width="86px">
        <el-form-item label="学科名称" required><el-input v-model="subjectForm.name" /></el-form-item>
        <el-form-item label="学段" required><el-input v-model="subjectForm.stage" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subjectDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSubject">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="regionDialog" :title="regionForm.id ? '编辑区域' : '新增区域'" width="480px">
      <el-form :model="regionForm" label-width="86px">
        <el-form-item label="区域名称" required><el-input v-model="regionForm.name" /></el-form-item>
        <el-form-item label="区域代码" required><el-input v-model="regionForm.code" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="regionDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRegion">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialog" title="导入基础数据包" width="720px" :close-on-click-modal="false">
      <el-alert
        title="导入是增量写入：已有代码或名称的数据会跳过，不会删除现有数据。建议先校验，再确认导入。"
        type="info"
        show-icon
        :closable="false"
      />
      <el-input
        v-model="importText"
        type="textarea"
        :rows="14"
        class="import-textarea"
        placeholder="粘贴 JSON 数据包，或点击“下载模板”后按模板填写"
      />
      <div v-if="importSummary" class="summary">
        <strong>{{ importSummary.dry_run ? '校验结果' : '导入结果' }}</strong>
        <div class="summary-grid">
          <span>区域：新增 {{ importSummary.created.regions }}，跳过 {{ importSummary.skipped.regions }}</span>
          <span>学校：新增 {{ importSummary.created.schools }}，跳过 {{ importSummary.skipped.schools }}</span>
          <span>班级：新增 {{ importSummary.created.classes }}，跳过 {{ importSummary.skipped.classes }}</span>
          <span>学科：新增 {{ importSummary.created.subjects }}，跳过 {{ importSummary.skipped.subjects }}</span>
        </div>
        <el-alert v-if="importSummary.errors.length" :title="importSummary.errors.join('；')" type="error" show-icon :closable="false" />
      </div>
      <template #footer>
        <el-button @click="importDialog = false">取消</el-button>
        <el-button :loading="importing" @click="submitImport(true)">仅校验</el-button>
        <el-button type="primary" :loading="importing" @click="submitImport(false)">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import {
  createClass,
  createRegion,
  createSchool,
  createSubject,
  deleteClass,
  deleteRegion,
  deleteSchool,
  deleteSubject,
  exportOrgDataPackage,
  getClasses,
  getOrgDataTemplate,
  getRegions,
  getSchools,
  getSubjects,
  importOrgDataPackage,
  updateClass,
  updateRegion,
  updateSchool,
  updateSubject
} from '@/api/admin'
import type {
  ClassItem,
  OrgDataImportSummary,
  OrgDataPackage,
  RegionItem,
  SchoolItem,
  SubjectItem
} from '@/api/admin'

const activeTab = ref('schools')
const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
const schools = ref<SchoolItem[]>([])
const classes = ref<ClassItem[]>([])
const subjects = ref<SubjectItem[]>([])
const regions = ref<RegionItem[]>([])

const schoolKeyword = ref('')
const classKeyword = ref('')
const subjectKeyword = ref('')
const regionKeyword = ref('')
const classSchoolId = ref('')

const schoolDialog = ref(false)
const classDialog = ref(false)
const subjectDialog = ref(false)
const regionDialog = ref(false)
const importDialog = ref(false)
const importText = ref('')
const importSummary = ref<OrgDataImportSummary | null>(null)

const schoolForm = reactive({ id: '', region_id: '', name: '', code: '', status: 'active' })
const classForm = reactive({ id: '', school_id: '', grade: '', name: '', academic_year: '2026-2027' })
const subjectForm = reactive({ id: '', name: '', stage: 'junior_high' })
const regionForm = reactive({ id: '', name: '', code: '' })

async function loadRegions() {
  loading.value = true
  try {
    const res = await getRegions({ page: 1, page_size: 100, keyword: regionKeyword.value || undefined })
    regions.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

async function loadSchools() {
  loading.value = true
  try {
    const res = await getSchools({ page: 1, page_size: 100, keyword: schoolKeyword.value || undefined })
    schools.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

async function loadClasses() {
  loading.value = true
  try {
    const res = await getClasses({
      page: 1,
      page_size: 100,
      keyword: classKeyword.value || undefined,
      school_id: classSchoolId.value || undefined
    })
    classes.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

async function loadSubjects() {
  loading.value = true
  try {
    const res = await getSubjects({ page: 1, page_size: 100, keyword: subjectKeyword.value || undefined })
    subjects.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

async function reloadCurrent() {
  if (activeTab.value === 'schools') await Promise.all([loadRegions(), loadSchools()])
  if (activeTab.value === 'classes') await Promise.all([loadSchools(), loadClasses()])
  if (activeTab.value === 'subjects') await loadSubjects()
  if (activeTab.value === 'regions') await loadRegions()
}

function openSchool(row?: SchoolItem) {
  schoolForm.id = row?.id || ''
  schoolForm.region_id = row?.region_id || regions.value[0]?.id || ''
  schoolForm.name = row?.name || ''
  schoolForm.code = row?.code || ''
  schoolForm.status = row?.status || 'active'
  schoolDialog.value = true
}

async function saveSchool() {
  saving.value = true
  try {
    const payload = {
      region_id: schoolForm.region_id,
      name: schoolForm.name,
      code: schoolForm.code,
      status: schoolForm.status
    }
    if (schoolForm.id) await updateSchool(schoolForm.id, payload)
    else await createSchool(payload)
    ElMessage.success('学校已保存')
    schoolDialog.value = false
    await loadSchools()
  } finally {
    saving.value = false
  }
}

function openClass(row?: ClassItem) {
  classForm.id = row?.id || ''
  classForm.school_id = row?.school_id || schools.value[0]?.id || ''
  classForm.grade = row?.grade || ''
  classForm.name = row?.name || ''
  classForm.academic_year = row?.academic_year || '2026-2027'
  classDialog.value = true
}

async function saveClass() {
  saving.value = true
  try {
    const payload = {
      school_id: classForm.school_id,
      grade: classForm.grade,
      name: classForm.name,
      academic_year: classForm.academic_year
    }
    if (classForm.id) await updateClass(classForm.id, payload)
    else await createClass(payload)
    ElMessage.success('班级已保存')
    classDialog.value = false
    await loadClasses()
  } finally {
    saving.value = false
  }
}

function openSubject(row?: SubjectItem) {
  subjectForm.id = row?.id || ''
  subjectForm.name = row?.name || ''
  subjectForm.stage = row?.stage || 'junior_high'
  subjectDialog.value = true
}

async function saveSubject() {
  saving.value = true
  try {
    const payload = { name: subjectForm.name, stage: subjectForm.stage }
    if (subjectForm.id) await updateSubject(subjectForm.id, payload)
    else await createSubject(payload)
    ElMessage.success('学科已保存')
    subjectDialog.value = false
    await loadSubjects()
  } finally {
    saving.value = false
  }
}

function openRegion(row?: RegionItem) {
  regionForm.id = row?.id || ''
  regionForm.name = row?.name || ''
  regionForm.code = row?.code || ''
  regionDialog.value = true
}

async function saveRegion() {
  saving.value = true
  try {
    const payload = { name: regionForm.name, code: regionForm.code }
    if (regionForm.id) await updateRegion(regionForm.id, payload)
    else await createRegion(payload)
    ElMessage.success('区域已保存')
    regionDialog.value = false
    await loadRegions()
  } finally {
    saving.value = false
  }
}

async function confirmRemove(name: string) {
  await ElMessageBox.confirm(`确认删除“${name}”？`, '删除确认', { type: 'warning' })
}

async function removeSchool(row: SchoolItem) {
  await confirmRemove(row.name)
  await deleteSchool(row.id)
  ElMessage.success('学校已删除')
  await loadSchools()
}

async function removeClass(row: ClassItem) {
  await confirmRemove(row.name)
  await deleteClass(row.id)
  ElMessage.success('班级已删除')
  await loadClasses()
}

async function removeSubject(row: SubjectItem) {
  await confirmRemove(row.name)
  await deleteSubject(row.id)
  ElMessage.success('学科已删除')
  await loadSubjects()
}

async function removeRegion(row: RegionItem) {
  await confirmRemove(row.name)
  await deleteRegion(row.id)
  ElMessage.success('区域已删除')
  await loadRegions()
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

async function downloadTemplate() {
  const res = await getOrgDataTemplate()
  downloadJson('org-data-template.json', res.data)
}

async function downloadExport() {
  const res = await exportOrgDataPackage()
  downloadJson(`org-data-export-${new Date().toISOString().slice(0, 10)}.json`, res.data)
}

function openImportDialog() {
  importText.value = ''
  importSummary.value = null
  importDialog.value = true
}

function parseImportPackage(): OrgDataPackage | null {
  try {
    return JSON.parse(importText.value) as OrgDataPackage
  } catch {
    ElMessage.error('JSON 格式不正确')
    return null
  }
}

async function submitImport(dryRun: boolean) {
  const parsed = parseImportPackage()
  if (!parsed) return

  importing.value = true
  try {
    const res = await importOrgDataPackage({ dry_run: dryRun, package: parsed })
    importSummary.value = res.data
    if (!dryRun && res.data.errors.length === 0) {
      ElMessage.success('基础数据已导入')
      await Promise.all([loadRegions(), loadSchools(), loadClasses(), loadSubjects()])
    }
  } finally {
    importing.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadRegions(), loadSchools(), loadClasses(), loadSubjects()])
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
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.toolbar {
  margin-bottom: 12px;
}

.toolbar .el-input {
  width: 240px;
}

.import-textarea {
  margin-top: 14px;
}

.summary {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  color: #475569;
}

@media (max-width: 760px) {
  .header-band {
    flex-direction: column;
    align-items: stretch;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
