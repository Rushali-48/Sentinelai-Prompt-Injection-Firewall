from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_PATH = PROJECT_ROOT / "data" / "sentinelai_dataset_metadata.csv"

VECTOR_DB_PATH = PROJECT_ROOT / "vector_db" / "chroma_db"

COLLECTION_NAME = "sentinelai_attack_knowledge"

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

TOP_K = 12

RERANK_TOP_K = 3

CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

LLM_MODEL_NAME = "openai/gpt-oss-120b"
