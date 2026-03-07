// API client — for connecting to the Arterial backend

const API_BASE = '/api/v1';

function authHeaders() {
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}

function getErrorMessage(data, status) {
    if (typeof data?.detail === 'string' && data.detail.trim()) return data.detail;
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
        const messages = data.detail
            .map((item) => (typeof item === 'string' ? item.trim() : item?.msg?.trim?.() || ''))
            .filter(Boolean);
        if (messages.length > 0) return messages.join('; ');
    }
    if (typeof data?.error === 'string' && data.error.trim()) return data.error;
    if (typeof data?.message === 'string' && data.message.trim()) return data.message;
    return `API returned ${status}`;
}

async function apiFetch(url, options = {}) {
    const res = await fetch(url, { ...options, headers: { ...authHeaders(), ...options.headers } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(getErrorMessage(data, res.status));
    return data;
}

// ─── Auth ───

export async function login({ email, password }) {
    return apiFetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
}

export async function register({ email, password, name, organization_name }) {
    return apiFetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        body: JSON.stringify({ email, password, name, organization_name }),
    });
}

// ─── Parcels ───

export async function searchParcels(address) {
    try {
        return await apiFetch(`${API_BASE}/parcels/search?address=${encodeURIComponent(address)}`);
    } catch {
        return [];
    }
}

export async function getParcel(parcelId) {
    try {
        return await apiFetch(`${API_BASE}/parcels/${parcelId}`);
    } catch {
        return null;
    }
}

export async function getPolicyStack(parcelId) {
    try {
        return await apiFetch(`${API_BASE}/parcels/${parcelId}/policy-stack`);
    } catch {
        return { parcel_id: parcelId, applicable_policies: [], citations: [] };
    }
}

export async function getParcelOverlays(parcelId) {
    try {
        return await apiFetch(`${API_BASE}/parcels/${parcelId}/overlays`);
    } catch {
        return { parcel_id: parcelId, overlays: [] };
    }
}

// ─── Assistant ───

export async function parseModel(text, currentParams = null) {
    return apiFetch(`${API_BASE}/assistant/parse-model`, {
        method: 'POST',
        body: JSON.stringify({ text, current_params: currentParams }),
    });
}

export async function chatWithAssistant({ messages, parcelContext = null }) {
    const data = await apiFetch(`${API_BASE}/assistant/chat`, {
        method: 'POST',
        body: JSON.stringify({ messages, parcel_context: parcelContext }),
    });
    if (typeof data?.message !== 'string') throw new Error('Assistant response was malformed.');
    return { message: data.message, proposedAction: data.proposed_action ?? null };
}

// ─── Plans ───

export async function generatePlan(query) {
    return apiFetch(`${API_BASE}/plans/generate`, {
        method: 'POST',
        body: JSON.stringify({ query, auto_run: true }),
    });
}

export async function getPlan(planId) {
    return apiFetch(`${API_BASE}/plans/${planId}`);
}

export async function getPlanDocuments(planId) {
    return apiFetch(`${API_BASE}/plans/${planId}/documents`);
}

// ─── Uploads ───

export async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    // Don't set Content-Type — browser sets it with boundary for multipart
    const res = await fetch(`${API_BASE}/uploads`, {
        method: 'POST',
        headers,
        body: formData,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(getErrorMessage(data, res.status));
    return data;
}

export async function getUpload(uploadId) {
    return apiFetch(`${API_BASE}/uploads/${uploadId}`);
}

export async function getUploadPages(uploadId) {
    return apiFetch(`${API_BASE}/uploads/${uploadId}/pages`);
}

export async function getUploadAnalysis(uploadId) {
    return apiFetch(`${API_BASE}/uploads/${uploadId}/analysis`);
}

export async function generatePlanFromUpload(uploadId, projectName = null) {
    return apiFetch(`${API_BASE}/uploads/${uploadId}/generate-plan`, {
        method: 'POST',
        body: JSON.stringify(projectName ? { project_name: projectName } : {}),
    });
}

export async function generateResponseFromUpload(uploadId, responseType = 'correction_response') {
    return apiFetch(`${API_BASE}/uploads/${uploadId}/generate-response`, {
        method: 'POST',
        body: JSON.stringify({ response_type: responseType }),
    });
}
