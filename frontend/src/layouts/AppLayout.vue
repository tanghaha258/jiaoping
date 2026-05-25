<template>
  <el-container class="app-shell">
    <el-aside :width="sidebarWidth" class="app-aside">
      <div class="brand" :class="{ collapsed: sidebarCollapsed }">
        <div class="brand-mark">
          <span class="brand-dot dot-a"></span>
          <span class="brand-dot dot-b"></span>
          <span class="brand-dot dot-c"></span>
        </div>
        <div v-if="!sidebarCollapsed" class="brand-copy">
          <strong>跨学科教学评一体化</strong>
          <span>AI智能体平台</span>
          <em>广西钦州市教育专属版</em>
        </div>
      </div>
      <RoleMenu :collapsed="sidebarCollapsed" />
    </el-aside>

    <el-container class="workspace">
      <el-header class="app-header">
        <div class="header-left">
          <el-button
            :icon="sidebarCollapsed ? Expand : Fold"
            @click="toggleSidebar"
            circle
            text
            class="icon-button"
            aria-label="折叠菜单"
          />
          <nav class="top-nav" aria-label="主导航">
            <button
              v-for="item in topNav"
              :key="item.label"
              class="top-nav-item"
              :class="{ active: item.path === activeTopPath }"
              type="button"
              @click="navigate(item.path)"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </button>
          </nav>
        </div>

        <div class="header-right">
          <el-button :icon="Search" circle text class="icon-button" aria-label="搜索" />
          <el-badge :value="12" class="notice-badge">
            <el-button :icon="Bell" circle text class="icon-button" aria-label="消息通知" />
          </el-badge>
          <el-button :icon="QuestionFilled" circle text class="icon-button" aria-label="帮助" />
          <el-button :icon="FullScreen" circle text class="icon-button" aria-label="全屏" />
          <el-dropdown trigger="click">
            <span class="user-card">
              <span class="avatar">张</span>
              <span class="user-meta">
                <strong>{{ userName || '张老师' }}</strong>
                <em>钦州市第一中学</em>
              </span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import RoleMenu from './RoleMenu.vue'
import {
  ArrowDown,
  Bell,
  Checked,
  DataAnalysis,
  Expand,
  Files,
  Fold,
  FullScreen,
  Grid,
  Memo,
  Monitor,
  QuestionFilled,
  Search,
  SwitchButton,
  User
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

const { sidebarCollapsed } = storeToRefs(appStore)
const { userName } = storeToRefs(authStore)

const sidebarWidth = computed(() => (sidebarCollapsed.value ? '72px' : '260px'))
const topNav = [
  { label: '工作台', path: '/teacher', icon: Grid },
  { label: '教学设计', path: '/teacher/projects', icon: Memo },
  { label: '智能备课', path: '/teacher/ai/lesson-plan', icon: Files },
  { label: '课堂实施', path: '/teacher/projects', icon: Monitor },
  { label: '学情分析', path: '/teacher/evaluations', icon: DataAnalysis },
  { label: '智能评价', path: '/teacher/evaluations', icon: Checked }
]
const activeTopPath = computed(() => {
  if (route.path.startsWith('/teacher/evaluations')) return '/teacher/evaluations'
  if (route.path.startsWith('/teacher/ai/lesson-plan')) return '/teacher/ai/lesson-plan'
  if (route.path.startsWith('/teacher/projects')) return '/teacher/projects'
  return '/teacher'
})

function toggleSidebar() {
  appStore.toggleSidebar()
}

function navigate(path: string) {
  router.push(path)
}

function handleLogout() {
  authStore.logout()
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: #f3f7fd;
}

.app-aside {
  position: relative;
  z-index: 2;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(15, 78, 179, 0.22), transparent 42%),
    linear-gradient(180deg, #061a3d 0%, #082453 48%, #052a51 100%);
  box-shadow: 12px 0 32px rgba(13, 46, 96, 0.16);
  transition: width 0.24s ease;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 88px;
  padding: 18px 18px 16px;
  color: #ffffff;
}

.brand.collapsed {
  justify-content: center;
  padding-inline: 0;
}

.brand-mark {
  position: relative;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  border-radius: 12px;
  background: linear-gradient(135deg, #6bb9ff, #175cff);
  box-shadow: 0 10px 28px rgba(42, 121, 255, 0.38);
}

.brand-dot {
  position: absolute;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.92);
}

.dot-a {
  width: 18px;
  height: 18px;
  left: 7px;
  top: 7px;
}

.dot-b {
  width: 16px;
  height: 16px;
  right: 6px;
  bottom: 7px;
}

.dot-c {
  width: 13px;
  height: 13px;
  left: 10px;
  bottom: 7px;
  opacity: 0.78;
}

.brand-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.brand-copy strong,
.brand-copy span {
  overflow: hidden;
  font-size: 18px;
  line-height: 1.16;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.brand-copy em {
  margin-top: 4px;
  color: #9dc0f6;
  font-size: 12px;
  font-style: normal;
}

.workspace {
  min-width: 0;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
  padding: 0 26px;
  border-bottom: 1px solid #dce7f5;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(14px);
}

.header-left,
.header-right,
.top-nav,
.top-nav-item,
.user-card {
  display: flex;
  align-items: center;
}

.header-left {
  min-width: 0;
  gap: 14px;
}

.header-right {
  flex: 0 0 auto;
  gap: 10px;
}

.icon-button {
  color: #243553;
}

.top-nav {
  min-width: 0;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}

.top-nav::-webkit-scrollbar {
  display: none;
}

.top-nav-item {
  gap: 7px;
  height: 40px;
  padding: 0 14px;
  border: 0;
  border-radius: 8px;
  color: #30415f;
  background: transparent;
  font: inherit;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.top-nav-item.active {
  color: #075eea;
  background: #eaf2ff;
  box-shadow: inset 0 0 0 1px rgba(55, 125, 255, 0.14);
}

.notice-badge :deep(.el-badge__content) {
  top: 4px;
  right: 7px;
  border: 2px solid #fff;
}

.user-card {
  gap: 10px;
  padding-left: 6px;
  color: #1f2c44;
  cursor: pointer;
}

.avatar {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  color: #ffffff;
  font-weight: 800;
  background: linear-gradient(135deg, #16b38f, #1976ff);
  box-shadow: 0 8px 18px rgba(25, 118, 255, 0.22);
}

.user-meta {
  display: grid;
  gap: 1px;
  line-height: 1.2;
}

.user-meta strong {
  font-size: 14px;
}

.user-meta em {
  color: #7c8ba4;
  font-size: 12px;
  font-style: normal;
}

.app-main {
  min-width: 0;
  padding: 18px;
  overflow: auto;
  background:
    linear-gradient(180deg, rgba(232, 241, 255, 0.86) 0%, rgba(246, 249, 253, 0.96) 36%),
    #f5f8fd;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1160px) {
  .app-header {
    padding-inline: 16px;
  }

  .header-right .icon-button:nth-of-type(n + 3),
  .user-meta {
    display: none;
  }
}
</style>
