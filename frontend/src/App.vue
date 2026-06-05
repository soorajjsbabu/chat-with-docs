<script setup>
import { ref, nextTick, watch } from 'vue'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const chatContainer = ref(null)
const inputRef = ref(null)
const bottomAnchor = ref(null)

const selectedFiles = ref([])
const uploading = ref(false)
const uploadStatus = ref('')
const fileInput = ref(null)
const isDragOver = ref(false)
const modalOpen = ref(false)
const isTransitioning = ref(false)

const uploadedFiles = ref([])

function openModal() {
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  uploadStatus.value = ''
}

function onFileChange(e) {
  const newFiles = Array.from(e.target.files)
  const combined = [...selectedFiles.value, ...newFiles]
  if (combined.length > 5) {
    uploadStatus.value = 'Maximum 5 files allowed at once'
    e.target.value = ''
    return
  }
  selectedFiles.value = combined
  uploadStatus.value = ''
  e.target.value = ''
}

function removeSelectedFile(index) {
  selectedFiles.value = selectedFiles.value.filter((_, i) => i !== index)
}

function triggerFileInput() {
  fileInput.value?.click()
}

function onDragOver(e) {
  e.preventDefault()
  isDragOver.value = true
}

function onDragLeave() {
  isDragOver.value = false
}

function onDrop(e) {
  e.preventDefault()
  isDragOver.value = false
  const newFiles = Array.from(e.dataTransfer.files)
  const combined = [...selectedFiles.value, ...newFiles]
  if (combined.length > 5) {
    uploadStatus.value = 'Maximum 5 files allowed at once'
    return
  }
  selectedFiles.value = combined
  uploadStatus.value = ''
}

