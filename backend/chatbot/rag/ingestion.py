import io
import os
import re
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import requests
from django.conf import settings

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - dépendance optionnelle
    PdfReader = None

try:
    import docx  # type: ignore
except Exception:  # pragma: no cover - dépendance optionnelle
    docx = None

try:
    import chromadb
except Exception:  # pragma: no cover - dépendance optionnelle
    chromadb = None


def extract_text(file: Any) -> str:
    """Extrait le texte brut d'un fichier PDF, DOCX ou TXT."""
    if file is None:
        return ""

    if isinstance(file, (str, os.PathLike)):
        path = Path(file)
        if not path.exists():
            return ""
        name = path.name.lower()
        with path.open("rb") as handle:
            data = handle.read()
    else:
        name = (getattr(file, "name", "") or "").lower()
        try:
            file.seek(0)
        except Exception:
            pass
        data = file.read()
        try:
            file.seek(0)
        except Exception:
            pass

    if not data:
        return ""

    if name.endswith(".txt"):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore")

    if name.endswith(".pdf"):
        if PdfReader is None:
            return ""
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(page for page in pages if page).strip()
        except Exception:
            return ""

    if name.endswith(".docx"):
        if docx is None:
            return ""
        try:
            document = docx.Document(io.BytesIO(data))
            paragraphs = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
            return "\n".join(paragraphs).strip()
        except Exception:
            return ""

    return ""


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> List[str]:
    """Découpe un texte en chunks de taille approximative avec chevauchement."""
    if not text:
        return []

    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    words = normalized.split()
    if len(words) <= chunk_size:
        return [normalized]

    step = max(1, chunk_size - overlap)
    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start += step
    return chunks


def get_embedding(text: str) -> List[float]:
    """Génère un embedding via l'API Gemini avec un format compatible."""
    print(f"[RAG] embedding start text_len={len(text or '')} model=gemini-embedding-001")
    api_key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Clé API Gemini absente. Définis GEMINI_API_KEY dans l'environnement.")

    candidates = [
        {
            "model": "gemini-embedding-001",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent",
        }
    ]

    request_text = (text or "")[:3000]
    last_error = None

    for candidate in candidates:
        payload = {
            "model": candidate["model"],
            "content": {"parts": [{"text": request_text}]},
            "outputDimensionality": 1536,
        }
        url = f"{candidate['endpoint']}?key={api_key}"
        try:
            response = requests.post(url, json=payload, timeout=20)
        except requests.RequestException as exc:
            last_error = str(exc)
            continue

        if response.status_code == 200:
            payload_json = response.json()
            values = payload_json.get("embedding", {}).get("values", [])
            if values:
                print(f"[RAG] embedding success dim={len(values)}")
                return values
            raise RuntimeError("L'API Gemini a répondu sans vecteur d'embedding.")

        last_error = f"{response.status_code} - {response.text[:200]}"
        if response.status_code == 404:
            continue
        break

    if last_error:
        raise RuntimeError(f"Échec embedding Gemini: {last_error}")
    raise RuntimeError("Échec embedding Gemini: aucune réponse valide reçue.")


def embed_and_store(chunks: List[str], metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Génère les embeddings et les stocke dans ChromaDB de manière persistante."""
    if not chunks:
        return []
    if chromadb is None:
        raise RuntimeError("La dépendance chromadb n'est pas installée.")

    if len(chunks) != len(metadata_list):
        raise ValueError("Le nombre de chunks et de métadonnées doit être identique.")

    print(f"[RAG] ingest start chunks={len(chunks)} document_id={metadata_list[0].get('document_id') if metadata_list else 'n/a'}")

    try:
        client = chromadb.PersistentClient(
    path=settings.CHROMA_DB_PATH
)
    except Exception as exc:
        raise RuntimeError(f"Impossible d'initialiser ChromaDB : {exc}") from exc

    collection = client.get_or_create_collection(
        name="course_documents",
        metadata={"hnsw:space": "cosine"},
    )

    documents: List[str] = []
    embeddings: List[List[float]] = []
    ids: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for index, (chunk_text_value, metadata) in enumerate(zip(chunks, metadata_list)):
        embedding = get_embedding(chunk_text_value)
        if not embedding:
            continue

        document_id = metadata.get("document_id") or "document"
        chunk_id = f"{document_id}-chunk-{index}"
        documents.append(chunk_text_value)
        embeddings.append(embedding)
        ids.append(chunk_id)
        metadatas.append({
            **metadata,
            "chunk_index": index,
            "text_preview": chunk_text_value[:160],
        })

    if not documents:
        return []

    try:
        collection.add(documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas)
    except Exception as exc:
        print(f"[RAG] ingest error {exc}")
        raise

    print(f"[RAG] ingest success stored={len(metadatas)}")
    return metadatas
