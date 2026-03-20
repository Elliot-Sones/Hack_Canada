const STORAGE_KEY = 'cocivil_conversations';
const MAX_CONVERSATIONS = 50;

const WELCOME_MESSAGE = {
    role: 'assistant',
    text: "Hello! I'm your development due-diligence assistant. Search for a property above or ask me anything about zoning, policies, or development potential.",
};

function readAll() {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
        return [];
    }
}

function writeAll(conversations) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

function titleFromMessages(messages) {
    const first = messages.find((m) => m.role === 'user');
    if (!first?.text) return 'New conversation';
    return first.text.length > 60 ? first.text.slice(0, 57) + '...' : first.text;
}

export function getConversations() {
    return readAll()
        .map(({ id, title, createdAt, updatedAt }) => ({ id, title, createdAt, updatedAt }))
        .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
}

export function getConversation(id) {
    return readAll().find((c) => c.id === id) || null;
}

export function saveConversation(id, messages) {
    const all = readAll();
    const now = new Date().toISOString();
    const idx = all.findIndex((c) => c.id === id);
    const title = titleFromMessages(messages);

    if (idx >= 0) {
        all[idx].messages = messages;
        all[idx].title = title;
        all[idx].updatedAt = now;
    } else {
        all.push({ id, title, createdAt: now, updatedAt: now, messages });
    }

    // Prune oldest beyond limit
    if (all.length > MAX_CONVERSATIONS) {
        all.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
        all.length = MAX_CONVERSATIONS;
    }

    writeAll(all);
}

export function deleteConversation(id) {
    writeAll(readAll().filter((c) => c.id !== id));
}

export function createConversation() {
    return {
        id: `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        messages: [WELCOME_MESSAGE],
    };
}

export { WELCOME_MESSAGE };
