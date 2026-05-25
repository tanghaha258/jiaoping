import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // Public routes
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginPage.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },

  // Redirect root to role-based home
  {
    path: '/',
    redirect: (to) => {
      const userInfo = localStorage.getItem('user_info')
      if (!userInfo) return '/login'
      try {
        const user = JSON.parse(userInfo)
        const roleHomeMap: Record<string, string> = {
          teacher: '/teacher',
          student: '/student',
          researcher: '/research',
          system_admin: '/admin',
          school_admin: '/admin',
          region_admin: '/admin'
        }
        return roleHomeMap[user.role] || '/login'
      } catch {
        return '/login'
      }
    }
  },

  // Teacher routes
  {
    path: '/teacher',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true, roles: ['teacher'], title: '教师工作台' },
    children: [
      {
        path: '',
        name: 'TeacherDashboard',
        component: () => import('@/views/teacher/TeacherDashboard.vue'),
        meta: { title: '工作台' }
      },
      {
        path: 'projects',
        name: 'ProjectList',
        component: () => import('@/views/teacher/ProjectList.vue'),
        meta: { title: '项目管理' }
      },
      {
        path: 'ai/lesson-plan',
        name: 'AILessonPlanCreate',
        component: () => import('@/views/teacher/AILessonPlan.vue'),
        meta: { title: 'AI教学方案' }
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/teacher/ProjectDetail.vue'),
        meta: { title: '项目详情' }
      },
      {
        path: 'projects/:id/ai',
        name: 'AILessonPlan',
        component: () => import('@/views/teacher/AILessonPlan.vue'),
        meta: { title: 'AI教案' }
      },
      {
        path: 'tasks/:id/submissions',
        name: 'SubmissionReview',
        component: () => import('@/views/teacher/SubmissionReview.vue'),
        meta: { title: '提交审核' }
      },
      {
        path: 'evaluations',
        name: 'EvaluationCenter',
        component: () => import('@/views/teacher/EvaluationCenter.vue'),
        meta: { title: '评价中心' }
      },
      {
        path: 'resources',
        name: 'TeacherResourceCenter',
        component: () => import('@/views/teacher/ResourceCenter.vue'),
        meta: { title: '资源中心' }
      },
      {
        path: 'data',
        name: 'TeacherDataCenter',
        component: () => import('@/views/teacher/TeacherDataCenter.vue'),
        meta: { title: '数据中心' }
      },
      {
        path: 'settings',
        name: 'TeacherSettings',
        component: () => import('@/views/teacher/TeacherSettings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  },

  // Student routes
  {
    path: '/student',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true, roles: ['student'], title: '学生学习' },
    children: [
      {
        path: '',
        name: 'StudentDashboard',
        component: () => import('@/views/student/StudentDashboard.vue'),
        meta: { title: '学习概览' }
      },
      {
        path: 'tasks',
        name: 'StudentTaskList',
        component: () => import('@/views/student/StudentTaskList.vue'),
        meta: { title: '学习任务' }
      },
      {
        path: 'tasks/:id',
        name: 'StudentTaskDetail',
        component: () => import('@/views/student/StudentTaskDetail.vue'),
        meta: { title: '任务详情' }
      },
      {
        path: 'submissions/:id',
        name: 'SubmissionDetail',
        component: () => import('@/views/student/SubmissionDetail.vue'),
        meta: { title: '提交详情' }
      },
      {
        path: 'profile',
        name: 'StudentProfile',
        component: () => import('@/views/student/StudentProfile.vue'),
        meta: { title: '我的档案' }
      }
    ]
  },

  // Researcher routes
  {
    path: '/research',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true, roles: ['researcher'], title: '教研工作台' },
    children: [
      {
        path: '',
        name: 'ResearchDashboard',
        component: () => import('@/views/research/ResearchDashboard.vue'),
        meta: { title: '工作台' }
      },
      {
        path: 'templates',
        name: 'TemplateList',
        component: () => import('@/views/research/TemplateList.vue'),
        meta: { title: '模板管理' }
      },
      {
        path: 'resources',
        name: 'ResourceReview',
        component: () => import('@/views/research/ResourceReview.vue'),
        meta: { title: '资源审核' }
      }
    ]
  },

  // Admin routes
  {
    path: '/admin',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true, roles: ['system_admin', 'school_admin', 'region_admin'], title: '管理后台' },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/AdminDashboard.vue'),
        meta: { title: '驾驶舱' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/admin/UserManagement.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'schools',
        name: 'SchoolManagement',
        component: () => import('@/views/admin/SchoolManagement.vue'),
        meta: { title: '学校管理' }
      },
      {
        path: 'ai-agents',
        name: 'AIAgentConfig',
        component: () => import('@/views/admin/AIAgentConfig.vue'),
        meta: { title: 'AI智能体' }
      },
      {
        path: 'ai-calls',
        name: 'AICallHistory',
        component: () => import('@/views/admin/AICallHistory.vue'),
        meta: { title: 'AI调用' }
      },
      {
        path: 'audit-logs',
        name: 'AuditLogViewer',
        component: () => import('@/views/admin/AuditLogViewer.vue'),
        meta: { title: '审计日志' }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/admin/SystemSettings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  },

  // 403 Forbidden
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/ForbiddenPage.vue'),
    meta: { requiresAuth: false, title: '403 无权限' }
  },

  // 404 catch-all
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/ForbiddenPage.vue'),
    meta: { requiresAuth: false, title: '404 页面未找到' }
  }
]

export default routes
