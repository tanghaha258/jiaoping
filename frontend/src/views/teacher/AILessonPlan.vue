<template>
  <div class="lesson-workflow">
    <section class="page-head">
      <div>
        <span class="eyebrow">AI Agent Workflow</span>
        <h1>AI生成教学方案</h1>
        <p>填写结构化教学意图，生成可审阅、可采纳、可落地的教学评一体化方案。</p>
      </div>
      <div class="head-actions">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <el-button type="primary" :icon="MagicStick" :loading="generating" @click="generateDraft">
          生成草案
        </el-button>
      </div>
    </section>

    <el-card class="steps-card" shadow="never">
      <el-steps :active="step" finish-status="success" align-center>
        <el-step title="结构化输入" description="主题、班级、学科、评价偏好" />
        <el-step title="AI草案审阅" description="项目、任务、量规、资源卡片" />
        <el-step title="采纳落地" description="项目激活，任务保持草稿" />
      </el-steps>
    </el-card>

    <section class="workflow-grid">
      <el-card class="form-card" shadow="never">
        <template #header>
          <div class="card-title">
            <span>高级备课输入</span>
            <el-tag effect="light">教师主控</el-tag>
          </div>
        </template>

        <el-form ref="formRef" :model="form" label-position="top" class="workflow-form">
          <el-form-item label="AI智能体">
            <el-select v-model="form.agent_id" placeholder="默认使用可用的备课智能体" clearable>
              <el-option
                v-for="agent in options.agents"
                :key="agent.id"
                :label="`${agent.name}（${agent.provider || 'mock'}）`"
                :value="agent.id"
              />
            </el-select>
          </el-form-item>

          <div class="two-cols">
            <el-form-item label="教学主题" required>
              <el-input v-model="form.theme" maxlength="80" show-word-limit placeholder="如：海洋生态保护" />
            </el-form-item>
            <el-form-item label="年级" required>
              <el-select v-model="form.grade" filterable allow-create default-first-option>
                <el-option v-for="grade in gradeOptions" :key="grade" :label="grade" :value="grade" />
              </el-select>
            </el-form-item>
          </div>

          <div class="two-cols">
            <el-form-item label="授课班级" required>
              <el-select v-model="form.class_ids" multiple collapse-tags collapse-tags-tooltip placeholder="选择班级">
                <el-option
                  v-for="item in options.classes"
                  :key="item.id"
                  :label="`${item.grade} ${item.name}`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="融合学科" required>
              <el-select v-model="form.subject_ids" multiple collapse-tags collapse-tags-tooltip placeholder="选择学科">
                <el-option v-for="item in options.subjects" :key="item.id" :label="item.name" :value="item.id" />
              </el-select>
            </el-form-item>
          </div>

          <div class="two-cols">
            <el-form-item label="课时数" required>
              <el-input-number v-model="form.lesson_count" :min="1" :max="20" />
            </el-form-item>
            <el-form-item label="核心素养目标">
              <el-select
                v-model="form.core_competencies"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="输入或选择目标"
              >
                <el-option v-for="item in competencyOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item label="跨学科要求">
            <el-input
              v-model="form.interdisciplinary_requirements"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="说明希望哪些学科怎样融合，是否需要真实问题、项目化学习、小组合作等"
            />
          </el-form-item>
          <el-form-item label="评价方式偏好">
            <el-input
              v-model="form.assessment_preferences"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="如：过程性评价+成果展示+同伴互评，重点关注探究能力和表达能力"
            />
          </el-form-item>
          <el-form-item label="资源偏好">
            <el-input
              v-model="form.resource_preferences"
              type="textarea"
              :rows="3"
              maxlength="500"
              show-word-limit
              placeholder="如：任务单、阅读资料包、微课视频、成果展示模板"
            />
          </el-form-item>
          <el-form-item label="补充说明">
            <el-input
              v-model="form.extra_requirements"
              type="textarea"
              :rows="4"
              maxlength="800"
              show-word-limit
              placeholder="填写本校、本班或本节课的特殊要求"
            />
          </el-form-item>
        </el-form>
      </el-card>

      <div class="preview-column">
        <el-card class="status-card" shadow="never">
          <template #header>
            <div class="card-title">
              <span>工作流状态</span>
              <el-tag :type="draft ? 'success' : 'info'" effect="light">{{ draft ? '已生成草案' : '待生成' }}</el-tag>
            </div>
          </template>
          <div class="status-list">
            <div>
              <strong>采纳策略</strong>
              <span>项目自动激活，任务保持草稿，学生端暂不可提交。</span>
            </div>
            <div>
              <strong>桂教通对接</strong>
              <span>当前使用统一JSON协议，后续只替换Provider。</span>
            </div>
            <div v-if="callId">
              <strong>AI调用</strong>
              <span>{{ callId }}</span>
            </div>
          </div>
        </el-card>

        <el-card v-if="adoptResult" class="adopted-card" shadow="never">
          <template #header>
            <div class="card-title">
              <span>已落地</span>
              <el-tag type="success" effect="light">项目已激活</el-tag>
            </div>
          </template>
          <h3>{{ adoptResult.project.name }}</h3>
          <p>已创建 {{ adoptResult.tasks.length }} 个草稿任务、1 个评价量规、{{ adoptResult.resources.length }} 条资源建议。</p>
          <el-button type="primary" @click="router.push(`/teacher/projects/${adoptResult.project.id}`)">
            查看项目
          </el-button>
        </el-card>
      </div>
    </section>

    <section v-if="draft" class="draft-section">
      <div class="section-head">
        <div>
          <span class="eyebrow">Review</span>
          <h2>AI草案审阅</h2>
        </div>
        <div class="head-actions">
          <el-button :icon="Refresh" :loading="generating" @click="generateDraft">重新生成</el-button>
          <el-button type="success" :icon="Check" :loading="adopting" @click="adoptDraft">
            采纳并落地
          </el-button>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="draft-tabs">
        <el-tab-pane label="项目概览" name="project">
          <el-card class="draft-card" shadow="never">
            <div class="two-cols">
              <el-form-item label="项目名称">
                <el-input v-model="draft.project.name" />
              </el-form-item>
              <el-form-item label="课时数">
                <el-input-number v-model="draft.project.lesson_count" :min="1" :max="20" />
              </el-form-item>
            </div>
            <el-form-item label="驱动性问题">
              <el-input v-model="draft.project.driving_question" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="学习目标">
              <el-select v-model="draft.project.objectives" multiple filterable allow-create default-first-option>
                <el-option v-for="item in competencyOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <div class="meta-line">
              <el-tag v-for="item in selectedSubjectNames" :key="item" effect="light">{{ item }}</el-tag>
              <el-tag v-for="item in selectedClassNames" :key="item" type="success" effect="light">{{ item }}</el-tag>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="课时任务" name="tasks">
          <div class="task-list">
            <el-card v-for="(task, index) in draft.tasks" :key="index" class="draft-card" shadow="never">
              <div class="task-head">
                <strong>任务 {{ index + 1 }}</strong>
                <el-tag effect="light">{{ task.task_type }}</el-tag>
              </div>
              <el-form-item label="任务标题">
                <el-input v-model="task.title" />
              </el-form-item>
              <el-form-item label="任务说明">
                <el-input v-model="task.description" type="textarea" :rows="5" />
              </el-form-item>
              <div class="two-cols">
                <el-form-item label="任务类型">
                  <el-select v-model="task.task_type">
                    <el-option label="个人任务" value="individual" />
                    <el-option label="小组任务" value="group" />
                    <el-option label="课堂活动" value="classroom" />
                    <el-option label="课后作业" value="homework" />
                  </el-select>
                </el-form-item>
                <el-form-item label="提交方式">
                  <el-select v-model="task.submit_type">
                    <el-option label="文本" value="text" />
                    <el-option label="文件" value="file" />
                    <el-option label="链接" value="link" />
                    <el-option label="混合" value="mixed" />
                  </el-select>
                </el-form-item>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="评价量规" name="rubric">
          <el-card class="draft-card" shadow="never">
            <div class="two-cols">
              <el-form-item label="量规名称">
                <el-input v-model="draft.rubric.name" />
              </el-form-item>
              <el-form-item label="可见范围">
                <el-select v-model="draft.rubric.scope">
                  <el-option label="个人" value="personal" />
                  <el-option label="校本" value="school" />
                </el-select>
              </el-form-item>
            </div>
            <el-form-item label="量规说明">
              <el-input v-model="draft.rubric.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-table :data="draft.rubric.items" border>
              <el-table-column label="维度" min-width="140">
                <template #default="{ row }">
                  <el-input v-model="row.dimension" />
                </template>
              </el-table-column>
              <el-table-column label="权重" width="120">
                <template #default="{ row }">
                  <el-input-number v-model="row.weight" :min="0" :max="100" :controls="false" />
                </template>
              </el-table-column>
              <el-table-column label="A级描述" min-width="220">
                <template #default="{ row }">
                  <el-input v-model="row.level_a" />
                </template>
              </el-table-column>
              <el-table-column label="B级描述" min-width="220">
                <template #default="{ row }">
                  <el-input v-model="row.level_b" />
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="资源建议" name="resources">
          <div class="resource-grid">
            <el-card v-for="(resource, index) in draft.resources" :key="index" class="draft-card" shadow="never">
              <div class="task-head">
                <strong>资源 {{ index + 1 }}</strong>
                <el-tag effect="light">{{ resource.resource_type }}</el-tag>
              </div>
              <el-form-item label="资源名称">
                <el-input v-model="resource.title" />
              </el-form-item>
              <el-form-item label="资源说明">
                <el-input v-model="resource.description" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item label="建议用法">
                <el-input v-model="resource.suggested_use" type="textarea" :rows="3" />
              </el-form-item>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="教师确认" name="confirm">
          <el-card class="confirm-card" shadow="never">
            <div class="confirm-icon">
              <el-icon><Check /></el-icon>
            </div>
            <h3>确认采纳后，系统将创建真实业务对象</h3>
            <p>项目会进入激活状态；所有任务保持草稿，需要老师在项目详情页逐个发布后学生端才可见。</p>
            <div class="confirm-summary">
              <span>{{ draft.tasks.length }} 个草稿任务</span>
              <span>{{ draft.rubric.items.length }} 个评价维度</span>
              <span>{{ draft.resources.length }} 条资源建议</span>
            </div>
            <el-button type="success" size="large" :icon="Check" :loading="adopting" @click="adoptDraft">
              采纳并创建项目
            </el-button>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { ArrowLeft, Check, MagicStick, Refresh } from '@element-plus/icons-vue'
