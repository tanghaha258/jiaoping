import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface BreadcrumbItem {
  title: string
  path?: string
}

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref<boolean>(false)
  const pageLoading = ref<boolean>(false)
  const breadcrumbs = ref<BreadcrumbItem[]>([])

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setPageLoading(loading: boolean) {
    pageLoading.value = loading
  }

  function setBreadcrumbs(items: BreadcrumbItem[]) {
    breadcrumbs.value = items
  }

  return {
    sidebarCollapsed,
    pageLoading,
    breadcrumbs,
    toggleSidebar,
    setPageLoading,
    setBreadcrumbs
  }
})
