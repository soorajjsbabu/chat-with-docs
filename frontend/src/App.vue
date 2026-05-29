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

function onFileChange(e) {
  selectedFiles.value = Array.from(e.target.files)
  uploadStatus.value = ''
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

  try {
    const res = await fetch('http://localhost:8000/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`)
    }

    const data = await res.json()
    messages.value.push({
      role: 'assistant',
      content: data.answer || 'No answer received.',
      sources: data.sources || []
    })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: `Error: ${err.message}`,
      sources: []
    })
  } finally {
    loading.value = false
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
          <p class="content">{{ msg.content }}</p>
          <p v-if="msg.role === 'assistant' && msg.sources.length" class="sources">
            Sources: {{ msg.sources.join(', ') }}
          </p>
        </div>
      </div>

      <div v-if="loading" class="message-row assistant">
        <div class="bubble loading-bubble">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </main>

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
      <div class="file-list">
        <span v-for="file in selectedFiles" :key="file.name" class="file-tag">
          {{ file.name }}
        </span>
        <span v-if="!selectedFiles.length" class="file-placeholder">
          No files selected
        </span>
      </div>
      <button
        :disabled="!selectedFiles.length || uploading"
        class="send-btn"
        @click="uploadFiles"
      >
        {{ uploading ? 'Uploading...' : 'Upload' }}
      </button>
      <p v-if="uploadStatus" class="upload-status">{{ uploadStatus }}</p>
    </div>

    <footer class="input-bar">
      <input
        ref="inputRef"
        v-model="input"
        type="text"
        placeholder="Ask a question..."
        class="input"
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

/* Loading dots */
.loading-bubble {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 1rem 1.25rem;
}

.dot {
  width: 0.5rem;
  height: 0.5rem;
  background-color: #8b949e;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
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

/* Upload bar */
.upload-bar {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background-color: #0d1117;
  border-top: 1px solid #30363d;
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

.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  flex: 1;
  align-items: center;
}

.file-tag {
  padding: 0.25rem 0.5rem;
  background-color: #1f6feb;
  color: #ffffff;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.file-placeholder {
  font-size: 0.875rem;
  color: #484f58;
}

.upload-status {
  width: 100%;
  margin: 0;
  font-size: 0.75rem;
  color: #8b949e;
}
</style>