import { getProject } from '@/api/projects'
import {
  adoptLessonPlanDraft,
  createLessonPlanDraft,
  getLessonPlanOptions
} from '@/api/ai'
import type {
  LessonPlanAdoptResponse,
  LessonPlanDraft,
  LessonPlanDraftRequest,
  LessonPlanWorkflowOptions
} from '@/api/ai'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()

const projectId = computed(() => route.params.id as string | undefined)
const step = ref(0)
const activeTab = ref('project')
const generating = ref(false)
const adopting = ref(false)
const callId = ref('')
const draft = ref<LessonPlanDraft | null>(null)
const adoptResult = ref<LessonPlanAdoptResponse | null>(null)

const options = reactive<LessonPlanWorkflowOptions>({
  subjects: [],
  classes: [],
  agents: []
})

const form = reactive<LessonPlanDraftRequest>({
  agent_id: undefined,
  theme: '',
  grade: '七年级',
  subject_ids: [],
  class_ids: [],
  lesson_count: 5,
  core_competencies: ['问题解决', '跨学科迁移', '合作表达'],
  interdisciplinary_requirements: '围绕真实问题组织项目化学习，要求至少融合两个学科视角。',
  assessment_preferences: '采用过程性评价、成果展示、同伴互评和教师评价相结合。',
  resource_preferences: '优先生成任务单、阅读资料包、评价量规和成果展示模板。',
  extra_requirements: ''
})

