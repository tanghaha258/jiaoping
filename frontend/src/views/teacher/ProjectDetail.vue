<template>
  <div class="project-detail-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回项目列表</el-button>
    </div>

    <el-card class="info-card" v-loading="infoLoading">
      <template #header>
        <div class="card-header">
          <div>
            <div class="card-title">项目概览</div>
            <div class="card-subtitle">项目承载教学目标，课时任务发布后才会进入学生端。</div>
          </div>
          <div class="header-actions">
            <el-button
              v-if="project.status === 'draft'"
              type="success"
              @click="handleActivate"
            >
              激活项目
            </el-button>
            <el-button
              v-if="project.status === 'active'"
              type="warning"
              @click="handleComplete"
            >
              完成项目
            </el-button>
            <el-button
              v-if="project.status === 'completed'"
              type="info"
              @click="handleArchive"
            >
              归档项目
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目名称" :span="2">
          {{ project.name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="年级">
          {{ project.grade || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusTag
            :status="project.status"
            :type-map="statusTypeMap"
            :text-map="statusTextMap"
          />
        </el-descriptions-item>
        <el-descriptions-item label="驱动问题" :span="2">
          {{ project.driving_question || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="涉及学科">
          <div class="tag-list">
            <el-tag
              v-for="subject in project.subjects"
              :key="subject.id"
              size="small"
              effect="plain"
            >
              {{ subject.name }}
            </el-tag>
            <span v-if="!project.subjects || project.subjects.length === 0" class="muted">-</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="课时数量">
          {{ project.lesson_count || 0 }} 节
        </el-descriptions-item>
        <el-descriptions-item label="参与班级">
          <div class="tag-list">
            <el-tag
              v-for="cls in project.classes"
              :key="cls.id"
              size="small"
              effect="plain"
            >
              {{ cls.name }}
            </el-tag>
            <span v-if="!project.classes || project.classes.length === 0" class="muted">-</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ project.owner_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="教学目标" :span="2">
          <ul v-if="project.objectives && project.objectives.length > 0" class="objectives-list">
            <li v-for="(obj, idx) in project.objectives" :key="idx">{{ obj }}</li>
          </ul>
          <span v-else class="muted">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ project.created_at || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ project.updated_at || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="tasks-card">
      <template #header>
        <div class="card-header">
          <div>
            <div class="card-title">课时任务</div>
            <div class="card-subtitle">草稿任务仅教师可见，发布后学生才可以查看和提交。</div>
          </div>
          <div class="header-actions">
            <el-button
              v-if="project.status === 'active'"
              :icon="MagicStick"
              @click="goToAI"
            >
              AI 继续备课
            </el-button>
            <el-button
              v-if="project.status === 'active'"
              type="primary"
              :icon="Plus"
              @click="openCreateTask"
            >
              添加课时
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="tasks"
        v-loading="tasksLoading"
        border
        stripe
        empty-text="暂无课时任务，请添加课时或使用 AI 继续备课"
      >
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column prop="title" label="课时标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="任务类型" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info" effect="plain">
              {{ taskTypeMap[row.task_type] || row.task_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交方式" width="120" align="center">
          <template #default="{ row }">
            {{ submitTypeMap[row.submit_type] || row.submit_type }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              :type-map="taskStatusTypeMap"
              :text-map="taskStatusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="170" align="center">
          <template #default="{ row }">
            {{ row.due_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="提交数" width="90" align="center">
          <template #default="{ row }">
            {{ row.submission_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openTaskDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              type="primary"
              link
              @click="openEditTask(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              type="success"
              link
              @click="handlePublishTask(row)"
            >
              发布
            </el-button>
            <el-button
              v-if="row.status === 'published'"
              size="small"
              type="warning"
              link
              @click="handleCloseTask(row)"
            >
              关闭
            </el-button>
            <el-button size="small" type="primary" link @click="viewSubmissions(row)">
              查看提交
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="showTaskDialog"
      :title="editingTaskId ? '编辑课时任务' : '添加课时任务'"
      width="620px"
      :close-on-click-modal="false"
      @closed="resetTaskForm"
    >
      <el-form
        ref="taskFormRef"
        :model="taskForm"
        :rules="taskFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="课时标题" prop="title">
          <el-input v-model="taskForm.title" placeholder="请输入课时标题" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="任务说明" prop="description">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入任务说明、活动要求和成果形式"
            maxlength="800"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="taskForm.task_type" placeholder="请选择任务类型" style="width: 100%">
            <el-option
              v-for="option in taskTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="提交方式" prop="submit_type">
          <el-select v-model="taskForm.submit_type" placeholder="请选择提交方式" style="width: 100%">
            <el-option
              v-for="option in submitTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期" prop="due_at">
          <el-date-picker
            v-model="taskForm.due_at"
            type="datetime"
            placeholder="请选择截止日期"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTaskDialog = false">取消</el-button>
        <el-button type="primary" :loading="creatingTask" @click="handleSaveTask">
          {{ editingTaskId ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="taskDetailVisible" title="课时详情" size="540px">
      <template v-if="selectedTask">
        <div class="task-detail-head">
          <div>
            <h2>{{ selectedTask.title }}</h2>
            <p>{{ taskTypeMap[selectedTask.task_type] || selectedTask.task_type }}</p>
          </div>
          <StatusTag
            :status="selectedTask.status"
            :type-map="taskStatusTypeMap"
            :text-map="taskStatusTextMap"
          />
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="任务说明">
            {{ selectedTask.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="提交方式">
            {{ submitTypeMap[selectedTask.submit_type] || selectedTask.submit_type }}
          </el-descriptions-item>
          <el-descriptions-item label="截止日期">
            {{ selectedTask.due_at || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="提交数量">
            {{ selectedTask.submission_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="评价量规">
            {{ selectedTask.rubric_name || '未绑定' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ selectedTask.created_at }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ selectedTask.updated_at }}
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { ArrowLeft, MagicStick, Plus } from '@element-plus/icons-vue'
import { activateProject, archiveProject, completeProject, getProject } from '@/api/projects'
import type { ProjectItem } from '@/api/projects'
import { closeTask, createTask, getTasks, publishTask, updateTask } from '@/api/tasks'
import type { TaskCreate, TaskItem } from '@/api/tasks'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string

const statusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  draft: 'info',
  active: 'success',
  completed: 'warning',
  archived: 'danger'
}

const statusTextMap: Record<string, string> = {
  draft: '草稿',
  active: '进行中',
  completed: '已完成',
  archived: '已归档'
}

const taskStatusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  draft: 'info',
  published: 'success',
  closed: 'danger'
}

const taskStatusTextMap: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  closed: '已关闭'
}

const taskTypeMap: Record<string, string> = {
  individual: '个人任务',
  group: '小组协作',
  classroom: '课堂活动',
  homework: '课后作业'
}

const submitTypeMap: Record<string, string> = {
  text: '文本',
  file: '文件',
  link: '链接',
  mixed: '综合材料'
}

const taskTypeOptions = [
  { label: '个人任务', value: 'individual' },
  { label: '小组协作', value: 'group' },
  { label: '课堂活动', value: 'classroom' },
  { label: '课后作业', value: 'homework' }
]

const submitTypeOptions = [
  { label: '文本', value: 'text' },
  { label: '文件', value: 'file' },
  { label: '链接', value: 'link' },
  { label: '综合材料', value: 'mixed' }
]

const project = ref<ProjectItem>({
  id: '',
  name: '',
  grade: '',
  status: '',
  driving_question: '',
  lesson_count: 0,
  objectives: [],
  owner_name: '',
  owner_id: '',
  subjects: [],
  classes: [],
  created_at: '',
  updated_at: ''
})
const infoLoading = ref(false)

const tasks = ref<TaskItem[]>([])
const tasksLoading = ref(false)

const showTaskDialog = ref(false)
const creatingTask = ref(false)
const taskFormRef = ref<FormInstance>()
const editingTaskId = ref('')
const selectedTask = ref<TaskItem | null>(null)
const taskDetailVisible = ref(false)

const taskForm = reactive<TaskCreate>({
  title: '',
  description: '',
  task_type: '',
  submit_type: 'text',
  due_at: null,
  rubric_id: null
})

const taskFormRules: FormRules = {
  title: [
    { required: true, message: '请输入课时标题', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入任务说明', trigger: 'blur' }
  ],
  task_type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  submit_type: [
    { required: true, message: '请选择提交方式', trigger: 'change' }
  ]
}

function goBack() {
  router.push('/teacher/projects')
}

function goToAI() {
  router.push(`/teacher/projects/${projectId}/ai`)
}

async function loadProject() {
  infoLoading.value = true
  try {
    const res = await getProject(projectId)
    project.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.message || '项目详情加载失败')
  } finally {
    infoLoading.value = false
  }
}

async function loadTasks() {
  tasksLoading.value = true
  try {
    const res = await getTasks(projectId)
    tasks.value = res.data.items || []
  } catch (e: any) {
    tasks.value = []
    ElMessage.error(e?.message || '课时任务加载失败')
  } finally {
    tasksLoading.value = false
  }
}

async function handleActivate() {
  try {
    await activateProject(projectId)
    ElMessage.success('项目已激活')
    loadProject()
  } catch (e: any) {
    ElMessage.error(e?.message || '激活失败')
  }
}

async function handleComplete() {
  try {
    await ElMessageBox.confirm('确定要将该项目标记为已完成吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await completeProject(projectId)
    ElMessage.success('项目已完成')
    loadProject()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || '操作失败')
  }
}

async function handleArchive() {
  try {
    await ElMessageBox.confirm('归档后项目将进入只读状态，确定要归档吗？', '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await archiveProject(projectId)
    ElMessage.success('项目已归档')
    loadProject()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || '操作失败')
  }
}

async function handlePublishTask(row: TaskItem) {
  try {
    await ElMessageBox.confirm('发布后学生端将可见并可以提交，确定发布吗？', '发布课时任务', {
      confirmButtonText: '发布',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await publishTask(row.id)
    ElMessage.success('课时已发布')
    loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || '发布失败')
  }
}

async function handleCloseTask(row: TaskItem) {
  try {
    await ElMessageBox.confirm('关闭后学生不能继续提交，确定关闭吗？', '关闭课时任务', {
      confirmButtonText: '关闭',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await closeTask(row.id)
    ElMessage.success('课时已关闭')
    loadTasks()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || '关闭失败')
  }
}

function viewSubmissions(row: TaskItem) {
  router.push(`/teacher/tasks/${row.id}/submissions`)
}

function resetTaskForm() {
  editingTaskId.value = ''
  taskForm.title = ''
  taskForm.description = ''
  taskForm.task_type = ''
  taskForm.submit_type = 'text'
  taskForm.due_at = null
  taskForm.rubric_id = null
  taskFormRef.value?.clearValidate()
}

function openCreateTask() {
  resetTaskForm()
  showTaskDialog.value = true
}

function openEditTask(row: TaskItem) {
  editingTaskId.value = row.id
  taskForm.title = row.title
  taskForm.description = row.description
  taskForm.task_type = row.task_type
  taskForm.submit_type = row.submit_type
  taskForm.due_at = row.due_at
  taskForm.rubric_id = row.rubric_id
  showTaskDialog.value = true
}

function openTaskDetail(row: TaskItem) {
  selectedTask.value = row
  taskDetailVisible.value = true
}

async function handleSaveTask() {
  if (!taskFormRef.value) return
  const valid = await taskFormRef.value.validate().catch(() => false)
  if (!valid) return

  creatingTask.value = true
  try {
    const payload = {
      ...taskForm,
      title: taskForm.title.trim(),
      description: taskForm.description.trim()
    }
    if (editingTaskId.value) {
      await updateTask(editingTaskId.value, payload)
      ElMessage.success('课时已更新')
    } else {
      await createTask(projectId, payload)
      ElMessage.success('课时添加成功')
    }
    showTaskDialog.value = false
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    creatingTask.value = false
  }
}

onMounted(() => {
  loadProject()
  loadTasks()
})
</script>

<style scoped>
.project-detail-page {
  padding: 0;
}

.page-nav {
  margin-bottom: 16px;
}

.info-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.tasks-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-subtitle {
  margin-top: 4px;
  color: #7a8699;
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.muted {
  color: #909399;
}

.objectives-list {
  margin: 0;
  padding-left: 18px;
}

.objectives-list li {
  line-height: 1.8;
}

.task-detail-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.task-detail-head h2 {
  margin: 0 0 4px;
  font-size: 18px;
  color: #303133;
}

.task-detail-head p {
  margin: 0;
  color: #7a8699;
  font-size: 13px;
}
</style>
