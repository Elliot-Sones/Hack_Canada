import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.geospatial import ProjectParcel
from app.models.plan import DevelopmentPlan
from app.models.tenant import Project, ProjectConversation, ProjectNote
from app.models.upload import UploadedDocument
from app.schemas.tenant import (
    AddParcelRequest,
    ConversationCreate,
    ConversationResponse,
    ConversationSummary,
    ConversationUpdate,
    MapStateUpdate,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.access_control import get_project_for_org

router = APIRouter()


# ─── Helpers ───

async def _project_with_counts(db: AsyncSession, project: Project) -> dict:
    """Build ProjectResponse dict with relationship counts."""
    pid = project.id
    counts = await db.execute(
        select(
            select(func.count()).where(ProjectParcel.project_id == pid).correlate(None).scalar_subquery().label("parcel_count"),
            select(func.count()).where(DevelopmentPlan.project_id == pid).correlate(None).scalar_subquery().label("plan_count"),
            select(func.count()).where(ProjectNote.project_id == pid).correlate(None).scalar_subquery().label("note_count"),
            select(func.count()).where(ProjectConversation.project_id == pid).correlate(None).scalar_subquery().label("conversation_count"),
            select(func.count()).where(UploadedDocument.project_id == pid).correlate(None).scalar_subquery().label("upload_count"),
        )
    )
    row = counts.one()
    return {
        "id": project.id,
        "organization_id": project.organization_id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "map_state": project.map_state,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "parcel_count": row.parcel_count,
        "plan_count": row.plan_count,
        "note_count": row.note_count,
        "conversation_count": row.conversation_count,
        "upload_count": row.upload_count,
    }


# ─── Project CRUD ───

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    project = Project(
        name=body.name,
        description=body.description,
        organization_id=user["organization_id"],
        created_by=user["id"],
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return await _project_with_counts(db, project)


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.organization_id == user["organization_id"]).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [await _project_with_counts(db, p) for p in projects]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    project = await get_project_for_org(db, project_id, user["organization_id"])
    return await _project_with_counts(db, project)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    project = await get_project_for_org(db, project_id, user["organization_id"])
    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    await db.flush()
    await db.refresh(project)
    return await _project_with_counts(db, project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    project = await get_project_for_org(db, project_id, user["organization_id"])
    await db.delete(project)
    await db.flush()


# ─── Parcels ───

@router.post("/projects/{project_id}/parcels", status_code=status.HTTP_201_CREATED)
async def add_parcel_to_project(
    project_id: uuid.UUID,
    body: AddParcelRequest,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    existing = await db.execute(
        select(ProjectParcel).where(ProjectParcel.project_id == project_id, ProjectParcel.parcel_id == body.parcel_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Parcel already linked to project")
    link = ProjectParcel(project_id=project_id, parcel_id=body.parcel_id, role=body.role)
    db.add(link)
    await db.flush()
    return {"status": "added", "project_id": str(project_id), "parcel_id": str(body.parcel_id)}


@router.delete("/projects/{project_id}/parcels/{parcel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_parcel_from_project(
    project_id: uuid.UUID,
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectParcel).where(ProjectParcel.project_id == project_id, ProjectParcel.parcel_id == parcel_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Parcel not linked to project")
    await db.delete(link)


# ─── Notes ───

@router.post("/projects/{project_id}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    project_id: uuid.UUID,
    body: NoteCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    note = ProjectNote(
        project_id=project_id,
        created_by=user["id"],
        content=body.content,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)
    return note


@router.get("/projects/{project_id}/notes", response_model=list[NoteResponse])
async def list_notes(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectNote)
        .where(ProjectNote.project_id == project_id)
        .order_by(ProjectNote.pinned.desc(), ProjectNote.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/projects/{project_id}/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    project_id: uuid.UUID,
    note_id: uuid.UUID,
    body: NoteUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectNote).where(ProjectNote.id == note_id, ProjectNote.project_id == project_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if body.content is not None:
        note.content = body.content
    if body.pinned is not None:
        note.pinned = body.pinned
    await db.flush()
    await db.refresh(note)
    return note


@router.delete("/projects/{project_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    project_id: uuid.UUID,
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectNote).where(ProjectNote.id == note_id, ProjectNote.project_id == project_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)


# ─── Conversations ───

@router.post("/projects/{project_id}/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    project_id: uuid.UUID,
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    title = body.title or "New conversation"
    # Auto-derive title from first user message
    if body.title is None and body.messages:
        first_user = next((m for m in body.messages if m.get("role") == "user"), None)
        if first_user and first_user.get("text"):
            text = first_user["text"]
            title = text[:57] + "..." if len(text) > 60 else text
    conv = ProjectConversation(
        project_id=project_id,
        created_by=user["id"],
        title=title,
        messages=body.messages,
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


@router.get("/projects/{project_id}/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectConversation)
        .where(ProjectConversation.project_id == project_id)
        .order_by(ProjectConversation.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/projects/{project_id}/conversations/{conv_id}", response_model=ConversationResponse)
async def get_conversation(
    project_id: uuid.UUID,
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectConversation).where(
            ProjectConversation.id == conv_id, ProjectConversation.project_id == project_id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.put("/projects/{project_id}/conversations/{conv_id}", response_model=ConversationResponse)
async def update_conversation(
    project_id: uuid.UUID,
    conv_id: uuid.UUID,
    body: ConversationUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectConversation).where(
            ProjectConversation.id == conv_id, ProjectConversation.project_id == project_id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if body.title is not None:
        conv.title = body.title
    if body.messages is not None:
        conv.messages = body.messages
    await db.flush()
    await db.refresh(conv)
    return conv


@router.delete("/projects/{project_id}/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    project_id: uuid.UUID,
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(ProjectConversation).where(
            ProjectConversation.id == conv_id, ProjectConversation.project_id == project_id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)


# ─── Plans ───

@router.get("/projects/{project_id}/plans")
async def list_project_plans(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(DevelopmentPlan)
        .where(DevelopmentPlan.project_id == project_id)
        .order_by(DevelopmentPlan.created_at.desc())
    )
    plans = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "original_query": p.original_query,
            "status": p.status,
            "current_step": p.current_step,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        }
        for p in plans
    ]


# ─── Uploads ───

@router.get("/projects/{project_id}/uploads")
async def list_project_uploads(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    await get_project_for_org(db, project_id, user["organization_id"])
    result = await db.execute(
        select(UploadedDocument)
        .where(UploadedDocument.project_id == project_id)
        .order_by(UploadedDocument.created_at.desc())
    )
    uploads = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "original_filename": u.original_filename,
            "content_type": u.content_type,
            "file_size_bytes": u.file_size_bytes,
            "status": u.status,
            "doc_category": u.doc_category,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in uploads
    ]


@router.post("/projects/{project_id}/uploads", status_code=status.HTTP_201_CREATED)
async def upload_to_project(
    project_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    """Upload a file and link it to a project."""
    await get_project_for_org(db, project_id, user["organization_id"])

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    from app.services.document_processor import compute_file_hash, get_file_category

    file_hash = compute_file_hash(file_bytes)
    filename = file.filename or "unknown"
    content_type = file.content_type or "application/octet-stream"

    doc = UploadedDocument(
        organization_id=user["organization_id"],
        uploaded_by=user["id"],
        project_id=project_id,
        original_filename=filename,
        content_type=content_type,
        file_size_bytes=len(file_bytes),
        object_key=f"projects/{project_id}/{uuid.uuid4()}/{filename}",
        file_hash=file_hash,
        doc_category=get_file_category(filename, content_type),
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return {
        "id": str(doc.id),
        "original_filename": doc.original_filename,
        "status": doc.status,
    }


# ─── Map State ───

@router.patch("/projects/{project_id}/map-state", response_model=ProjectResponse)
async def save_map_state(
    project_id: uuid.UUID,
    body: MapStateUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(get_current_user),
):
    project = await get_project_for_org(db, project_id, user["organization_id"])
    state = project.map_state or {}
    if body.center is not None:
        state["center"] = body.center
    if body.zoom is not None:
        state["zoom"] = body.zoom
    if body.selected_parcel_ids is not None:
        state["selected_parcel_ids"] = [str(pid) for pid in body.selected_parcel_ids]
    if body.infra_layers is not None:
        state["infra_layers"] = body.infra_layers
    project.map_state = state
    await db.flush()
    await db.refresh(project)
    return await _project_with_counts(db, project)
