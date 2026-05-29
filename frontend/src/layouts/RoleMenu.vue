<template>
  <el-menu
    :default-active="activeMenu"
    :collapse="collapsed"
    class="role-menu"
    background-color="transparent"
    text-color="#b8c9e6"
    active-text-color="#ffffff"
    @select="handleSelect"
  >
    <template v-for="section in visibleSections" :key="section.title">
      <div v-if="!collapsed" class="menu-section">{{ section.title }}</div>
      <el-menu-item
        v-for="item in section.items"
        :key="item.index"
        :index="item.index"
        class="menu-item"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <template #title>
          <span>{{ item.label }}</span>
          <el-icon v-if="item.actionable" class="chevron"><ArrowRight /></el-icon>
        </template>
      </el-menu-item>
    </template>
  </el-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRight,
  Checked,
  ChatDotRound,
  Collection,
  Connection,
  Cpu,
  DataAnalysis,
  DataBoard,
  Document,
  Files,
  Folder,
  Grid,
  HomeFilled,
  Management,
  Memo,
  Monitor,
  Notebook,
  Odometer,
  OfficeBuilding,
  Platform,
  Reading,
  School,
  Setting,
  Tickets,
  TrendCharts,
  User,
  UserFilled
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  collapsed: boolean
}>()

type MenuItem = {
  index: string
  label: string
  icon: unknown
  actionable?: boolean
}

type MenuSection = {
  title: string
  items: MenuItem[]
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const teacherSections: MenuSection[] = [
  {
    title: '教学核心应用',
    items: [
      { index: '/teacher', label: '工作台', icon: Grid, actionable: true },
      { index: '/teacher/ai/lesson-plan', label: 'AI生成教学方案', icon: Document, actionable: true },
      { index: '/teacher/projects?type=task', label: '跨学科任务设计', icon: Management },
      { index: '/teacher/evaluations?type=diagnosis', label: '学情诊断与分析', icon: DataAnalysis, actionable: true },
      { index: '/teacher/projects?type=classroom', label: '课堂互动工具', icon: ChatDotRound },
      { index: '/teacher/evaluations', label: '智能评价与反馈', icon: Checked, actionable: true },
      { index: '/teacher/evaluations?type=improve', label: '教学改进建议', icon: TrendCharts }
    ]
  },
  {
    title: '资源与知识库',
    items: [
      { index: '/teacher/resources?type=region', label: '区域教材中心', icon: Files },
      { index: '/teacher/resources', label: '教学资源库', icon: Folder },
      { index: '/teacher/resources?type=questions', label: '题库中心', icon: Notebook },
      { index: '/teacher/resources?type=cases', label: '案例库', icon: Collection },
      { index: '/teacher/resources?type=video', label: '微课资源', icon: Monitor }
    ]
  },
  {
    title: '数据与管理',
    items: [
      { index: '/teacher/data?type=class', label: '班级数据看板', icon: DataBoard },
      { index: '/teacher/data?type=school', label: '学校管理', icon: School },
      { index: '/teacher/data?type=region', label: '区域驾驶舱', icon: Odometer },
      { index: '/teacher/settings', label: '系统设置', icon: Setting }
    ]
  }
]

const menuByRole: Record<string, MenuSection[]> = {
  student: [
    {
      title: '学习空间',
      items: [
        { index: '/student', label: '学习概览', icon: HomeFilled, actionable: true },
        { index: '/student/tasks', label: '学习任务', icon: Notebook, actionable: true },
        { index: '/student/profile', label: '我的档案', icon: User, actionable: true }
      ]
    }
  ],
  researcher: [
    {
      title: '教研协同',
      items: [
        { index: '/research', label: '工作台', icon: HomeFilled, actionable: true },
        { index: '/research/templates', label: '模板管理', icon: Tickets, actionable: true },
        { index: '/research/resources', label: '资源审核', icon: Checked, actionable: true }
      ]
    }
  ],
  system_admin: [
    {
      title: '平台治理',
      items: [
        { index: '/admin', label: '驾驶舱', icon: Odometer, actionable: true },
        { index: '/admin/trial-delivery', label: '试点交付包', icon: Tickets, actionable: true },
        { index: '/admin/users', label: '用户管理', icon: UserFilled, actionable: true },
        { index: '/admin/schools', label: '学校管理', icon: OfficeBuilding, actionable: true },
        { index: '/admin/ai-agents', label: 'AI智能体', icon: Cpu, actionable: true },
        { index: '/admin/ai-calls', label: 'AI调用', icon: Connection, actionable: true },
        { index: '/admin/audit-logs', label: '审计日志', icon: Memo, actionable: true },
        { index: '/admin/settings', label: '系统设置', icon: Setting, actionable: true }
      ]
    }
  ]
}

const visibleSections = computed(() => {
  const role = authStore.userRole || 'teacher'
  if (role === 'teacher') return teacherSections
  if (role === 'school_admin' || role === 'region_admin') return menuByRole.system_admin
  return menuByRole[role] || teacherSections
})

const activeMenu = computed(() => {
  if (route.path.startsWith('/teacher/ai/lesson-plan')) return '/teacher/ai/lesson-plan'
  if (route.path.startsWith('/teacher/evaluations')) return '/teacher/evaluations'
  if (route.path.startsWith('/teacher/projects')) return '/teacher/projects'
  return route.path
})

function handleSelect(index: string) {
  const path = index.split('?')[0]
  const availableRoots = ['/teacher', '/teacher/ai/lesson-plan', '/teacher/projects', '/teacher/evaluations', '/student', '/student/tasks', '/student/profile', '/research', '/research/templates', '/research/resources', '/admin', '/admin/trial-delivery', '/admin/users', '/admin/schools', '/admin/ai-agents', '/admin/ai-calls', '/admin/audit-logs', '/admin/settings']

  if (availableRoots.includes(path)) {
    router.push(index)
  }
}
</script>

<style scoped>
.role-menu {
  height: calc(100vh - 88px);
  overflow-y: auto;
  border-right: none;
  padding: 8px 10px 20px;
}

.role-menu:not(.el-menu--collapse) {
  width: 260px;
}

.menu-section {
  padding: 14px 10px 8px;
  color: #6f92c9;
  font-size: 12px;
  line-height: 1;
}

.menu-item {
  height: 42px;
  margin: 4px 0;
  border-radius: 8px;
  --el-menu-hover-bg-color: rgba(72, 134, 255, 0.16);
}

.menu-item.is-active {
  background: linear-gradient(90deg, #1c76ff, #075df4);
  box-shadow: 0 10px 22px rgba(17, 99, 255, 0.28);
}

.menu-item :deep(.el-menu-tooltip__trigger),
.menu-item :deep(.el-tooltip__trigger) {
  justify-content: center;
}

.menu-item span {
  display: inline-block;
  max-width: 170px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chevron {
  position: absolute;
  right: 12px;
  color: currentColor;
  opacity: 0.72;
}
</style>
