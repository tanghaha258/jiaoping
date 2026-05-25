import type { ProjectItem } from '@/api/projects'
import type { TaskItem } from '@/api/tasks'
import type { AIAgent, AICallItem } from '@/api/ai'
import type { EvaluationItem } from '@/api/evaluations'

export const demoProject: ProjectItem = {
  id: 'demo-ocean-project',
  name: '保护海洋，从我做起',
  grade: '七年级',
  status: 'active',
  driving_question: '如何减少生活中的海洋污染，并用跨学科证据提出可执行的校园倡议？',
  lesson_count: 5,
  objectives: [
    '理解海洋生态系统的基本结构和污染影响。',
    '能够收集、整理并可视化海洋污染案例数据。',
    '完成一份有证据支撑的校园环保倡议书。'
  ],
  owner_name: '张老师',
  owner_id: 'user-teacher-0000-0000-0000-0001',
  subjects: [
    { id: 'subject-00000000-0000-0000-0004', name: '地理' },
    { id: 'subject-00000000-0000-0000-0005', name: '生物' },
    { id: 'subject-00000000-0000-0000-0001', name: '语文' },
    { id: 'subject-00000000-0000-0000-0007', name: '信息科技' }
  ],
  classes: [
    { id: 'class-00000000-0000-0000-0001', name: '七年级(1)班' }
  ],
  created_at: '2026-05-20T09:00:00+08:00',
  updated_at: '2026-05-22T09:30:00+08:00'
}

export const demoProjects: ProjectItem[] = [
  demoProject,
  {
    ...demoProject,
    id: 'demo-wetland-project',
    name: '湿地与生物多样性调查',
    status: 'draft',
    driving_question: '如何用科学观察和文字表达说明湿地生态价值？',
    lesson_count: 4,
    subjects: [
      { id: 'subject-00000000-0000-0000-0004', name: '地理' },
      { id: 'subject-00000000-0000-0000-0005', name: '生物' },
      { id: 'subject-00000000-0000-0000-0001', name: '语文' }
    ],
    created_at: '2026-05-19T15:30:00+08:00'
  }
]

export const demoTasks: TaskItem[] = [
  {
    id: 'demo-task-1',
    project_id: demoProject.id,
    title: '课时一：认识海洋生态系统',
    description: '通过图文资料和视频案例梳理海洋生态系统的组成与相互关系。',
    task_type: 'reading',
    submit_type: 'text',
    status: 'published',
    due_at: '2026-05-24T18:00:00+08:00',
    rubric_id: null,
    rubric_name: null,
    submission_count: 42,
    created_at: '2026-05-20T10:00:00+08:00',
    updated_at: '2026-05-20T10:00:00+08:00'
  },
  {
    id: 'demo-task-2',
    project_id: demoProject.id,
    title: '课时二：海洋污染案例调查',
    description: '小组选择一个海洋污染案例，完成成因、影响和治理措施分析。',
    task_type: 'discussion',
    submit_type: 'file',
    status: 'published',
    due_at: '2026-05-25T18:00:00+08:00',
    rubric_id: null,
    rubric_name: null,
    submission_count: 36,
    created_at: '2026-05-21T10:00:00+08:00',
    updated_at: '2026-05-21T10:00:00+08:00'
  },
  {
    id: 'demo-task-3',
    project_id: demoProject.id,
    title: '课时三：数据整理与可视化',
    description: '整理调查数据，用表格或图表呈现污染类型、来源和影响范围。',
    task_type: 'creation',
    submit_type: 'link',
    status: 'draft',
    due_at: null,
    rubric_id: null,
    rubric_name: null,
    submission_count: 0,
    created_at: '2026-05-22T09:00:00+08:00',
    updated_at: '2026-05-22T09:00:00+08:00'
  }
]

export const demoAgents: AIAgent[] = [
  {
    id: 'agent-lesson-plan-0000-0000-0001',
    name: '教案生成智能体',
    provider: 'mock',
    scenario: 'lesson_plan',
    config: { provider: 'mock', model: 'mock-lesson-plan', timeout_seconds: 30, max_retries: 1, extra: {} },
    input_schema: {},
    output_schema: {},
    enabled: true,
    agent_type: 'lesson_plan',
    description: '生成跨学科主题教学设计、任务链和评价量规',
    is_active: true,
    created_at: '2026-05-21T10:00:00+08:00'
  }
]

export const demoLessonPlan = `主题：保护海洋，从我做起

一、教学目标
1. 认识海洋生态系统的组成及污染对生态链的影响。
2. 能够围绕真实案例收集证据，并进行数据整理与可视化表达。
3. 通过倡议书、展示汇报等方式提出可执行的校园环保行动。

二、跨学科任务链
第1课时：认识海洋生态系统，建立核心概念。
第2课时：小组调查海洋污染案例，完成资料卡。
第3课时：用表格和图表整理污染来源、影响和治理措施。
第4课时：撰写校园环保倡议书并进行同伴互评。
第5课时：展示成果，依据量规完成教师评价与反思。

三、评价建议
从知识理解、证据使用、跨学科迁移、合作表达和行动方案五个维度评价。AI建议仅作为辅助，最终评价由教师确认。`

export const demoAICall = (projectId: string, agentId: string): AICallItem => ({
  id: 'demo-ai-call-lesson-plan',
  project_id: projectId,
  agent_id: agentId,
  agent_name: '教案生成智能体',
  call_type: 'lesson_plan',
  input_params: {},
  output_content: demoLessonPlan,
  adopted_content: '',
  status: 'succeeded',
  created_at: '2026-05-22T10:00:00+08:00',
  updated_at: '2026-05-22T10:00:00+08:00'
})

export const demoEvaluations: EvaluationItem[] = [
  {
    id: 'demo-eval-1',
    submission_id: 'demo-submission-1',
    evaluator_id: 'user-teacher-0000-0000-0000-0001',
    evaluator_name: '张老师',
    evaluator_type: 'teacher',
    rubric_id: 'demo-rubric',
    rubric_name: '跨学科探究评价量规',
    scores: { 知识理解: 18, 探究能力: 17, 跨学科迁移: 18, 合作表达: 16, 创新实践: 17 },
    dimension_scores: [
      { dimension: '知识理解', score: 18, max_score: 20, comment: '概念准确，能解释生态关系。' },
      { dimension: '探究能力', score: 17, max_score: 20, comment: '资料来源较充分。' },
      { dimension: '跨学科迁移', score: 18, max_score: 20, comment: '能结合地理与生物证据。' },
      { dimension: '合作表达', score: 16, max_score: 20, comment: '分工清晰，展示还可更凝练。' },
      { dimension: '创新实践', score: 17, max_score: 20, comment: '行动建议具体可执行。' }
    ],
    total_score: 86,
    max_score: 100,
    student_name: '学生一',
    student_id: 'user-student-0000-0000-0000-0001',
    task_id: 'demo-task-2',
    task_title: '海洋污染案例调查',
    comments: '整体完成度较高，能用真实案例支撑观点。建议补充数据来源说明。',
    status: 'draft',
    confirmed_by: null,
    confirmer_name: null,
    created_at: '2026-05-22T09:20:00+08:00',
    updated_at: '2026-05-22T09:20:00+08:00'
  }
]
