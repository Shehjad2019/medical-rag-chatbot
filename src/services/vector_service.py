from langchain_pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import os

class VectorService:
    def __init__(self):
        # Initialize embeddings using the updated library
        self.embeddings = HuggingFaceEmbeddings(
            model_name='sentence-transformers/all-MiniLM-L6-v2'
        )
        self.index_name = os.environ.get("PINECONE_INDEX_NAME", "medicalbot")
        
    def get_retriever(self, k=3):
        """Returns the Pinecone retriever instance."""
        vectorstore = Pinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": k})

    def similarity_search_with_score(self, query, k=3):
        """Directly searches the index and returns documents with similarity scores."""
        vectorstore = Pinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        return vectorstore.similarity_search_with_score(query, k=k)
