<script setup>
import { ref, nextTick, watch } from 'vue'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const chatContainer = ref(null)
const inputRef = ref(null)

const selectedFiles = ref([])
const uploading = ref(false)
const uploadStatus = ref('')
const fileInput = ref(null)

const uploadedFiles = ref([])

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
    uploadStatus.value = `${data.message} (${data.chunks_added} chunks added)`
    uploadedFiles.value.push(...data.files)
    selectedFiles.value = []
  } catch (err) {
    uploadStatus.value = `Upload failed: ${err.message}`
  } finally {
    uploading.value = false
  }
}

async function sendMessage() {
  const question = input.value.trim()
  if (!question || loading.value) return

  // Add user message
  messages.value.push({
    role: 'user',
    content: question,
    sources: []
  })
  input.value = ''
  loading.value = true
  scrollToBottom()

  // Add empty assistant message for streaming
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

      // Process complete SSE events
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
            // It's a token chunk
            messages.value[messages.value.length - 1].content += data
          }
        }
      }
    }

    // Ensure loading is reset if stream ends without [DONE]
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
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })
watch(loading, scrollToBottom)
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>Chat with your Docs</h1>
    </header>

    <main ref="chatContainer" class="chat">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message-row"
        :class="msg.role"
      >
        <div class="bubble">
          <p class="content">
            {{ msg.content }}
            <span
              v-if="loading && index === messages.length - 1 && msg.role === 'assistant'"
              class="cursor"
            >|</span>
          </p>
          <p v-if="msg.role === 'assistant' && msg.sources.length" class="sources">
            Sources: {{ msg.sources.join(', ') }}
          </p>
        </div>
      </div>
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

    <div class="upload-section">
      <div v-if="selectedFiles.length" class="selected-files">
        <span
          v-for="(file, idx) in selectedFiles"
          :key="file.name + '-' + idx"
          class="file-chip"
        >
          {{ file.name }}
          <button class="chip-remove" @click="removeSelectedFile(idx)">&#10005;</button>
        </span>
      </div>

      <div class="upload-bar">
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".pdf,.txt,.md"
          class="hidden-input"
          @change="onFileChange"
        />
        <button class="upload-btn" @click="triggerFileInput">
          Choose Files
        </button>
        <button
          :disabled="!selectedFiles.length || uploading"
          class="send-btn"
          @click="uploadFiles"
        >
          {{ uploading ? 'Uploading...' : 'Upload' }}
        </button>
      </div>
      <p v-if="uploadStatus" class="upload-status">{{ uploadStatus }}</p>
    </div>

    <footer class="input-bar">
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
}

/* Header */
.header {
  flex-shrink: 0;
  padding: 1rem 1.5rem;
  background-color: #161b22;
  border-bottom: 1px solid #30363d;
  text-align: center;
}

.header h1 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #e6edf3;
}

/* Chat area */
.chat {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
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
}

.user .bubble {
  background-color: #1f6feb;
  color: #ffffff;
  border-bottom-right-radius: 0.25rem;
}

.assistant .bubble {
  background-color: #21262d;
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

/* Indexed Documents panel */
.indexed-panel {
  flex-shrink: 0;
  padding: 0.75rem 1.5rem;
  background-color: #0d1117;
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
  background-color: #161b22;
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

/* Upload section */
.upload-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background-color: #0d1117;
  border-top: 1px solid #30363d;
}

.selected-files {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.6rem;
  background-color: #21262d;
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

.upload-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.hidden-input {
  display: none;
}

.upload-btn {
  padding: 0.5rem 1rem;
  background-color: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.upload-btn:hover {
  background-color: #30363d;
}

.upload-status {
  margin: 0;
  font-size: 0.75rem;
  color: #8b949e;
}

/* Input bar */
.input-bar {
  flex-shrink: 0;
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background-color: #161b22;
  border-top: 1px solid #30363d;
}

.input {
  flex: 1;
  padding: 0.75rem 1rem;
  background-color: #0d1117;
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
</style>
