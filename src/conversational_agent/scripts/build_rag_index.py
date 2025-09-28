import shutil
import subprocess

from pyserini.search.lucene import LuceneSearcher

from conversational_agent.config.dependencies.rag import get_rag_config
from conversational_agent.services.rag_service import RAGService


def build_sparse_index():
    """Build sparse index using Pyserini's LuceneIndexer directly"""
    rag_config = get_rag_config()
    idx_path = rag_config.index_path
    kb_path = rag_config.kb_path
    if idx_path.exists():
        # Remove existing index directory and its contents
        shutil.rmtree(idx_path)
    idx_path.mkdir(parents=True)

    if not kb_path.exists():
        print(f"Knowledge base file not found: {kb_path}")
        print("Run 'python src/conversational_agent/scripts/create_knowledge_base.py' first")
        return
    cmd = f"python -m pyserini.index.lucene \
  --collection JsonCollection \
  --input {kb_path.parent} \
  --index {idx_path} \
  --generator DefaultLuceneDocumentGenerator \
  --threads 1 \
  --storePositions --storeDocvectors --storeRaw"
    subprocess.run(cmd, shell=True)


def verify_index():
    """Verify the index was built correctly"""
    try:
        rag_config = get_rag_config()
        idx_path = rag_config.index_path
        searcher = LuceneSearcher(str(idx_path))
        hits = searcher.search("shipping times", k=3)
        for i, doc in enumerate(RAGService().convert_lucene_hits_to_documents(hits)):
            print(f"Hit {i + 1}:")
            print(f"  Doc ID: {doc.id}")
            print(f"  Score: {doc.score}")
            print(f"  Title: {doc.title}")
            print(f"  Contents: {doc.contents[:200]}...")  # Print first 200 characters
        assert len(hits) > 0, "No hits found, expected at least 1 for query = 'shipping times'"
    except Exception as e:
        print(f"Index verification failed: {e}")


if __name__ == "__main__":
    build_sparse_index()
    verify_index()
