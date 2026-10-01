<template>
  <div class="er-demos-section">
    <div class="er-section-head">
      <div class="er-label">
        // reproductor de demos
      </div>
      <ErButton
        v-if="canEdit"
        variant="primary"
        icon="plus"
        @click="showUploadModal = true"
      >
        Subir demo
      </ErButton>
    </div>

    <ErDemoPlayer
      :takes="takesWithSrc"
      :author="currentUserDisplayName"
      @comment="handleComment"
    />

    <DemoUploadModal
      v-if="showUploadModal"
      :composition-id="compositionId"
      @close="showUploadModal = false"
      @uploaded="handleUploaded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ErButton, ErDemoPlayer, type DemoTake, type DemoComment } from '@/design-system'
import { addComment, getPlaybackUrl, listComments } from '@/api/demos'
import DemoUploadModal from './DemoUploadModal.vue'

const props = withDefaults(
  defineProps<{
    compositionId: string
    demos: DemoTake[]
    canEdit?: boolean
    currentUserDisplayName?: string
  }>(),
  {
    canEdit: false,
    currentUserDisplayName: 'Tú',
  }
)

const emit = defineEmits<{
  (e: 'updated', demos: DemoTake[]): void
}>()

const localDemos = ref<DemoTake[]>(props.demos.slice())
const showUploadModal = ref(false)

const takesWithSrc = computed(() => {
  return localDemos.value
})

async function handleComment(takeId: string, comment: DemoComment) {
  try {
    await addComment(props.compositionId, takeId, comment.text, comment.t)
  } catch {
    // Non-blocking fallback
  }
}

/**
 * Returns a copy of the take with its playback src and comments resolved.
 * Each lookup is failure-tolerant: a failing request leaves that field untouched.
 * Known limitation: signed URLs are short-lived (`expires_at`); no refresh logic yet.
 */
async function resolveTake(take: DemoTake): Promise<DemoTake> {
  const [url, comments] = await Promise.allSettled([
    getPlaybackUrl(props.compositionId, take.id),
    listComments(props.compositionId, take.id),
  ])
  return {
    ...take,
    src: url.status === 'fulfilled' ? url.value.url : take.src,
    comments: comments.status === 'fulfilled' ? comments.value : take.comments,
  }
}

onMounted(async () => {
  const initial = localDemos.value.slice()
  if (initial.length === 0) return
  const resolved = await Promise.allSettled(initial.map(resolveTake))
  const byId = new Map<string, DemoTake>()
  resolved.forEach((r, i) => {
    if (r.status === 'fulfilled') byId.set(initial[i].id, r.value)
  })
  // Keep any take uploaded while resolving; swap in the resolved copies.
  localDemos.value = localDemos.value.map((t) => byId.get(t.id) ?? t)
})

async function handleUploaded(demo: DemoTake) {
  showUploadModal.value = false
  const resolved = await resolveTake(demo)
  localDemos.value.push(resolved)
  emit('updated', localDemos.value)
}
</script>
