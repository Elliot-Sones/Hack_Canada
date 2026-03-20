import { useState, useEffect, useCallback, useRef } from 'react';
import {
    listProjects,
    createProject,
    getProject,
    updateProject,
    deleteProject,
    addParcelToProject,
    removeParcelFromProject,
    getProjectPlans,
    getProjectNotes,
    createProjectNote,
    updateProjectNote,
    deleteProjectNote,
    getProjectConversations,
    getProjectConversation,
    deleteProjectConversation,
    getProjectUploads,
    uploadProjectFile,
    saveProjectMapState,
} from '../api.js';
import { isResolvedParcel } from '../lib/parcelState.js';

// ─── Helpers ───

function formatDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatFileSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS_COLORS = {
    active: '#4ade80',
    completed: '#60a5fa',
    archived: '#94a3b8',
    draft: '#fbbf24',
};

// ─── Project List View ───

function ProjectListView({ projects, loading, onOpenProject, onCreateNew }) {
    return (
        <div className="projects-list">
            <div className="projects-list-header">
                <h3>Your Projects</h3>
                <button className="projects-create-btn" onClick={onCreateNew}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                        <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    New Project
                </button>
            </div>
            {loading ? (
                <div className="projects-loading">Loading projects...</div>
            ) : projects.length === 0 ? (
                <div className="projects-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="32" height="32">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                    </svg>
                    <p>No projects yet. Create one to start organizing your work.</p>
                </div>
            ) : (
                <div className="projects-grid">
                    {projects.map((p) => (
                        <button key={p.id} className="project-card" onClick={() => onOpenProject(p.id)}>
                            <div className="project-card-header">
                                <span className="project-card-name">{p.name}</span>
                                <span className="project-card-status" style={{ color: STATUS_COLORS[p.status] || '#94a3b8' }}>
                                    {p.status}
                                </span>
                            </div>
                            {p.description && <p className="project-card-desc">{p.description}</p>}
                            <div className="project-card-counts">
                                {p.parcel_count > 0 && <span>{p.parcel_count} parcels</span>}
                                {p.plan_count > 0 && <span>{p.plan_count} plans</span>}
                                {p.note_count > 0 && <span>{p.note_count} notes</span>}
                                {p.upload_count > 0 && <span>{p.upload_count} files</span>}
                                {p.conversation_count > 0 && <span>{p.conversation_count} chats</span>}
                            </div>
                            <div className="project-card-date">{formatDate(p.created_at)}</div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

// ─── Create Form ───

function CreateProjectForm({ onCreated, onCancel }) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [saving, setSaving] = useState(false);
    const inputRef = useRef(null);

    useEffect(() => { inputRef.current?.focus(); }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!name.trim()) return;
        setSaving(true);
        try {
            const project = await createProject(name.trim(), description.trim() || null);
            onCreated(project);
        } catch (err) {
            console.error('Failed to create project:', err);
        } finally {
            setSaving(false);
        }
    };

    return (
        <form className="project-create-form" onSubmit={handleSubmit}>
            <h3>New Project</h3>
            <label>
                Name
                <input ref={inputRef} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. 100 King St W Redevelopment" maxLength={255} required />
            </label>
            <label>
                Description
                <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description..." rows={3} />
            </label>
            <div className="project-create-actions">
                <button type="button" className="project-cancel-btn" onClick={onCancel}>Cancel</button>
                <button type="submit" className="project-save-btn" disabled={saving || !name.trim()}>
                    {saving ? 'Creating...' : 'Create Project'}
                </button>
            </div>
        </form>
    );
}

// ─── Detail Tabs ───

const TABS = [
    { id: 'overview', label: 'Overview' },
    { id: 'parcels', label: 'Parcels' },
    { id: 'plans', label: 'Plans' },
    { id: 'files', label: 'Files' },
    { id: 'notes', label: 'Notes' },
    { id: 'chat', label: 'Chat' },
];

function OverviewTab({ project, onUpdate }) {
    const [editing, setEditing] = useState(false);
    const [name, setName] = useState(project.name);
    const [description, setDescription] = useState(project.description || '');

    useEffect(() => {
        setName(project.name);
        setDescription(project.description || '');
    }, [project]);

    const handleSave = async () => {
        await onUpdate({ name: name.trim(), description: description.trim() || null });
        setEditing(false);
    };

    return (
        <div className="project-tab-content">
            {editing ? (
                <div className="project-edit-form">
                    <label>Name<input value={name} onChange={(e) => setName(e.target.value)} /></label>
                    <label>Description<textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} /></label>
                    <div className="project-edit-actions">
                        <button onClick={() => setEditing(false)}>Cancel</button>
                        <button className="project-save-btn" onClick={handleSave}>Save</button>
                    </div>
                </div>
            ) : (
                <>
                    <div className="project-overview-field">
                        <span className="field-label">Name</span>
                        <span className="field-value">{project.name}</span>
                    </div>
                    <div className="project-overview-field">
                        <span className="field-label">Description</span>
                        <span className="field-value">{project.description || 'No description'}</span>
                    </div>
                    <div className="project-overview-field">
                        <span className="field-label">Status</span>
                        <span className="field-value" style={{ color: STATUS_COLORS[project.status] }}>{project.status}</span>
                    </div>
                    <div className="project-overview-field">
                        <span className="field-label">Created</span>
                        <span className="field-value">{formatDate(project.created_at)}</span>
                    </div>
                    <button className="project-edit-btn" onClick={() => setEditing(true)}>Edit Details</button>
                </>
            )}
        </div>
    );
}

function ParcelsTab({ projectId, selectedParcels }) {
    const [parcels, setParcels] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadParcels = useCallback(async () => {
        setLoading(true);
        try {
            const proj = await getProject(projectId);
            // The project response doesn't include parcels list — but we get parcel_count.
            // For now, store locally what we add.
            setParcels((prev) => prev);
        } catch { /* ignore */ }
        setLoading(false);
    }, [projectId]);

    useEffect(() => { loadParcels(); }, [loadParcels]);

    const handleAddCurrent = async () => {
        const primary = selectedParcels?.[selectedParcels.length - 1];
        if (!primary || !isResolvedParcel(primary)) return;
        try {
            await addParcelToProject(projectId, primary.id);
            setParcels((prev) => [...prev, { id: primary.id, address: primary.address }]);
        } catch (err) {
            if (err.status === 409) return; // already linked
            console.error('Failed to add parcel:', err);
        }
    };

    const handleRemove = async (parcelId) => {
        try {
            await removeParcelFromProject(projectId, parcelId);
            setParcels((prev) => prev.filter((p) => p.id !== parcelId));
        } catch (err) {
            console.error('Failed to remove parcel:', err);
        }
    };

    const currentParcel = selectedParcels?.[selectedParcels.length - 1];
    const canAdd = currentParcel && isResolvedParcel(currentParcel) && !parcels.some((p) => p.id === currentParcel.id);

    return (
        <div className="project-tab-content">
            {canAdd && (
                <button className="project-add-parcel-btn" onClick={handleAddCurrent}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                        <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Add Current Parcel
                </button>
            )}
            {parcels.length === 0 ? (
                <div className="project-tab-empty">No parcels linked. Select a parcel on the map and click "Add Current Parcel".</div>
            ) : (
                <div className="project-parcel-list">
                    {parcels.map((p) => (
                        <div key={p.id} className="project-parcel-item">
                            <span>{p.address || p.id}</span>
                            <button className="project-remove-btn" onClick={() => handleRemove(p.id)} title="Remove">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function PlansTab({ projectId }) {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getProjectPlans(projectId).then(setPlans).catch(() => setPlans([])).finally(() => setLoading(false));
    }, [projectId]);

    if (loading) return <div className="project-tab-content"><div className="projects-loading">Loading plans...</div></div>;

    return (
        <div className="project-tab-content">
            {plans.length === 0 ? (
                <div className="project-tab-empty">No plans linked to this project yet. Generate a plan from the chat to see it here.</div>
            ) : (
                <div className="project-plan-list">
                    {plans.map((p) => (
                        <div key={p.id} className="project-plan-item">
                            <div className="plan-item-header">
                                <span className="plan-item-query">{p.original_query?.slice(0, 80) || 'Plan'}</span>
                                <span className={`plan-item-status status-${p.status}`}>{p.status}</span>
                            </div>
                            <span className="plan-item-date">{formatDate(p.created_at)}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function FilesTab({ projectId }) {
    const [uploads, setUploads] = useState([]);
    const [loading, setLoading] = useState(true);
    const fileInputRef = useRef(null);

    useEffect(() => {
        getProjectUploads(projectId).then(setUploads).catch(() => setUploads([])).finally(() => setLoading(false));
    }, [projectId]);

    const handleUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
            const result = await uploadProjectFile(projectId, file);
            setUploads((prev) => [{ ...result, original_filename: file.name, file_size_bytes: file.size, content_type: file.type, created_at: new Date().toISOString() }, ...prev]);
        } catch (err) {
            console.error('Upload failed:', err);
        }
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const FILE_ICONS = {
        'application/pdf': 'PDF',
        'image/': 'IMG',
        'text/': 'TXT',
        'application/': 'DOC',
    };

    function fileIcon(contentType) {
        for (const [prefix, label] of Object.entries(FILE_ICONS)) {
            if (contentType?.startsWith(prefix)) return label;
        }
        return 'FILE';
    }

    if (loading) return <div className="project-tab-content"><div className="projects-loading">Loading files...</div></div>;

    return (
        <div className="project-tab-content">
            <input ref={fileInputRef} type="file" hidden onChange={handleUpload} />
            <button className="project-upload-btn" onClick={() => fileInputRef.current?.click()}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                Upload File
            </button>
            {uploads.length === 0 ? (
                <div className="project-tab-empty">No files uploaded yet.</div>
            ) : (
                <div className="project-file-list">
                    {uploads.map((u) => (
                        <div key={u.id} className="project-file-item">
                            <span className="file-icon">{fileIcon(u.content_type)}</span>
                            <div className="file-info">
                                <span className="file-name">{u.original_filename}</span>
                                <span className="file-meta">{formatFileSize(u.file_size_bytes)} &middot; {formatDate(u.created_at)}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function NotesTab({ projectId }) {
    const [notes, setNotes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newNote, setNewNote] = useState('');
    const [saving, setSaving] = useState(false);

    const loadNotes = useCallback(async () => {
        setLoading(true);
        try { setNotes(await getProjectNotes(projectId)); } catch { setNotes([]); }
        setLoading(false);
    }, [projectId]);

    useEffect(() => { loadNotes(); }, [loadNotes]);

    const handleAdd = async () => {
        if (!newNote.trim() || saving) return;
        setSaving(true);
        try {
            const note = await createProjectNote(projectId, newNote.trim());
            setNotes((prev) => [note, ...prev]);
            setNewNote('');
        } catch (err) {
            console.error('Failed to create note:', err);
        }
        setSaving(false);
    };

    const handlePin = async (note) => {
        try {
            const updated = await updateProjectNote(projectId, note.id, { pinned: !note.pinned });
            setNotes((prev) => prev.map((n) => n.id === note.id ? updated : n).sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0)));
        } catch (err) {
            console.error('Failed to update note:', err);
        }
    };

    const handleDelete = async (noteId) => {
        try {
            await deleteProjectNote(projectId, noteId);
            setNotes((prev) => prev.filter((n) => n.id !== noteId));
        } catch (err) {
            console.error('Failed to delete note:', err);
        }
    };

    if (loading) return <div className="project-tab-content"><div className="projects-loading">Loading notes...</div></div>;

    return (
        <div className="project-tab-content">
            <div className="project-note-input">
                <textarea value={newNote} onChange={(e) => setNewNote(e.target.value)} placeholder="Add a note..." rows={2} />
                <button className="project-save-btn" onClick={handleAdd} disabled={!newNote.trim() || saving}>Add</button>
            </div>
            {notes.length === 0 ? (
                <div className="project-tab-empty">No notes yet.</div>
            ) : (
                <div className="project-note-list">
                    {notes.map((n) => (
                        <div key={n.id} className={`project-note-card${n.pinned ? ' pinned' : ''}`}>
                            <div className="note-card-content">{n.content}</div>
                            <div className="note-card-footer">
                                <span className="note-card-date">{formatDate(n.created_at)}</span>
                                <div className="note-card-actions">
                                    <button onClick={() => handlePin(n)} title={n.pinned ? 'Unpin' : 'Pin'}>
                                        <svg viewBox="0 0 24 24" fill={n.pinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" width="12" height="12">
                                            <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" />
                                        </svg>
                                    </button>
                                    <button onClick={() => handleDelete(n.id)} title="Delete">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                                            <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function ChatTab({ projectId }) {
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedConv, setSelectedConv] = useState(null);
    const [loadingConv, setLoadingConv] = useState(false);

    useEffect(() => {
        getProjectConversations(projectId).then(setConversations).catch(() => setConversations([])).finally(() => setLoading(false));
    }, [projectId]);

    const handleOpen = async (convId) => {
        setLoadingConv(true);
        try {
            const conv = await getProjectConversation(projectId, convId);
            setSelectedConv(conv);
        } catch (err) {
            console.error('Failed to load conversation:', err);
        }
        setLoadingConv(false);
    };

    const handleDelete = async (convId) => {
        try {
            await deleteProjectConversation(projectId, convId);
            setConversations((prev) => prev.filter((c) => c.id !== convId));
            if (selectedConv?.id === convId) setSelectedConv(null);
        } catch (err) {
            console.error('Failed to delete conversation:', err);
        }
    };

    if (loading) return <div className="project-tab-content"><div className="projects-loading">Loading conversations...</div></div>;

    if (selectedConv) {
        return (
            <div className="project-tab-content">
                <button className="project-back-btn" onClick={() => setSelectedConv(null)}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14"><polyline points="15 18 9 12 15 6" /></svg>
                    Back to list
                </button>
                <h4 className="conv-detail-title">{selectedConv.title}</h4>
                <div className="conv-messages">
                    {selectedConv.messages?.map((m, i) => (
                        <div key={i} className={`conv-message conv-message-${m.role}`}>
                            <span className="conv-role">{m.role === 'user' ? 'You' : 'Assistant'}</span>
                            <p>{m.text}</p>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="project-tab-content">
            {conversations.length === 0 ? (
                <div className="project-tab-empty">No saved conversations. Chat messages sent while this project is open will be saved here.</div>
            ) : (
                <div className="project-conv-list">
                    {conversations.map((c) => (
                        <div key={c.id} className="project-conv-item">
                            <button className="conv-item-main" onClick={() => handleOpen(c.id)}>
                                <span className="conv-item-title">{c.title}</span>
                                <span className="conv-item-date">{formatDate(c.updated_at)}</span>
                            </button>
                            <button className="project-remove-btn" onClick={() => handleDelete(c.id)} title="Delete">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            )}
            {loadingConv && <div className="projects-loading">Loading conversation...</div>}
        </div>
    );
}

// ─── Detail View ───

function ProjectDetailView({ projectId, onBack, selectedParcels }) {
    const [project, setProject] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        setLoading(true);
        getProject(projectId).then(setProject).catch(() => setProject(null)).finally(() => setLoading(false));
    }, [projectId]);

    const handleUpdate = async (updates) => {
        const updated = await updateProject(projectId, updates);
        setProject(updated);
    };

    const handleDelete = async () => {
        await deleteProject(projectId);
        onBack();
    };

    if (loading) return <div className="projects-loading">Loading project...</div>;
    if (!project) return <div className="project-tab-empty">Project not found.</div>;

    return (
        <div className="project-detail">
            <div className="project-detail-header">
                <button className="project-back-btn" onClick={onBack}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14"><polyline points="15 18 9 12 15 6" /></svg>
                    Projects
                </button>
                <h3 className="project-detail-name">{project.name}</h3>
                <button className="project-delete-btn" onClick={handleDelete} title="Delete project">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                        <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                </button>
            </div>
            <div className="project-tabs">
                {TABS.map((t) => (
                    <button key={t.id} className={`project-tab${activeTab === t.id ? ' active' : ''}`} onClick={() => setActiveTab(t.id)}>
                        {t.label}
                    </button>
                ))}
            </div>
            <div className="project-tab-body">
                {activeTab === 'overview' && <OverviewTab project={project} onUpdate={handleUpdate} />}
                {activeTab === 'parcels' && <ParcelsTab projectId={projectId} selectedParcels={selectedParcels} />}
                {activeTab === 'plans' && <PlansTab projectId={projectId} />}
                {activeTab === 'files' && <FilesTab projectId={projectId} />}
                {activeTab === 'notes' && <NotesTab projectId={projectId} />}
                {activeTab === 'chat' && <ChatTab projectId={projectId} />}
            </div>
        </div>
    );
}

// ─── Main ───

export default function ProjectsPanel({ selectedParcels, onProjectOpen, onProjectClose, activeProjectId }) {
    const [view, setView] = useState(activeProjectId ? 'detail' : 'list');
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [openProjectId, setOpenProjectId] = useState(activeProjectId || null);

    const loadProjects = useCallback(async () => {
        setLoading(true);
        try { setProjects(await listProjects()); } catch { setProjects([]); }
        setLoading(false);
    }, []);

    useEffect(() => { loadProjects(); }, [loadProjects]);

    const handleOpenProject = async (id) => {
        setOpenProjectId(id);
        setView('detail');
        // Notify parent with project name
        try {
            const proj = await getProject(id);
            onProjectOpen?.(id, proj.name);
        } catch {
            onProjectOpen?.(id, 'Project');
        }
    };

    const handleCreated = (project) => {
        setProjects((prev) => [project, ...prev]);
        setOpenProjectId(project.id);
        setView('detail');
        onProjectOpen?.(project.id, project.name);
    };

    const handleBackToList = () => {
        setView('list');
        setOpenProjectId(null);
        onProjectClose?.();
        loadProjects(); // refresh counts
    };

    if (view === 'create') {
        return <CreateProjectForm onCreated={handleCreated} onCancel={() => setView('list')} />;
    }

    if (view === 'detail' && openProjectId) {
        return <ProjectDetailView projectId={openProjectId} onBack={handleBackToList} selectedParcels={selectedParcels} />;
    }

    return <ProjectListView projects={projects} loading={loading} onOpenProject={handleOpenProject} onCreateNew={() => setView('create')} />;
}
