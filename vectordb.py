import os, shutil
from langchain.vectorstores import Chroma


def create_vector_db(embeddings, documents, persist_directory):
    vector_db = Chroma.from_documents(
        documents=documents, embedding=embeddings, persist_directory=persist_directory
    )
    return vector_db
