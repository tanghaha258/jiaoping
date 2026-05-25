<template>
  <div class="submission-detail-page">
    <div class="page-nav">
      <el-button :icon="ArrowLeft" @click="goBack">返回任务详情</el-button>
    </div>

    <!-- Submission Content Card -->
    <el-card class="detail-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">提交详情</span>
          <StatusTag
            v-if="submission"
            :status="submission.status"
            :type-map="statusTypeMap"
            :text-map="statusTextMap"
          />
        </div>
      </template>

      <template v-if="submission">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学生">
            {{ submission.student_name }}
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">
            {{ submission.submitted_at }}
          </el-descriptions-item>
          <el-descriptions-item label="批阅状态" :span="2">
            <StatusTag
              :status="submission.status"
              :type-map="statusTypeMap"
              :text-map="statusTextMap"
            />
          </el-descriptions-item>
          <el-descriptions-item label="提交内容" :span="2">
            <div class="content-box">{{ submission.content }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>

    <!-- Evaluation Section -->
    <el-card v-if="evaluation" class="eval-card">
      <template #header>
        <span class="card-title">教师评价</span>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="评价人">
          {{ evaluation.evaluator_name }}
        </el-descriptions-item>
        <el-descriptions-item label="评价方式">
          <el-tag size="small" type="info">
            {{ evaluatorTextMap[evaluation.evaluator_type] || evaluation.evaluator_type }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="评价量规">
          {{ evaluation.rubric_name }}
        </el-descriptions-item>
        <el-descriptions-item label="评价时间">
          {{ evaluation.created_at }}
        </el-descriptions-item>
        <el-descriptions-item label="总分" :span="2">
          <span class="score-display">
            {{ evaluation.total_score }} / {{ evaluation.max_score }}
          </span>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">维度评分</el-divider>
      <el-table
        v-if="evaluation.dimension_scores && evaluation.dimension_scores.length > 0"
        :data="evaluation.dimension_scores"
        border
        size="small"
      >
        <el-table-column prop="dimension" label="评分维度" />
        <el-table-column label="得分" width="120" align="center">
          <template #default="{ row }">
            <span class="dimension-score">{{ row.score }} / {{ row.max_score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="comment" label="维度评语" min-width="220" show-overflow-tooltip />
      </el-table>

      <el-divider content-position="left">综合评语</el-divider>
      <div class="comment-box">{{ evaluation.comments || '暂无评语' }}</div>
    </el-card>

    <div v-if="!submission && !loading" class="empty-hint">
      未找到提交记录
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getSubmission } from '@/api/tasks'
import type { SubmissionItem } from '@/api/tasks'
import { getStudentEvaluations } from '@/api/evaluations'
import type { EvaluationItem } from '@/api/evaluations'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const router = useRouter()

const submissionId = route.params.id as string

const statusTypeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  submitted: 'info',
  reviewed: 'success'
}

const statusTextMap: Record<string, string> = {
  submitted: '待批阅',
  reviewed: '已批阅'
}

const evaluatorTextMap: Record<string, string> = {
  teacher: '教师',
  ai: 'AI',
  self: '自评',
  peer: '互评'
}

const submission = ref<SubmissionItem | null>(null)
const evaluation = ref<EvaluationItem | null>(null)
const loading = ref(false)

function goBack() {
  if (submission.value?.task_id) {
    router.push(`/student/tasks/${submission.value.task_id}`)
  } else {
    router.push('/student/tasks')
  }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getSubmission(submissionId)
    submission.value = res.data

    // Load evaluation if reviewed
    if (res.data.status === 'reviewed') {
      try {
        const evalRes = await getStudentEvaluations({ page: 1, page_size: 50 })
        const matchingEval = (evalRes.data.items || []).find(
          (e: EvaluationItem) => e.submission_id === submissionId
        )
        if (matchingEval) {
          evaluation.value = matchingEval
        }
      } catch {
        // Evaluation may not exist
      }
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '加载提交详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.submission-detail-page {
  padding: 0;
}

.page-nav {
  margin-bottom: 16px;
}

.detail-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.eval-card {
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

.content-box {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  line-height: 1.8;
}

.score-display {
  color: #409eff;
  font-weight: 700;
  font-size: 18px;
}

.dimension-score {
  color: #409eff;
  font-weight: 600;
}

.comment-box {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  line-height: 1.8;
  white-space: pre-wrap;
  min-height: 60px;
}

.empty-hint {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  font-size: 14px;
}
</style>
