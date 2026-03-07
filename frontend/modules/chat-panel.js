// Chat Panel — AI agent interface using Gemini API

const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

// Will be set by the user or from an env var
let geminiApiKey = '';

// System context for the AI
const SYSTEM_PROMPT = `You are an expert land-development due-diligence assistant for the City of Toronto. You help development analysts, planners, and architects understand zoning regulations, building policies, setback requirements, height limits, floor space index (FSI), permitted uses, and development potential.

Your knowledge covers:
- Toronto Zoning Bylaw 569-2013
- Ontario Building Code
- Toronto Official Plan policies
- Development application processes
- Entitlements and variance procedures
- Building envelope constraints (setbacks, angular planes, stepbacks)
- Unit mix and density requirements
- Parking and loading requirements

When answering:
- Be precise and cite bylaw sections when possible
- Provide specific numeric values (heights in metres, setbacks in metres, FSI ratios)
- Distinguish between as-of-right permissions and what requires a variance
- Note when information may have changed due to amendments
- Keep responses concise but thorough

If a parcel address is provided in the conversation context, tailor your answers to that specific location and its zoning.`;

let conversationHistory = [];
let currentParcelContext = '';

/**
 * Initialize the chat panel
 */
export function initChatPanel() {
    const toggle = document.getElementById('chat-toggle');
    const panel = document.getElementById('chat-panel');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');

    // Toggle expanded/collapsed
    toggle.addEventListener('click', () => {
        panel.classList.toggle('expanded');
        if (panel.classList.contains('expanded')) {
            input.focus();
        }
    });

    // Send message
    sendBtn.addEventListener('click', () => sendMessage());
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Listen for parcel selection to add context
    window.addEventListener('parcel-selected', (e) => {
        currentParcelContext = `Current parcel: ${e.detail.address}, Zoning: ${e.detail.zoning}, Lot Area: ${e.detail.lotArea}m²`;
    });

    // Try to load API key from localStorage
    geminiApiKey = localStorage.getItem('gemini_api_key') || '';

    // Check for API key on first expand
    toggle.addEventListener('click', () => {
        if (!geminiApiKey && panel.classList.contains('expanded')) {
            promptForApiKey();
        }
    }, { once: true });
}

/**
 * Ask user for Gemini API key
 */
function promptForApiKey() {
    const key = prompt('Enter your Gemini API key for AI responses.\nGet one free at: https://aistudio.google.com/apikey');
    if (key && key.trim()) {
        geminiApiKey = key.trim();
        localStorage.setItem('gemini_api_key', geminiApiKey);
        appendMessage('assistant', 'API key saved! I\'m ready to answer your questions about zoning, development potential, and land-use policies.');
    }
}

/**
 * Send a user message and get AI response
 */
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    appendMessage('user', text);

    // Add to conversation history
    conversationHistory.push({ role: 'user', parts: [{ text }] });

    if (!geminiApiKey) {
        appendMessage('assistant', 'Please provide a Gemini API key to enable AI responses. Click the chat header to set it up.');
        promptForApiKey();
        return;
    }

    // Show typing indicator
    const typingId = showTypingIndicator();

    try {
        const response = await callGemini(text);
        removeTypingIndicator(typingId);
        appendMessage('assistant', response);
        conversationHistory.push({ role: 'model', parts: [{ text: response }] });
    } catch (err) {
        removeTypingIndicator(typingId);
        console.error('Gemini API error:', err);
        appendMessage('assistant', `I encountered an error: ${err.message}. Please check your API key and try again.`);
    }
}

/**
 * Call the Gemini API
 */
async function callGemini(userMessage) {
    const contextMessage = currentParcelContext
        ? `[Context: ${currentParcelContext}]\n\n${userMessage}`
        : userMessage;

    const body = {
        system_instruction: {
            parts: [{ text: SYSTEM_PROMPT }],
        },
        contents: [
            ...conversationHistory.slice(-10).map(msg => ({
                role: msg.role,
                parts: msg.parts,
            })),
        ],
        generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 1024,
            topP: 0.9,
        },
    };

    // Override the last user message with context
    if (body.contents.length > 0) {
        const lastIdx = body.contents.length - 1;
        body.contents[lastIdx] = {
            role: 'user',
            parts: [{ text: contextMessage }],
        };
    }

    const res = await fetch(`${GEMINI_API_URL}?key=${geminiApiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error?.message || `API returned ${res.status}`);
    }

    const data = await res.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response generated.';
}

/**
 * Append a message to the chat UI
 */
function appendMessage(role, text) {
    const messages = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = `chat-message ${role}`;

    const avatar = role === 'assistant' ? 'AI' : 'You';

    // Simple markdown-like formatting: **bold**, `code`, newlines
    const formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.06);padding:1px 4px;border-radius:3px;font-size:0.85em;">$1</code>')
        .replace(/\n/g, '<br>');

    msg.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content"><p>${formatted}</p></div>
  `;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const messages = document.getElementById('chat-messages');
    const id = 'typing-' + Date.now();
    const indicator = document.createElement('div');
    indicator.id = id;
    indicator.className = 'chat-message assistant';
    indicator.innerHTML = `
    <div class="message-avatar">AI</div>
    <div class="message-content">
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
    messages.appendChild(indicator);
    messages.scrollTop = messages.scrollHeight;
    return id;
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Update the parcel context for the chat
 */
export function setParcelContext(context) {
    currentParcelContext = context;
}
