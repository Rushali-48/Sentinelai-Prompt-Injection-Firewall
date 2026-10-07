from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from sentence_transformers import CrossEncoder

from .config import (
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    TOP_K,
    RERANK_TOP_K,
    CROSS_ENCODER_MODEL_NAME,
)


# load vectordb
def load_vector_database():

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vector_store = Chroma(
        persist_directory=str(VECTOR_DB_PATH),
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    return vector_store


# load cross encoder model
def load_cross_encoder():

    cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL_NAME)

    return cross_encoder


# Retrive + rerank
def retrieve_similar_attacks(query, k=TOP_K, rerank_k=RERANK_TOP_K):

    # vector retrival

    vector_store = load_vector_database()

    results = vector_store.similarity_search_with_score(query, k=k)

    candidates = []

    for document, score in results:
        candidates.append(
            {
                "content": document.page_content,
                "category": document.metadata.get("category"),
                "style": document.metadata.get("style"),
                "source_format": document.metadata.get("source_format"),
                "embedding_distance": float(score),
            }
        )
    if not candidates:
        return []

    # cross encoder reranking

    cross_encoder = load_cross_encoder()

    pairs = [(query, candidate["content"]) for candidate in candidates]

    rerank_scores = cross_encoder.predict(pairs)

    # add cross encoder scores
    for candidate, score in zip(candidates, rerank_scores):
        candidate["cross_encoder_score"] = float(score)

    # sort by cross encoder score
    candidates.sort(key=lambda x: x["cross_encoder_score"], reverse=True)

    # Keep top 3 rerank
    final_results = candidates[:rerank_k]

    return final_results