const gradeOptions = ['七年级', '八年级', '九年级']
const competencyOptions = ['知识理解', '问题解决', '跨学科迁移', '探究实践', '合作表达', '创新思维', '社会责任']

const selectedSubjectNames = computed(() => {
  const map = new Map(options.subjects.map(item => [item.id, item.name]))
  return form.subject_ids.map(id => map.get(id) || id)
})

const selectedClassNames = computed(() => {
  const map = new Map(options.classes.map(item => [item.id, `${item.grade} ${item.name}`]))
  return form.class_ids.map(id => map.get(id) || id)
})

async function loadOptions() {
  const res = await getLessonPlanOptions()
  Object.assign(options, res.data)
  if (!form.agent_id && options.agents.length) form.agent_id = options.agents[0].id
  if (!form.class_ids.length && options.classes.length) {
    form.class_ids = [options.classes[0].id]
    form.grade = options.classes[0].grade || form.grade
  }
  if (!form.subject_ids.length && options.subjects.length) {
    form.subject_ids = options.subjects.slice(0, 3).map(item => item.id)
  }
}

async function prefillFromProject() {
  if (!projectId.value) return
  const res = await getProject(projectId.value)
  const project = res.data
  form.theme = project.name || project.driving_question
  form.grade = project.grade
  form.subject_ids = project.subjects?.map(item => item.id) || form.subject_ids
  form.class_ids = project.classes?.map(item => item.id) || form.class_ids
  form.lesson_count = project.lesson_count || form.lesson_count
  form.core_competencies = project.objectives?.length ? project.objectives : form.core_competencies
  form.extra_requirements = project.driving_question || ''
}

