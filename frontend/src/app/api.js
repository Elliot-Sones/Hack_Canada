// API client — for connecting to the CoCivil backend

const API_BASE = '/api/v1';

// ─── Simple in-memory GET cache (5-min TTL, 200-entry cap) ───

const _cache = new Map();
const CACHE_TTL_MS = 5 * 60 * 1000;

function getCached(url) {
    const entry = _cache.get(url);
    if (!entry) return undefined;
    if (Date.now() - entry.ts > CACHE_TTL_MS) {
        _cache.delete(url);
        return undefined;
    }
    return entry.data;
}

function setCache(url, data) {
    _cache.set(url, { data, ts: Date.now() });
    if (_cache.size > 200) {
        const oldest = _cache.keys().next().value;
        _cache.delete(oldest);
    }
}

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

function isAbortError(error) {
    return error?.name === 'AbortError';
}

async function apiFetch(url, options = {}) {
    const res = await fetch(url, { ...options, headers: { ...authHeaders(), ...options.headers } });
    const data = await res.json().catch(() => ({}));

    if (res.status === 401 && !options._retried) {
        try {
            await sessionExchange();
            return apiFetch(url, { ...options, _retried: true });
        } catch {
            // sessionExchange failed too — user is truly unauthenticated
        }
    }

    if (!res.ok) {
        const error = new Error(getErrorMessage(data, res.status));
        error.status = res.status;
        error.data = data;
        throw error;
    }
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

export async function sessionExchange() {
    const res = await fetch('/api/auth/exchange', { method: 'POST' });
    if (!res.ok) throw new Error('Session exchange failed');
    const data = await res.json();
    localStorage.setItem('token', data.access_token);
    return data;
}

export function hasFastApiToken() { return !!localStorage.getItem('token'); }
export function clearFastApiToken() { localStorage.removeItem('token'); }

// ─── Parcels ───

export async function searchParcels(address, { lat, lng } = {}) {
    let url = `${API_BASE}/parcels/search?address=${encodeURIComponent(address)}`;
    if (lat != null && lng != null) url += `&lat=${lat}&lng=${lng}`;
    const cached = getCached(url);
    if (cached) return cached;
    try {
        const data = await apiFetch(url);
        setCache(url, data);
        return data;
    } catch {
        return [];
    }
}

export async function searchParcelsBbox(bounds, zoom, options = {}) {
    if (zoom < 15) return { type: 'FeatureCollection', features: [] };
    try {
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        const url = `${API_BASE}/parcels/search?bbox=${sw.lng},${sw.lat},${ne.lng},${ne.lat}&page_size=500`;
        const parcels = await apiFetch(url, options);
        return {
            type: 'FeatureCollection',
            features: (parcels || []).filter(p => p.geom).map(p => ({
                type: 'Feature',
                id: p.id,
                properties: {
                    id: p.id,
                    address: (p.address && p.address !== 'None None' && p.address !== 'None') ? p.address : '',
                    zone_code: p.zone_code || '',
                    lot_area_m2: p.lot_area_m2 || 0,
                },
                geometry: p.geom,
            })),
        };
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { type: 'FeatureCollection', features: [] };
    }
}

export async function getParcel(parcelId, options = {}) {
    const url = `${API_BASE}/parcels/${parcelId}`;
    const cached = getCached(url);
    if (cached) return cached;
    try {
        const data = await apiFetch(url, options);
        setCache(url, data);
        return data;
    } catch (error) {
        if (isAbortError(error)) throw error;
        return null;
    }
}

export async function getPolicyStack(parcelId, options = {}) {
    const url = `${API_BASE}/parcels/${parcelId}/policy-stack`;
    const cached = getCached(url);
    if (cached) return cached;
    try {
        const data = await apiFetch(url, options);
        setCache(url, data);
        return data;
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { parcel_id: parcelId, applicable_policies: [], citations: [] };
    }
}

export async function getParcelOverlays(parcelId, options = {}) {
    const url = `${API_BASE}/parcels/${parcelId}/overlays`;
    const cached = getCached(url);
    if (cached) return cached;
    try {
        const data = await apiFetch(url, options);
        setCache(url, data);
        return data;
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { parcel_id: parcelId, overlays: [] };
    }
}

export async function getParcelZoningAnalysis(parcelId, options = {}) {
    const url = `${API_BASE}/parcels/${parcelId}/zoning-analysis`;
    const cached = getCached(url);
    if (cached) return cached;
    try {
        const data = await apiFetch(url, options);
        setCache(url, data);
        return data;
    } catch (error) {
        if (isAbortError(error)) throw error;
        return null;
    }
}

export async function getNearbyApplications(parcelId, options = {}) {
    try {
        return await apiFetch(`${API_BASE}/parcels/${parcelId}/nearby-applications`, options);
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { parcel_id: parcelId, applications: [], total: 0 };
    }
}

export async function getParcelFinancialSummary(parcelId, options = {}) {
    try {
        return await apiFetch(`${API_BASE}/parcels/${parcelId}/financial-summary`, options);
    } catch (error) {
        if (isAbortError(error)) throw error;
        return null;
    }
}

// ─── Assistant ───

export async function parseModel(text, currentParams = null, zoneCode = null, lotAreaM2 = null) {
    const payload = { text, current_params: currentParams };
    if (zoneCode) payload.zone_code = zoneCode;
    if (lotAreaM2) payload.lot_area_m2 = lotAreaM2;
    return apiFetch(`${API_BASE}/assistant/parse-model`, {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function chatWithAssistant({ messages, parcelContext = null, parcelId = null, lat = null, lng = null, modelParams = null, zoneCode = null, zoneCodes = null, uploadContext = null }) {
    const payload = { messages, parcel_context: parcelContext };
    if (parcelId) payload.parcel_id = parcelId;
    if (lat != null) payload.lat = lat;
    if (lng != null) payload.lng = lng;
    if (modelParams) payload.model_params = modelParams;
    if (zoneCode) payload.zone_code = zoneCode;
    if (zoneCodes?.length) payload.zone_codes = zoneCodes;
    if (uploadContext?.length) payload.upload_context = uploadContext;
    const data = await apiFetch(`${API_BASE}/assistant/chat`, {
        method: 'POST',
        body: JSON.stringify(payload),
    });
    if (typeof data?.message !== 'string') throw new Error('Assistant response was malformed.');
    return {
        message: data.message,
        proposedAction: data.proposed_action ?? null,
        modelUpdate: data.model_update ?? null,
        contractors: data.contractors ?? [],
    };
}

// ─── Plans ───

export async function generatePlan(query, generateSubset = null, projectId = null, parcelIds = null) {
    const body = { query, auto_run: true };
    if (generateSubset && generateSubset !== 'all') {
        body.generate_subset = generateSubset;
    }
    if (projectId) body.project_id = projectId;
    if (parcelIds && parcelIds.length >= 2) body.parcel_ids = parcelIds;
    return apiFetch(`${API_BASE}/plans/generate`, {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

export async function getPlan(planId, options = {}) {
    return apiFetch(`${API_BASE}/plans/${planId}`, options);
}

export async function getPlanDocuments(planId, options = {}) {
    return apiFetch(`${API_BASE}/plans/${planId}/documents`, options);
}

export async function regeneratePlanDocument(planId, docType, extraContext = {}) {
    return apiFetch(`${API_BASE}/plans/${planId}/generate-document/${docType}`, {
        method: 'POST',
        body: JSON.stringify({ extra_context: extraContext }),
    });
}

export async function downloadPlanDocument(planId, docId, format = 'markdown') {
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(
        `${API_BASE}/plans/${planId}/documents/${docId}/download?format=${format}`,
        { headers }
    );
    if (!res.ok) throw new Error(`Download failed: ${res.status}`);
    return res;
}

export async function exportPlan(planId) {
    return apiFetch(`${API_BASE}/plans/${planId}/export`, {
        method: 'POST',
    });
}

// ─── Contractors ───

export async function getContractorRecommendations(planId, lat, lng) {
    try {
        return await apiFetch(`${API_BASE}/plans/${planId}/contractors?lat=${lat}&lng=${lng}`);
    } catch {
        return { contractors: [] };
    }
}

// ─── Uploads ───

export async function uploadDocument(file, options = {}) {
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
        signal: options.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const error = new Error(getErrorMessage(data, res.status));
        error.status = res.status;
        error.data = data;
        throw error;
    }
    return data;
}

export async function getUpload(uploadId, options = {}) {
    return apiFetch(`${API_BASE}/uploads/${uploadId}`, options);
}

export async function getUploadPages(uploadId, options = {}) {
    return apiFetch(`${API_BASE}/uploads/${uploadId}/pages`, options);
}

export async function getUploadAnalysis(uploadId, options = {}) {
    return apiFetch(`${API_BASE}/uploads/${uploadId}/analysis`, options);
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

// ─── Infrastructure ───

export async function getNearbyPipelines(lat, lng, radius = 500, pipeType = null, options = {}) {
    let url = `${API_BASE}/infrastructure/pipelines/nearby?lat=${lat}&lng=${lng}&radius_m=${radius}`;
    if (pipeType) url += `&pipe_type=${pipeType}`;
    const cached = getCached(url);
    if (cached) return cached;
    try {
        const data = await apiFetch(url, options);
        setCache(url, data);
        return data;
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { type: 'FeatureCollection', features: [] };
    }
}

export async function getWatermainsBbox(bounds, options = {}) {
    try {
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        const url = `${API_BASE}/infrastructure/watermains/bbox?min_lng=${sw.lng}&min_lat=${sw.lat}&max_lng=${ne.lng}&max_lat=${ne.lat}`;
        return await apiFetch(url, options);
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { type: 'FeatureCollection', features: [] };
    }
}

export async function checkPipelineCompliance(params) {
    return apiFetch(`${API_BASE}/infrastructure/compliance/pipeline`, {
        method: 'POST',
        body: JSON.stringify(params),
    });
}

export async function parseInfraModel(text, currentParams = null, assetType = 'pipeline') {
    return apiFetch(`${API_BASE}/assistant/parse-infra-model`, {
        method: 'POST',
        body: JSON.stringify({ text, current_params: currentParams, asset_type: assetType }),
    });
}

export async function triggerWaterMainIngestion() {
    return apiFetch(`${API_BASE}/admin/ingest/water-mains`, { method: 'POST' });
}

export async function triggerSanitarySewerIngestion() {
    return apiFetch(`${API_BASE}/admin/ingest/sanitary-sewers`, { method: 'POST' });
}

export async function triggerStormSewerIngestion() {
    return apiFetch(`${API_BASE}/admin/ingest/storm-sewers`, { method: 'POST' });
}

export async function getElectricalNearby(lat, lng, radius = 500, options = {}) {
    const url = `${API_BASE}/infrastructure/electrical/nearby?lat=${lat}&lng=${lng}&radius_m=${radius}`;
    const cached = getCached(url);
    if (cached) return cached;
    try {
        const data = await apiFetch(url, options);
        setCache(url, data);
        return data;
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { type: 'FeatureCollection', features: [] };
    }
}

export async function checkElectricalCapacity(params) {
    return apiFetch(`${API_BASE}/infrastructure/electrical/capacity-check`, {
        method: 'POST',
        body: JSON.stringify(params),
    });
}

export async function getSewersBbox(bounds, pipeType = null, options = {}) {
    try {
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        let url = `${API_BASE}/infrastructure/sewers/bbox?min_lng=${sw.lng}&min_lat=${sw.lat}&max_lng=${ne.lng}&max_lat=${ne.lat}`;
        if (pipeType) url += `&pipe_type=${pipeType}`;
        return await apiFetch(url, options);
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { type: 'FeatureCollection', features: [] };
    }
}

export async function getElectricalBbox(bounds, options = {}) {
    try {
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        const url = `${API_BASE}/infrastructure/electrical/bbox?min_lng=${sw.lng}&min_lat=${sw.lat}&max_lng=${ne.lng}&max_lat=${ne.lat}`;
        return await apiFetch(url, options);
    } catch (error) {
        if (isAbortError(error)) throw error;
        return { type: 'FeatureCollection', features: [] };
    }
}

// ─── Projects ───

export async function listProjects() {
    return apiFetch(`${API_BASE}/projects`);
}

export async function createProject(name, description = null) {
    return apiFetch(`${API_BASE}/projects`, {
        method: 'POST',
        body: JSON.stringify({ name, description }),
    });
}

export async function getProject(projectId) {
    return apiFetch(`${API_BASE}/projects/${projectId}`);
}

export async function updateProject(projectId, updates) {
    return apiFetch(`${API_BASE}/projects/${projectId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
    });
}

export async function deleteProject(projectId) {
    return apiFetch(`${API_BASE}/projects/${projectId}`, { method: 'DELETE' });
}

// Project parcels
export async function addParcelToProject(projectId, parcelId, role = 'primary') {
    return apiFetch(`${API_BASE}/projects/${projectId}/parcels`, {
        method: 'POST',
        body: JSON.stringify({ parcel_id: parcelId, role }),
    });
}

export async function removeParcelFromProject(projectId, parcelId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/parcels/${parcelId}`, { method: 'DELETE' });
}

// Project plans
export async function getProjectPlans(projectId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/plans`);
}

// Project notes
export async function getProjectNotes(projectId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/notes`);
}

export async function createProjectNote(projectId, content) {
    return apiFetch(`${API_BASE}/projects/${projectId}/notes`, {
        method: 'POST',
        body: JSON.stringify({ content }),
    });
}

export async function updateProjectNote(projectId, noteId, updates) {
    return apiFetch(`${API_BASE}/projects/${projectId}/notes/${noteId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
    });
}

export async function deleteProjectNote(projectId, noteId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/notes/${noteId}`, { method: 'DELETE' });
}

// Project conversations
export async function getProjectConversations(projectId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/conversations`);
}

export async function getProjectConversation(projectId, convId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/conversations/${convId}`);
}

export async function saveProjectConversation(projectId, { title, messages }) {
    return apiFetch(`${API_BASE}/projects/${projectId}/conversations`, {
        method: 'POST',
        body: JSON.stringify({ title, messages }),
    });
}

export async function updateProjectConversation(projectId, convId, updates) {
    return apiFetch(`${API_BASE}/projects/${projectId}/conversations/${convId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
    });
}

export async function deleteProjectConversation(projectId, convId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/conversations/${convId}`, { method: 'DELETE' });
}

// Project uploads
export async function getProjectUploads(projectId) {
    return apiFetch(`${API_BASE}/projects/${projectId}/uploads`);
}

export async function uploadProjectFile(projectId, file) {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/projects/${projectId}/uploads`, {
        method: 'POST',
        headers,
        body: formData,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const error = new Error(getErrorMessage(data, res.status));
        error.status = res.status;
        throw error;
    }
    return data;
}

// Project map state
export async function saveProjectMapState(projectId, mapState) {
    return apiFetch(`${API_BASE}/projects/${projectId}/map-state`, {
        method: 'PATCH',
        body: JSON.stringify(mapState),
    });
}

// ─── Design Version Control ───

export async function createBranch(projectId, name, fromVersionId = null) {
    return apiFetch(`${API_BASE}/designs/${projectId}/branches`, {
        method: 'POST',
        body: JSON.stringify({ name, from_version_id: fromVersionId }),
    });
}

export async function listBranches(projectId) {
    try {
        return await apiFetch(`${API_BASE}/designs/${projectId}/branches`);
    } catch {
        return [];
    }
}

export async function commitVersion(branchId, { floorPlans, modelParams, message, parcelId }) {
    return apiFetch(`${API_BASE}/designs/branches/${branchId}/commit`, {
        method: 'POST',
        body: JSON.stringify({
            floor_plans: floorPlans,
            model_params: modelParams,
            message,
            parcel_id: parcelId,
        }),
    });
}

export async function listVersions(branchId) {
    try {
        return await apiFetch(`${API_BASE}/designs/branches/${branchId}/versions`);
    } catch {
        return [];
    }
}

export async function getVersion(versionId) {
    return apiFetch(`${API_BASE}/designs/versions/${versionId}`);
}

export async function getLatestVersion(branchId) {
    try {
        return await apiFetch(`${API_BASE}/designs/branches/${branchId}/latest`);
    } catch {
        return null;
    }
}
