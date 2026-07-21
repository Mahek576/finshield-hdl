from src.llm.rag_retriever import (
    LocalRAGRetriever,
    chunk_text,
    default_policy_retriever,
    discover_text_files,
    load_document_chunks,
)


def test_chunk_text_creates_chunks():
    text = "First paragraph about fraud policy.\n\nSecond paragraph about blocked transactions."
    chunks = chunk_text(text=text, source_path="policy.md", max_chars=120, overlap_chars=10)

    assert len(chunks) >= 1
    assert chunks[0].source_path == "policy.md"
    assert "fraud policy" in chunks[0].text


def test_discover_text_files_finds_markdown(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "risk_policy.md").write_text("Risk policy content", encoding="utf-8")
    (docs / "ignore.csv").write_text("not supported", encoding="utf-8")

    files = discover_text_files([docs])

    assert len(files) == 1
    assert files[0].name == "risk_policy.md"


def test_local_rag_retriever_returns_relevant_result(tmp_path):
    policy = tmp_path / "risk_policy.md"
    playbook = tmp_path / "fraud_playbook.md"

    policy.write_text(
        "BLOCK means a transaction risk is high and should be stopped immediately.",
        encoding="utf-8",
    )
    playbook.write_text(
        "Analysts should investigate account takeover indicators and suspicious login behavior.",
        encoding="utf-8",
    )

    retriever = LocalRAGRetriever.from_paths([policy, playbook])
    results = retriever.query("What does BLOCK mean?", top_k=1)

    assert len(results) == 1
    assert "BLOCK means" in results[0].chunk.text


def test_build_context_includes_source(tmp_path):
    policy = tmp_path / "risk_policy.md"
    policy.write_text(
        "REVIEW means the transaction needs step-up authentication or analyst review.",
        encoding="utf-8",
    )

    retriever = LocalRAGRetriever.from_paths([policy])
    context = retriever.build_context("What does REVIEW mean?", top_k=1)

    assert "Source:" in context
    assert "risk_policy.md" in context
    assert "REVIEW" in context


def test_load_document_chunks_reads_docs(tmp_path):
    doc = tmp_path / "audit_policy.md"
    doc.write_text("Audit records preserve evidence and decision reasons.", encoding="utf-8")

    chunks = load_document_chunks([doc])

    assert len(chunks) == 1
    assert "Audit records" in chunks[0].text


def test_default_policy_retriever_loads_project_docs():
    retriever = default_policy_retriever("docs")
    results = retriever.query("What can the analyst assistant not do?", top_k=2)

    assert len(results) >= 1