function validateForm() {
  if (!form.theme.trim()) {
    ElMessage.warning('请先填写教学主题')
    return false
  }
  if (!form.grade.trim()) {
    ElMessage.warning('请先选择年级')
    return false
  }
  if (!form.class_ids.length) {
    ElMessage.warning('请至少选择一个授课班级')
    return false
  }
  if (!form.subject_ids.length) {
    ElMessage.warning('请至少选择一个融合学科')
    return false
  }
  return true
}

async function generateDraft() {
  if (!validateForm()) return
  generating.value = true
  adoptResult.value = null
  try {
    const res = await createLessonPlanDraft({
      ...form,
      theme: form.theme.trim()
    })
    callId.value = res.data.call_id
    draft.value = deepClone(res.data.draft)
    step.value = 1
    activeTab.value = 'project'
    ElMessage.success('AI教学方案草案已生成')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || error?.message || '生成草案失败')
  } finally {
    generating.value = false
  }
}

async function adoptDraft() {
  if (!callId.value || !draft.value) {
    ElMessage.warning('请先生成并审阅AI草案')
    return
  }
  adopting.value = true
  try {
    const res = await adoptLessonPlanDraft(callId.value, draft.value)
    adoptResult.value = res.data
    step.value = 2
    ElMessage.success('AI教学方案已创建为项目，任务保持草稿')
    router.push(`/teacher/projects/${res.data.project.id}`)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || error?.message || '采纳失败')
  } finally {
    adopting.value = false
  }
}

function goBack() {
  if (projectId.value) {
    router.push(`/teacher/projects/${projectId.value}`)
    return
  }
  router.push('/teacher')
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

onMounted(async () => {
  try {
    await loadOptions()
    await prefillFromProject()
    if (!form.theme) form.theme = '海洋生态保护'
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || error?.message || '加载AI备课配置失败')
  }
})
</script>

<style scoped>
.lesson-workflow {
  display: grid;
  gap: 16px;
}

.page-head,
.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  color: #1d5fd1;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.page-head h1,
.section-head h2 {
  margin: 6px 0 8px;
  color: #182b4d;
}

.page-head p {
  color: #64748b;
}

.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.steps-card,
.form-card,
.status-card,
.adopted-card,
.draft-card,
.confirm-card {
  border: 1px solid #e5edf7;
  border-radius: 8px;
}

.workflow-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 16px;
}

.card-title,
.task-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.workflow-form :deep(.el-select),
.workflow-form :deep(.el-input-number) {
  width: 100%;
}

.two-cols {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.preview-column {
  display: grid;
  align-content: start;
  gap: 16px;
}

.status-list {
  display: grid;
  gap: 14px;
}

.status-list div {
  display: grid;
  gap: 5px;
}

.status-list strong,
.adopted-card h3 {
  color: #1f3356;
}

.status-list span,
.adopted-card p {
  color: #667895;
  line-height: 1.6;
}

.draft-section {
  display: grid;
  gap: 12px;
}

.draft-tabs {
  padding: 16px;
  border: 1px solid #e5edf7;
  border-radius: 8px;
  background: #fff;
}

.draft-card {
  margin-bottom: 12px;
}

.task-list,
.resource-grid {
  display: grid;
  gap: 12px;
}

.resource-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.meta-line,
.confirm-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.confirm-card {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 28px;
  text-align: center;
}

.confirm-icon {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  color: #0f9f6e;
  background: #e9f8f1;
  font-size: 26px;
}

.confirm-card h3 {
  color: #1f3356;
}

.confirm-card p {
  max-width: 620px;
  color: #667895;
  line-height: 1.7;
}

.confirm-summary span {
  padding: 8px 12px;
  border-radius: 8px;
  color: #1d5fd1;
  background: #eef5ff;
}

@media (max-width: 1100px) {
  .workflow-grid,
  .resource-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .page-head,
  .section-head,
  .head-actions {
    display: grid;
    width: 100%;
  }

  .two-cols {
    grid-template-columns: 1fr;
  }
}
</style>
