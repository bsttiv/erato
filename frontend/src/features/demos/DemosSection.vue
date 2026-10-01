<template>
  <div class="er-demos-section">
    <div class="er-row" style="justify-content: space-between; align-items: center; margin-bottom: var(--space-4)">
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
import { ref, computed } from 'vue'
import { ErButton, ErDemoPlayer, type DemoTake, type DemoComment } from '@/design-system'
import { addComment, getPlaybackUrl } from '@/api/demos'
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

async function handleUploaded(demo: DemoTake) {
  showUploadModal.value = false
  // Resolve playback url
  try {
    const { url } = await getPlaybackUrl(props.compositionId, demo.id)
    demo.src = url
  } catch {
    // URL fallback
  }
  localDemos.value.push(demo)
  emit('updated', localDemos.value)
}
</script>
