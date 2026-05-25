<template>
  <div class="data-table-wrapper">
    <el-table
      :data="data"
      v-loading="loading"
      :element-loading-text="loadingText"
      :empty-text="emptyText"
      border
      stripe
      highlight-current-row
      class="data-table"
      v-bind="$attrs"
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
    >
      <el-table-column
        v-if="showSelection"
        type="selection"
        width="50"
        align="center"
      />
      <el-table-column
        v-if="showIndex"
        type="index"
        :label="indexLabel"
        width="60"
        align="center"
      />
      <slot />
    </el-table>

    <div v-if="showPagination" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="currentPageSize"
        :page-sizes="pageSizes"
        :total="total"
        :layout="paginationLayout"
        :background="paginationBackground"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  data: any[]
  loading?: boolean
  loadingText?: string
  emptyText?: string
  showPagination?: boolean
  total?: number
  page?: number
  pageSize?: number
  pageSizes?: number[]
  paginationLayout?: string
  paginationBackground?: boolean
  showSelection?: boolean
  showIndex?: boolean
  indexLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  loadingText: '加载中...',
  emptyText: '暂无数据',
  showPagination: true,
  total: 0,
  page: 1,
  pageSize: 10,
  pageSizes: () => [10, 20, 50, 100],
  paginationLayout: 'total, sizes, prev, pager, next, jumper',
  paginationBackground: true,
  showSelection: false,
  showIndex: false,
  indexLabel: '#'
})

const emit = defineEmits<{
  'page-change': [page: number, pageSize: number]
  'size-change': [pageSize: number]
  'selection-change': [selection: any[]]
  'row-click': [row: any, column: any, event: Event]
}>()

const currentPage = ref(props.page)
const currentPageSize = ref(props.pageSize)

watch(() => props.page, (val) => {
  currentPage.value = val
})

watch(() => props.pageSize, (val) => {
  currentPageSize.value = val
})

function handlePageChange(page: number) {
  currentPage.value = page
  emit('page-change', page, currentPageSize.value)
}

function handleSizeChange(pageSize: number) {
  currentPageSize.value = pageSize
  emit('size-change', pageSize)
}

function handleSelectionChange(selection: any[]) {
  emit('selection-change', selection)
}

function handleRowClick(row: any, column: any, event: Event) {
  emit('row-click', row, column, event)
}
</script>

<style scoped>
.data-table-wrapper {
  width: 100%;
}

.data-table {
  width: 100%;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
