import os

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")

_client = None
_embedder = DefaultEmbeddingFunction()


def get_collections():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:  # remove the old collection if an earlier index still has it
            _client.delete_collection("personal_history")
        except Exception:
            pass
    journal = _client.get_or_create_collection("journal", embedding_function=_embedder)
    knowledge = _client.get_or_create_collection("knowledge_base", embedding_function=_embedder)
    return journal, knowledge