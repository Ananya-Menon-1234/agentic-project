from pathlib import Path

from app.rag.store import get_collections

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def build_journal_docs():
    ids, docs, metas = [], [], []
    path = DATA_DIR / "journal" / "journal.txt"
    if not path.exists():
        return ids, docs, metas
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|", 2)]
        if len(parts) != 3:
            print(f"[ingest] skipping malformed journal line {n + 1}: {line[:60]}")
            continue
        date, domain, text = parts
        ids.append(f"journal-{date}-{n}")
        docs.append(f"Journal entry {date} ({domain}): {text}")
        metas.append({"date": date, "month": date[:7], "domain": domain})
    return ids, docs, metas


def build_knowledge_docs(max_chars: int = 600):
    ids, docs, metas = [], [], []
    for path in sorted((DATA_DIR / "knowledge").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunk, n = "", 0
        for p in paragraphs + [None]:  # None = sentinel to flush the last chunk
            if p is None or (chunk and len(chunk) + len(p) > max_chars):
                if chunk:
                    ids.append(f"{path.stem}-{n}")
                    docs.append(chunk)
                    metas.append({"source": path.name})
                    n += 1
                chunk = ""
            if p is not None:
                chunk = f"{chunk}\n\n{p}".strip()
    return ids, docs, metas


def ensure_indexed(force: bool = False):
    journal, knowledge = get_collections()
    if force or journal.count() == 0:
        ids, docs, metas = build_journal_docs()
        if ids:
            journal.upsert(ids=ids, documents=docs, metadatas=metas)
    if force or knowledge.count() == 0:
        ids, docs, metas = build_knowledge_docs()
        if ids:
            knowledge.upsert(ids=ids, documents=docs, metadatas=metas)
    return journal, knowledge


if __name__ == "__main__":
    j, k = ensure_indexed(force=True)
    print(f"journal: {j.count()} entries | knowledge_base: {k.count()} chunks")