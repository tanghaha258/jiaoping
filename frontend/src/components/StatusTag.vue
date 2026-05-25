<template>
  <el-tag :type="mappedType" :size="size" :effect="effect" :round="round">
    {{ displayText }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type TagType = '' | 'success' | 'warning' | 'info' | 'danger'

interface Props {
  status: string
  typeMap?: Record<string, TagType>
  textMap?: Record<string, string>
  size?: '' | 'large' | 'default' | 'small'
  effect?: 'dark' | 'light' | 'plain'
  round?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  typeMap: () => ({}),
  textMap: () => ({}),
  size: 'default',
  effect: 'light',
  round: false
})

const mappedType = computed(() => {
  const t = props.typeMap[props.status]
  return t || 'info'
})

const displayText = computed(() => {
  return props.textMap[props.status] || props.status
})
</script>
