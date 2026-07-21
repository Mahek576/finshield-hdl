from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SUPPORTED_EXTENSIONS = {".md", ".txt"}


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    source_path: str
    text: str
    start_char: int
    end_char: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk
    score: float

    def to_dict(self) -> Dict[str, object]:
        data = self.chunk.to_dict()
        data["score"] = self.score
        return data


def _normalize_text(text: str) -> str:
    return " ".join(text.replace("\r\n", "\n").replace("\r", "\n").split())


def discover_text_files(paths: Sequence[str | Path]) -> List[Path]:
    files: List[Path] = []

    for raw_path in paths:
        path = Path(raw_path)

        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

        elif path.is_dir():
            files.extend(
                sorted(
                    item
                    for item in path.rglob("*")
                    if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS
                )
            )

    return sorted({file.resolve() for file in files})


def chunk_text(
    text: str,
    source_path: str,
    max_chars: int = 900,
    overlap_chars: int = 120,
) -> List[DocumentChunk]:
    if max_chars <= 100:
        raise ValueError("max_chars must be greater than 100.")

    if overlap_chars < 0:
        raise ValueError("overlap_chars cannot be negative.")

    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be smaller than max_chars.")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    if not normalized:
        return []

    paragraphs = [para.strip() for para in normalized.split("\n\n") if para.strip()]

    chunks: List[DocumentChunk] = []
    current = ""
    start_char = 0
    cursor = 0

    for paragraph in paragraphs:
        paragraph_start = normalized.find(paragraph, cursor)
        if paragraph_start == -1:
            paragraph_start = cursor

        candidate = paragraph if not current else f"{current}\n\n{paragraph}"

        if len(candidate) <= max_chars:
            if not current:
                start_char = paragraph_start
            current = candidate
        else:
            if current:
                end_char = start_char + len(current)
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{Path(source_path).name}:{len(chunks)}",
                        source_path=source_path,
                        text=current,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )

                overlap_text = current[-overlap_chars:] if overlap_chars else ""
                current = f"{overlap_text}\n\n{paragraph}".strip()
                start_char = max(0, paragraph_start - len(overlap_text))
            else:
                piece_start = paragraph_start
                paragraph_end = paragraph_start + len(paragraph)

                while piece_start < paragraph_end:
                    piece_end = min(piece_start + max_chars, paragraph_end)
                    piece = normalized[piece_start:piece_end]
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{Path(source_path).name}:{len(chunks)}",
                            source_path=source_path,
                            text=piece,
                            start_char=piece_start,
                            end_char=piece_end,
                        )
                    )

                    if piece_end >= paragraph_end:
                        break

                    piece_start = max(piece_end - overlap_chars, piece_end)

                current = ""

        cursor = paragraph_start + len(paragraph)

    if current:
        chunks.append(
            DocumentChunk(
                chunk_id=f"{Path(source_path).name}:{len(chunks)}",
                source_path=source_path,
                text=current,
                start_char=start_char,
                end_char=start_char + len(current),
            )
        )

    return chunks


def load_document_chunks(
    paths: Sequence[str | Path],
    max_chars: int = 900,
    overlap_chars: int = 120,
) -> List[DocumentChunk]:
    files = discover_text_files(paths)
    chunks: List[DocumentChunk] = []

    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        chunks.extend(
            chunk_text(
                text=text,
                source_path=str(file_path),
                max_chars=max_chars,
                overlap_chars=overlap_chars,
            )
        )

    return chunks


class LocalRAGRetriever:
    """
    Offline deterministic retrieval layer for FinShield policy documents.

    This uses TF-IDF similarity so local development and tests do not need
    external APIs or vector databases.
    """

    def __init__(self, chunks: Sequence[DocumentChunk]):
        self.chunks = list(chunks)

        if not self.chunks:
            raise ValueError("LocalRAGRetriever requires at least one document chunk.")

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )

        self.chunk_texts = [_normalize_text(chunk.text) for chunk in self.chunks]
        self.matrix = self.vectorizer.fit_transform(self.chunk_texts)

    @classmethod
    def from_paths(
        cls,
        paths: Sequence[str | Path],
        max_chars: int = 900,
        overlap_chars: int = 120,
    ) -> "LocalRAGRetriever":
        chunks = load_document_chunks(
            paths=paths,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )
        return cls(chunks)

    def query(
        self,
        question: str,
        top_k: int = 3,
        min_score: float = 0.0,
        source_filter: Optional[Iterable[str]] = None,
    ) -> List[RetrievalResult]:
        cleaned_question = _normalize_text(question)

        if not cleaned_question:
            return []

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_vector = self.vectorizer.transform([cleaned_question])
        scores = cosine_similarity(query_vector, self.matrix).reshape(-1)

        allowed_sources = None
        if source_filter is not None:
            allowed_sources = {str(Path(source).resolve()) for source in source_filter}

        ranked_indices = np.argsort(scores)[::-1]
        results: List[RetrievalResult] = []

        for index in ranked_indices:
            score = float(scores[index])
            chunk = self.chunks[int(index)]

            if score < min_score:
                continue

            if allowed_sources is not None and str(Path(chunk.source_path).resolve()) not in allowed_sources:
                continue

            results.append(RetrievalResult(chunk=chunk, score=score))

            if len(results) >= top_k:
                break

        return results

    def build_context(
        self,
        question: str,
        top_k: int = 3,
        max_context_chars: int = 2500,
    ) -> str:
        results = self.query(question=question, top_k=top_k)

        context_parts: List[str] = []
        current_length = 0

        for result in results:
            source_name = Path(result.chunk.source_path).name
            snippet = result.chunk.text.strip()
            section = f"[Source: {source_name} | Score: {result.score:.3f}]\n{snippet}"

            if current_length + len(section) > max_context_chars:
                break

            context_parts.append(section)
            current_length += len(section)

        return "\n\n---\n\n".join(context_parts)


def default_policy_retriever(docs_dir: str | Path = "docs") -> LocalRAGRetriever:
    preferred_docs = [
        Path(docs_dir) / "risk_policy.md",
        Path(docs_dir) / "fraud_playbook.md",
        Path(docs_dir) / "audit_policy.md",
        Path(docs_dir) / "cost_sensitive_decisioning.md",
        Path(docs_dir) / "model_calibration.md",
        Path(docs_dir) / "model_monitoring.md",
        Path(docs_dir) / "llm_rag_design.md",
        Path(docs_dir) / "llm_risk_controls.md",
    ]

    existing_docs = [path for path in preferred_docs if path.exists()]

    if not existing_docs:
        raise FileNotFoundError("No FinShield policy documents found for retrieval.")

    return LocalRAGRetriever.from_paths(existing_docs)
