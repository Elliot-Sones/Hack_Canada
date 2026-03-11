"""
config.py - Shared configuration loaded from .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths relative to this file's directory (works regardless of working dir)
_rag_dir = Path(__file__).resolve().parent
load_dotenv(_rag_dir / ".env")
load_dotenv(_rag_dir.parent / ".env")
_docs_raw = os.getenv("DOCS_DIR", "../../SDG/Hack Canada")
DOCS_DIR = str((_rag_dir / _docs_raw).resolve())

# Additional document directories (comma-separated in .env)
# Each path resolved relative to the RAG directory
_extra_raw = os.getenv("EXTRA_DOCS_DIRS", "")
EXTRA_DOCS_DIRS = [
    str((_rag_dir / p.strip()).resolve())
    for p in _extra_raw.split(",") if p.strip()
]

# All document directories combined
ALL_DOCS_DIRS = [DOCS_DIR] + EXTRA_DOCS_DIRS

_chroma_raw = os.getenv("CHROMA_DIR", "./chroma_db")
CHROMA_DIR = str((_rag_dir / _chroma_raw).resolve())
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "hack_canada")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
