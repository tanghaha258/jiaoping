import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import routes from './routes'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/api'

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Route guard: authentication and role-based access control
router.beforeEach(async (to: RouteLocationNormalized, from: RouteLocationNormalized) => {
  const authStore = useAuthStore()

  // Initialize auth from localStorage on first navigation
  if (!authStore.token && !authStore.user) {
    authStore.initFromStorage()
  }

  const isLoggedIn = !!authStore.token
  const userRole = authStore.userRole

  // 1. Route requires auth but user is not logged in
  if (to.meta.requiresAuth && !isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // 2. Route has role check and user role is not in the allowed list
  if (to.meta.roles && isLoggedIn) {
    const allowedRoles = to.meta.roles as UserRole[]
    if (userRole && !allowedRoles.includes(userRole as UserRole)) {
      return { path: '/403' }
    }
  }

  // 3. User is logged in and going to /login -> redirect to role-appropriate home
  if (isLoggedIn && to.path === '/login') {
    const roleHomeMap: Record<string, string> = {
      teacher: '/teacher',
      student: '/student',
      researcher: '/research',
      system_admin: '/admin',
      school_admin: '/admin',
      region_admin: '/admin'
    }
    const path = roleHomeMap[userRole] || '/'
    return { path }
  }

  // Set page title
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智跨学评`
  }

  return true
})

export default router
