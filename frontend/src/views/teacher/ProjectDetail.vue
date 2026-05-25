<template>
  <div class="project-detail-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回项目列表</el-button>
    </div>

    <!-- Project Info Card -->
    <el-card class="info-card" v-loading="infoLoading">
      <template #header>
        <div class="card-header">
          <span class="card-title">项目信息</span>
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
          {{ project.name }}
        </el-descriptions-item>
        <el-descriptions-item label="年级">
          {{ project.grade }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusTag
            :status="project.status"
            :type-map="statusTypeMap"
            :text-map="statusTextMap"
          />
        </el-descriptions-item>
        <el-descriptions-item label="驱动性问题" :span="2">
          {{ project.driving_question }}
        </el-descriptions-item>
        <el-descriptions-item label="涉及学科">
          <el-tag
            v-for="subject in project.subjects"
            :key="subject.id"
            size="small"
            style="margin-right: 4px; margin-bottom: 2px"
          >
            {{ subject.name }}
          </el-tag>
          <span v-if="!project.subjects || project.subjects.length === 0">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="课时数量">
          {{ project.lesson_count }} 节
        </el-descriptions-item>
        <el-descriptions-item label="参与班级">
          <el-tag
            v-for="cls in project.classes"
            :key="cls.id"
            size="small"
            style="margin-right: 4px"
          >
            {{ cls.name }}
          </el-tag>
          <span v-if="!project.classes || project.classes.length === 0">-</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ project.owner_name }}
        </el-descriptions-item>
        <el-descriptions-item label="教学目标" :span="2">
          <ul v-if="project.objectives && project.objectives.length > 0" class="objectives-list">
            <li v-for="(obj, idx) in project.objectives" :key="idx">{{ obj }}</li>
          </ul>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ project.created_at }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ project.updated_at }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Tasks Section -->
    <el-card class="tasks-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">课时安排</span>
          <div class="header-actions">
            <el-button
              v-if="project.status === 'active'"
              type="primary"
              :icon="MagicStick"
              @click="goToAI"
            >
              AI 备课
            </el-button>
            <el-button
              v-if="project.status === 'active'"
              type="success"
              :icon="Plus"
              @click="openCreateTask"
            >
              添加课时
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="tasks" v-loading="tasksLoading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="title" label="课时标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="任务类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ taskTypeMap[row.task_type] || row.task_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交方式" width="110" align="center">
          <template #default="{ row }">
            {{ submitTypeMap[row.submit_type] || row.submit_type }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              :type-map="taskStatusTypeMap"
              :text-map="taskStatusTextMap"
            />
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="130" align="center">
          <template #default="{ row }">
            {{ row.due_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="openTaskDetail(row)"
            >
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
            <el-button
              size="small"
              type="primary"
              link
              @click="viewSubmissions(row)"
            >
              查看提交
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="tasks.length === 0 && !tasksLoading" class="empty-hint">
        暂无课时安排，请添加课时或使用 AI 备课功能
      </div>
    </el-card>

    <!-- Add Task Dialog -->
    <el-dialog
      v-model="showTaskDialog"
      :title="editingTaskId ? '编辑课时任务' : '添加课时任务'"
      width="560px"
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
        <el-form-item label="任务描述" prop="description">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="taskForm.task_type" placeholder="请选择任务类型" style="width: 100%">
            <el-option label="阅读与探究" value="reading" />
            <el-option label="实验与实践" value="experiment" />
            <el-option label="讨论与合作" value="discussion" />
            <el-option label="创作与展示" value="creation" />
            <el-option label="反思与总结" value="reflection" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交方式" prop="submit_type">
          <el-select v-model="taskForm.submit_type" placeholder="请选择提交方式" style="width: 100%">
            <el-option label="文本" value="text" />
            <el-option label="文件上传" value="file" />
            <el-option label="链接" value="link" />
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

    <el-drawer v-model="taskDetailVisible" title="课时详情" size="520px">
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
          <el-descriptions-item label="任务说明">{{ selectedTask.description }}</el-descriptions-item>
          <el-descriptions-item label="提交方式">{{ submitTypeMap[selectedTask.submit_type] || selectedTask.submit_type }}</el-descriptions-item>
          <el-descriptions-item label="截止日期">{{ selectedTask.due_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="提交数量">{{ selectedTask.submission_count }}</el-descriptions-item>
          <el-descriptions-item label="评价量规">{{ selectedTask.rubric_name || '未绑定' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ selectedTask.created_at }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { ArrowLeft, Plus, MagicStick } from '@element-plus/icons-vue'
import { getProject, activateProject, completeProject, archiveProject } from '@/api/projects'
import type { ProjectItem } from '@/api/projects'
import { getTasks, createTask, updateTask, publishTask, closeTask } from '@/api/tasks'
import type { TaskItem, TaskCreate } from '@/api/tasks'
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
  draft: '未发布',
  published: '已发布',
  closed: '已关闭'
}

const taskTypeMap: Record<string, string> = {
  reading: '阅读探究',
  experiment: '实验实践',
  discussion: '讨论合作',
  creation: '创作展示',
  reflection: '反思总结'
}

const submitTypeMap: Record<string, string> = {
  text: '文本',
  file: '文件',
  link: '链接'
}

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
  due_at: null
})

const taskFormRules: FormRules = {
  title: [
    { required: true, message: '请输入课时标题', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入任务描述', trigger: 'blur' }
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
    ElMessage.error(e?.message || '项目信息加载失败')
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
    ElMessage.error(e?.message || '课时数据加载失败')
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
    await ElMessageBox.confirm('归档后项目将变为只读，确定要归档吗？', '确认操作', {
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
    await publishTask(row.id)
    ElMessage.success('课时已发布')
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e?.message || '发布失败')
  }
}

async function handleCloseTask(row: TaskItem) {
  try {
    await closeTask(row.id)
    ElMessage.success('课时已关闭')
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e?.message || '关闭失败')
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
  taskFormRef.value?.resetFields()
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
    if (editingTaskId.value) {
      await updateTask(editingTaskId.value, { ...taskForm })
      ElMessage.success('课时已更新')
    } else {
      await createTask(projectId, { ...taskForm })
      ElMessage.success('课时添加成功')
    }
    showTaskDialog.value = false
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e?.message || '添加失败')
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
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.objectives-list {
  margin: 0;
  padding-left: 18px;
}

.objectives-list li {
  line-height: 1.8;
}

.empty-hint {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}
</style>
