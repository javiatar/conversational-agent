import json
from logging import getLogger
from typing import List

from pydantic import BaseModel
from pyserini.search.lucene import LuceneSearcher

from conversational_agent.config.dependencies.rag import get_rag_config

logger = getLogger(__name__)


class Document(BaseModel):
    id: str = ""
    title: str = ""
    contents: str
    score: float


class RAGService:
    def __init__(self, include_dense: bool = False) -> None:
        rag_config = get_rag_config()
        idx_path = rag_config.index_path
        self.enabled = rag_config.enabled
        self.sparse_searcher: LuceneSearcher = LuceneSearcher(str(idx_path))
        if include_dense:
            raise NotImplementedError("Dense search not implemented yet")

    def search(self, query: str, k: int = 3) -> list[Document]:
        try:
            hits = self.sparse_searcher.search(query, k)
            return self.convert_lucene_hits_to_documents(hits)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def format_context(self, docs: List[Document]) -> str:
        return "\n\n".join([f"- {d.contents}" for d in docs])

    # SAD: lack of typing for LuceneSearcher means we have to do this conversion ourselves
    def convert_lucene_hits_to_documents(self, hits: list) -> list[Document]:
        documents: list[Document] = []
        for hit in hits:
            doc_id = hit.docid
            score = hit.score
            if (raw := hit.lucene_document.get("raw")) is None:
                logger.warning(f"Document {doc_id} has no 'raw' field. Skipping...")
                continue
            parsed_raw: dict[str, str] = json.loads(raw)
            title = parsed_raw.get("title", "")
            if (contents := parsed_raw.get("contents")) is None:
                logger.warning(f"Document {doc_id} has no 'contents' field in 'raw'. Skipping...")
                continue
            documents.append(Document(id=doc_id, title=title, contents=contents, score=score))

        return documents
