import pandas as pd

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from config import (
    METADATA_PATH,
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
)


def load_training_attack_examples():
    print("loading metadata...")

    metadata = pd.read_csv(METADATA_PATH)
    print(f"Total metadata rows:{len(metadata)}")

    # use train split only
    train_data = metadata[metadata["split"].astype(str).str.lower() == "train"].copy()

    print(f"Total training rows:{len(train_data)}")

    # use malicious sample only
    attack_data = train_data[train_data["label"] == 1].copy()

    print(f"Malicious training examples: {len(attack_data)}")

    # check attack category
    print("\n Attack category")
    print(attack_data["category"].value_counts())

    return attack_data


def create_documents(attack_data):
    documents = []

    for _, row in attack_data.iterrows():
        document = Document(
            # Text that will embedded
            page_content=str(row["content"]),
            # metadata store with content
            metadata={
                "category": str(row["category"]),
                "style": str(row["style"]),
                "source_format": str(row["source_format"]),
                "split": "train",
            },
        )
        documents.append(document)
    return documents


def build_vector_database(documents):
    print("\nLoading embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("Creating Chroma vector database...")

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB_PATH),
        collection_name=COLLECTION_NAME,
    )
    print("\nVector database created successfully.")
    return vector_store


def main():
    attack_data = load_training_attack_examples()
    documents = create_documents(attack_data)
    print(f"\n Documents prepared: {len(documents)}")
    build_vector_database(documents)


if __name__ == "__main__":
    main()