async function uploadFiles() {
  if (!selectedFiles.value.length || uploading.value) return

  uploading.value = true
  uploadStatus.value = 'Uploading...'

  const formData = new FormData()
  for (const file of selectedFiles.value) {
    formData.append('files', file)
  }

  try {
    const res = await fetch('http://localhost:8000/api/upload', {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`)
    }

    const data = await res.json()
    uploadStatus.value = `Processed ${data.files.length} file(s). ${data.chunks_added} chunks added`
    uploadedFiles.value.push(...data.files)
    selectedFiles.value = []

    setTimeout(() => {
      closeModal()
    }, 0.500)
  } catch (err) {
    uploadStatus.value = `Upload failed: ${err.message}`
  } finally {
    uploading.value = false
  }
}

async function sendMessage() {
  const question = input.value.trim()
  if (!question || loading.value) return

  if (messages.value.length === 0) {
    isTransitioning.value = true
    await nextTick()
    setTimeout(() => {
      isTransitioning.value = false
    }, 800)
  }

  messages.value.push({
    role: 'user',
    content: question,
    sources: []
  })
  input.value = ''
  loading.value = true
  scrollToBottom()

  messages.value.push({
    role: 'assistant',
    content: '',
    sources: []
  })

  try {
    const res = await fetch('http://localhost:8000/api/query/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let eventEnd
      while ((eventEnd = buffer.indexOf('\n\n')) !== -1) {
        const event = buffer.slice(0, eventEnd)
        buffer = buffer.slice(eventEnd + 2)

        const dataLines = event.split('\n').filter(l => l.startsWith('data: '))
        const data = dataLines.map(l => l.slice(6)).join('\n')

        if (data === '[DONE]') {
          loading.value = false
        } else {
          try {
            const parsed = JSON.parse(data)
            if (parsed.sources) {
              messages.value[messages.value.length - 1].sources = parsed.sources
            }
          } catch {
            messages.value[messages.value.length - 1].content += data
          }
        }
      }
    }

    loading.value = false
  } catch (err) {
    messages.value[messages.value.length - 1].content = `Error: ${err.message}`
    loading.value = false
  } finally {
    scrollToBottom()
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function scrollToBottom() {
  nextTick(() => {
    bottomAnchor.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

watch(messages, scrollToBottom, { deep: true })
watch(loading, scrollToBottom)
</script>

<template>
  <div class="app">
    <div
      class="title-overlay"
      :class="{ 'is-header': messages.length > 0 || isTransitioning }"
    >
      <h1 class="animated-title">Chat With Your Documents</h1>
      <p
        class="subtitle"
        :class="{ 'is-hidden': messages.length > 0 || isTransitioning }"
      >
        Upload a document and ask anything about it
      </p>
    </div>

    <main
      ref="chatContainer"
      class="chat"
      :class="{ 'has-header': messages.length > 0 || isTransitioning }"
    >
      <template v-if="messages.length">
        <div class="messages-container">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-row"
            :class="msg.role"
          >
            <div class="bubble">
              <p v-if="msg.content" class="content">
                {{ msg.content }}
                <span
                  v-if="loading && index === messages.length - 1 && msg.role === 'assistant'"
                  class="cursor"
                >|</span>
              </p>
              <div
                v-else-if="loading && index === messages.length - 1 && msg.role === 'assistant'"
                class="typing-indicator"
              >
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p v-else class="content"></p>
              <p v-if="msg.role === 'assistant' && msg.sources.length" class="sources">
                Sources: {{ msg.sources.join(', ') }}
              </p>
            </div>
          </div>
          <div ref="bottomAnchor" class="bottom-anchor"></div>
        </div>
      </template>
    </main>

    <div v-if="uploadedFiles.length" class="indexed-panel">
      <h3 class="panel-title">Indexed Documents</h3>
      <div class="indexed-grid">
        <div
          v-for="(name, idx) in uploadedFiles"
          :key="name + '-' + idx"
          class="indexed-card"
        >
          <span class="doc-icon">&#128196;</span>
          <span class="doc-name">{{ name }}</span>
        </div>
      </div>
    </div>

    <footer class="input-bar">
      <button
        class="attach-btn"
        title="Upload documents"
        @click="openModal"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
        </svg>
      </button>
      <input
        ref="inputRef"
        v-model="input"
        type="text"
        placeholder="Ask a question..."
        class="input"
        :disabled="loading"
        @keydown="handleKeydown"
      />
      <button
        :disabled="!input.trim() || loading"
        class="send-btn"
        @click="sendMessage"
      >
        Send
      </button>
    </footer>

    <!-- Upload Modal -->
    <transition name="modal">
      <div v-if="modalOpen" class="modal-overlay" @click.self="closeModal">
        <div class="modal-card">
          <div class="modal-header">
            <h3 class="modal-title">Upload Documents</h3>
            <button class="modal-close" @click="closeModal">&#10005;</button>
          </div>

          <div
            class="modal-drop-zone"
            :class="{ 'drag-over': isDragOver }"
            @dragover.prevent="onDragOver"
            @dragleave="onDragLeave"
            @drop.prevent="onDrop"
            @click="triggerFileInput"
          >
            <div class="drop-zone-content">
              <svg
                class="cloud-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M4 17v2a2 2 0 0 0 2 2h12a`2 `2 0 0 0 2-2v-2" />
                <polyline points="7 11 12 16 17 11" />
                <line x1="12" y1="16" x2="12" y2="4" />
              </svg>
              <p class="drop-text">Drag and drop files here</p>
              <button class="choose-btn" @click.stop="triggerFileInput">
                or Choose Files
              </button>
            </div>
          </div>

          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.txt,.md,.docx,"
            class="hidden-input"
            @change="onFileChange"
          />

          <div v-if="selectedFiles.length" class="modal-selected-files">
            <span
              v-for="(file, idx) in selectedFiles"
              :key="file.name + '-' + idx"
              class="file-chip"
            >
              {{ file.name }}
              <button class="chip-remove" @click="removeSelectedFile(idx)">&#10005;</button>
            </span>
          </div>

          <button
            :disabled="!selectedFiles.length || uploading"
            class="send-btn modal-upload-btn"
            @click="uploadFiles"
          >
            {{ uploading ? 'Uploading...' : 'Upload' }}
          </button>

          <p v-if="uploadStatus" class="modal-status">{{ uploadStatus }}</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<style>
/* Reset / base */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #0d1117;
  color: #c9d1d9;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%);
}

/* Title overlay - transitions between welcome center and header top */
.title-overlay {
  position: fixed;
  z-index: 50;
  text-align: center;
  width: 100%;
  pointer-events: none;
  transition: all 0.7s cubic-bezier(0.4, 0, 0.2, 1);

  /* Welcome state (centered) */
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 0;
  background-color: transparent;
  border-bottom: 1px solid transparent;
  backdrop-filter: blur(0px);
}

.title-overlay.is-header {
  /* Header state (top bar) */
  top: 0;
  left: 0;
  transform: translate(0, 0);
  padding: 0.75rem 1.5rem;
  background-color: rgba(22, 27, 34, 0.6);
  border-bottom: 1px solid #30363d;
  backdrop-filter: blur(8px);
}

.animated-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  color: #e6edf3;
  transition: all 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
}

.title-overlay.is-header .animated-title {
  font-size: 1rem;
  font-weight: 600;
}

.subtitle {
  margin: 0.75rem 0 0 0;
  font-size: 1rem;
  color: #8b949e;
  opacity: 1;
  max-height: 2rem;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.subtitle.is-hidden {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

/* Chat area */
.chat {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: padding-top 0.7s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat.has-header {
  padding-top: 4.5rem;
}

/* Messages container fade-in */
.messages-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  animation: fadeIn 0.5s ease-out;
}

/* Message rows */
.message-row {
  display: flex;
  width: 100%;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

/* Bubble */
.bubble {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  line-height: 1.5;
  word-wrap: break-word;
  animation: fadeIn 0.35s ease-out;
}

.user .bubble {
  background-color: #1f6feb;
  color: #ffffff;
  border-bottom-right-radius: 0.25rem;
}

.assistant .bubble {
  background-color: rgba(33, 38, 45, 0.9);
  color: #c9d1d9;
  border-bottom-left-radius: 0.25rem;
}

.content {
  margin: 0;
}

.sources {
  margin: 0.5rem 0 0 0;
  font-size: 0.75rem;
  color: #8b949e;
}

/* Blinking cursor for streaming */
.cursor {
  display: inline-block;
  width: 0.5rem;
  background-color: #c9d1d9;
  color: transparent;
  animation: blink 1s step-end infinite;
  margin-left: 0.1rem;
  border-radius: 0.1rem;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0;
}

.typing-indicator span {
  width: 0.5rem;
  height: 0.5rem;
  background-color: #8b949e;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-6px);
  }
}

/* Indexed Documents panel */
.indexed-panel {
  flex-shrink: 0;
  padding: 0.75rem 1.5rem;
  background-color: rgba(13, 17, 23, 0.5);
  border-top: 1px solid #30363d;
  max-height: 140px;
  overflow-y: auto;
}

.panel-title {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #8b949e;
}

.indexed-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.indexed-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
  background-color: rgba(22, 27, 34, 0.8);
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #c9d1d9;
}

.doc-icon {
  font-size: 1rem;
  line-height: 1;
}

.doc-name {
  white-space: nowrap;
}

/* Input bar */
.input-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background-color: rgba(22, 27, 34, 0.6);
  backdrop-filter: blur(8px);
  border-top: 1px solid #30363d;
}

.attach-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.75rem;
  height: 2.75rem;
  padding: 0;
  background-color: rgba(13, 17, 23, 0.6);
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  color: #8b949e;
  font-size: 1.25rem;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
  flex-shrink: 0;
}

.attach-btn:hover {
  background-color: #30363d;
  color: #c9d1d9;
}

.input {
  flex: 1;
  padding: 0.75rem 1rem;
  background-color: rgba(13, 17, 23, 0.6);
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  color: #c9d1d9;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.input::placeholder {
  color: #484f58;
}

.input:focus {
  border-color: #1f6feb;
}

.input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-btn {
  padding: 0.75rem 1.5rem;
  background-color: #1f6feb;
  color: #ffffff;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-btn:hover:not(:disabled) {
  background-color: #388bfd;
}

.send-btn:disabled {
  background-color: #21262d;
  color: #484f58;
  cursor: not-allowed;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.25s ease;
}

.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  transform: scale(0.96);
}

.modal-card {
  width: 100%;
  max-width: 28rem;
  margin: 1rem;
  padding: 1.5rem;
  background-color: #161b22;
  border: 1px solid #30363d;
  border-radius: 1rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e6edf3;
}

.modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: transparent;
  border: none;
  color: #8b949e;
  font-size: 1rem;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: background-color 0.2s, color 0.2s;
}

.modal-close:hover {
  background-color: #21262d;
  color: #f85149;
}

.modal-drop-zone {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  border: 2px dashed #30363d;
  border-radius: 0.75rem;
  background-color: rgba(22, 27, 34, 0.5);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.modal-drop-zone.drag-over {
  background-color: rgba(31, 111, 235, 0.1);
  border-color: #1f6feb;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.cloud-icon {
  width: 2.5rem;
  height: 2.5rem;
  color: #8b949e;
}

.drop-text {
  margin: 0;
  font-size: 0.875rem;
  color: #c9d1d9;
}

.choose-btn {
  padding: 0.4rem 1rem;
  background-color: transparent;
  color: #1f6feb;
  border: 1px solid #1f6feb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.choose-btn:hover {
  background-color: #1f6feb;
  color: #ffffff;
}

.hidden-input {
  display: none;
}

.modal-selected-files {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.6rem;
  background-color: rgba(33, 38, 45, 0.8);
  border: 1px solid #30363d;
  border-radius: 0.375rem;
  font-size: 0.8rem;
  color: #c9d1d9;
}

.chip-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  padding: 0;
  background: transparent;
  border: none;
  color: #8b949e;
  font-size: 0.7rem;
  cursor: pointer;
  line-height: 1;
}

.chip-remove:hover {
  color: #f85149;
}

.modal-upload-btn {
  width: 100%;
}

.modal-status {
  margin: 0;
  font-size: 0.875rem;
  color: #8b949e;
  text-align: center;
}

.bottom-anchor {
  height: 1px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
