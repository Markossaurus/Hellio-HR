import { sendChatQuery } from '../api/chat.js';

let conversationHistory = [];
let isOpen = false;
let hasShownWelcomeMessage = false;
const WELCOME_MESSAGE = 'Hello! I can help you search candidates and positions. Try asking questions like "list open positions" or "show candidates with Python experience".';

export function initChatWidget() {
  if (document.getElementById('chat-widget-button') || document.getElementById('chat-panel')) {
    return;
  }

  createChatButton();
  createChatPanel();
  attachEventListeners();
}

function createChatButton() {
  const button = document.createElement('button');
  button.id = 'chat-widget-button';
  button.className = 'chat-widget-button';
  button.innerHTML = `
    <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
    </svg>
  `;
  document.body.appendChild(button);
}

function createChatPanel() {
  const panel = document.createElement('div');
  panel.id = 'chat-panel';
  panel.className = 'chat-panel';
  panel.style.display = 'none';
  panel.innerHTML = `
    <div class="chat-header">
      <span class="chat-title">HR Assistant</span>
      <button class="chat-close" id="chat-close-btn">&times;</button>
    </div>
    <div class="chat-messages" id="chat-messages"></div>
    <div class="chat-input-area">
      <input 
        type="text" 
        class="chat-input" 
        id="chat-input" 
        placeholder="Ask about candidates or positions..."
      />
      <button class="chat-send" id="chat-send-btn">
        <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  `;
  document.body.appendChild(panel);
}

function attachEventListeners() {
  const button = document.getElementById('chat-widget-button');
  const closeBtn = document.getElementById('chat-close-btn');
  const sendBtn = document.getElementById('chat-send-btn');
  const input = document.getElementById('chat-input');
  
  button.addEventListener('click', toggleChat);
  closeBtn.addEventListener('click', toggleChat);
  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
}

function toggleChat() {
  isOpen = !isOpen;
  const panel = document.getElementById('chat-panel');
  panel.style.display = isOpen ? 'flex' : 'none';
  
  const messagesContainer = document.getElementById('chat-messages');
  const hasWelcomeInUi = Array.from(messagesContainer.children).some((node) => {
    const content = node.querySelector('.chat-message-content');
    return content && content.textContent === WELCOME_MESSAGE;
  });

  if (isOpen && !hasShownWelcomeMessage && !hasWelcomeInUi) {
    addMessage('assistant', WELCOME_MESSAGE);
    hasShownWelcomeMessage = true;
    panel.dataset.welcomeShown = 'true';
  } else if (panel.dataset.welcomeShown === 'true') {
    hasShownWelcomeMessage = true;
  }
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const question = input.value.trim();
  
  if (!question) return;
  
  addMessage('user', question);
  input.value = '';
  
  showLoading();
  
  const response = await sendChatQuery(question, conversationHistory);
  
  hideLoading();
  
  if (response.success && response.answer) {
    addMessage('assistant', response.answer, {
      sql: response.sql,
      rowCount: response.rowCount,
      columns: response.columns
    });
    conversationHistory.push(
      { role: 'user', content: question },
      { role: 'assistant', content: response.answer }
    );
  } else {
    addMessage('assistant', `Error: ${response.error || 'Failed to get response'}`, {
      sql: response.sql
    });
  }
  
  scrollToBottom();
}

function addMessage(role, content, traces = {}) {
  const messagesContainer = document.getElementById('chat-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message chat-message-${role}`;
  
  let traceHtml = '';
  if (traces.sql) {
    traceHtml = `
      <details class="chat-trace">
        <summary>SQL Query (${traces.rowCount !== undefined ? traces.rowCount + ' rows' : 'view'})</summary>
        <pre><code>${escapeHtml(traces.sql)}</code></pre>
      </details>
    `;
  }
  
  messageDiv.innerHTML = `
    <div class="chat-message-content">${escapeHtml(content)}</div>
    ${traceHtml}
  `;
  
  messagesContainer.appendChild(messageDiv);
}

function showLoading() {
  const messagesContainer = document.getElementById('chat-messages');
  const loadingDiv = document.createElement('div');
  loadingDiv.id = 'chat-loading';
  loadingDiv.className = 'chat-message chat-message-assistant';
  loadingDiv.innerHTML = `
    <div class="chat-message-content">
      <span class="chat-loading-dots">...</span>
    </div>
  `;
  messagesContainer.appendChild(loadingDiv);
  scrollToBottom();
}

function hideLoading() {
  const loading = document.getElementById('chat-loading');
  if (loading) loading.remove();
}

function scrollToBottom() {
  const messagesContainer = document.getElementById('chat-messages');
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
