# Knowledge — CoCivil Domain Content

This directory contains all domain knowledge used by CoCivil's AI systems. It is the single source directory for RAG ingestion into ChromaDB.

## Structure

```
knowledge/
  research-pipeline/      Ontario site-feasibility research skills (9 skills)
  document-templates/     Planning document generation templates (29 skills)
  water-policy/           Ontario water/sewer policy and regulations
  research/               Data plans, implementation specs, research docs
```

## How It's Used

1. **RAG ingestion**: `fine-tuned-RAG/ingest.py` walks this entire directory, extracts text from MD/PDF/JSON/PNG files, chunks them, and stores embeddings in ChromaDB.
2. **Runtime retrieval**: The app queries ChromaDB vectors at runtime — it does NOT read these files directly.
3. **AI agent skills**: The research pipeline and document template skills are loaded as context for AI agents performing site research or document generation.

## Not for Coding

This directory is for the **app's AI**, not for the coding agent. Coding conventions, project structure, and DB schema docs live in `.claude/`.
