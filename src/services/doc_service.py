import os
from werkzeug.utils import secure_filename
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import Pinecone
from src.services.vector_service import VectorService
import uuid

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'tmp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class DocumentService:
    def __init__(self):
        self.vector_service = VectorService()

    def process_and_upload_pdf(self, file) -> dict:
        """Saves a PDF, extracts text, chunks it, and uploads to Pinecone."""
        if not file or file.filename == '':
            return {"success": False, "error": "No selected file"}
            
        filename = secure_filename(file.filename)
        # add uuid to prevent collision
        filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            # 1. Load Data
            loader = PyPDFLoader(filepath)
            documents = loader.load()

            # 2. Split chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            text_chunks = text_splitter.split_documents(documents)

            # 3. Add to Pinecone
            Pinecone.from_documents(
                documents=text_chunks,
                index_name=self.vector_service.index_name,
                embedding=self.vector_service.embeddings
            )
            
            return {
                "success": True, 
                "message": f"Successfully processed '{file.filename}' into {len(text_chunks)} chunks."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Cleanup temp file
            if os.path.exists(filepath):
                os.remove(filepath)
