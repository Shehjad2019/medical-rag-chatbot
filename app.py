from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from config import Config
from models import db, ChatSession, ChatMessage
from src.services.llm_service import LLMService
from src.services.doc_service import DocumentService
from utils.rate_limiter import limiter
import json
import logging

# Configure Application Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Application
app = Flask(__name__)
app.config.from_object(Config)

# Validate config before bringing app up
Config.validate()

# Initialize DB
db.init_app(app)

# Initialize Limiter
limiter.init_app(app)

with app.app_context():
    db.create_all()

# Instantiate Singletons (or lazily per request, but instantiation here is fine for Flask)
# Using sync LLMService here, we can iterate over the sync stream.
llm_service = LLMService(streaming=True)
doc_service = DocumentService()


# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

@app.route("/")
def index():
    """Renders the main Chat HTML interface."""
    return render_template('chat.html')


@app.route("/api/new_chat", methods=["POST"])
def new_chat():
    """Creates a new session in DB and returns the UUID."""
    session = ChatSession()
    db.session.add(session)
    db.session.commit()
    logger.info(f"Created new chat session: {session.id}")
    return jsonify({"session_id": session.id, "success": True})


@app.route("/api/chat_history/<session_id>", methods=["GET"])
@limiter.limit("50 per minute")
def get_chat_history(session_id):
    """Retrieves all chat messages for a specific session."""
    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found", "success": False}), 404
        
    messages = [msg.to_dict() for msg in session.messages]
    return jsonify({"data": messages, "success": True})


@app.route("/api/delete_chat/<session_id>", methods=["DELETE"])
def delete_chat(session_id):
    """Deletes a chat session and all cascading messages."""
    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found", "success": False}), 404
        
    db.session.delete(session)
    db.session.commit()
    logger.info(f"Deleted chat session: {session_id}")
    return jsonify({"success": True})


@app.route("/api/upload_pdf", methods=["POST"])
@limiter.limit("20 per day")
def upload_pdf():
    """Handles PDF file uploads to add to Pinecone knowledge base."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
        
    file = request.files['file']
    result = doc_service.process_and_upload_pdf(file)
    
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@app.route("/api/stream_chat", methods=["POST"])
@limiter.limit("30 per minute")
def stream_chat():
    """Streams response from LLM using SSE (Server Sent Events)."""
    data = request.json
    session_id = data.get("session_id")
    query = data.get("message")
    
    if not session_id or not query:
        return jsonify({"error": "Missing session_id or message", "success": False}), 400

    # Ensure Session exists
    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Invalid session_id", "success": False}), 400

    # 1. Save USER message to DB
    user_msg = ChatMessage(
        session_id=session_id, 
        role="user", 
        content=query, 
        sources_json=json.dumps([])
    )
    db.session.add(user_msg)
    db.session.commit()

    def generate():
        full_response = ""
        source_documents = []
        
        try:
            # The invoke returns the stream generator directly 
            # (Note: Using sync `.stream()` from RunnableWithMessageHistory)
            for chunk in llm_service.conversational_rag_chain.stream(
                {"input": query},
                config={"configurable": {"session_id": session_id}}
            ):
                
                # Check for answer chunk and yield to client
                if "answer" in chunk:
                    delta = chunk["answer"]
                    full_response += delta
                    # Yield in SSE format
                    yield f"data: {json.dumps({'content': delta, 'type': 'chunk'})}\n\n"
                    
                # Collect contexts/sources (Usually exposed via the 'context' key if retrieval chain propagates it)
                if "context" in chunk:
                    # chunk['context'] is a list of Document objects
                    for doc in chunk["context"]:
                        source = doc.metadata.get("source", "Unknown Source")
                        page = doc.metadata.get("page", "")
                        source_documents.append({"source": source, "page": page})
            
            # Deduplicate sources
            unique_sources = [dict(t) for t in {tuple(d.items()) for d in source_documents}]
            
            # 2. Save ASSISTANT response to DB (after streaming completes)
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_response,
                sources_json=json.dumps(unique_sources)
            )
            # Must acquire new session locally inside generator context if detached
            # SQLAlchemy scoped_session generally handles this on current thread.
            db.session.add(assistant_msg)
            db.session.commit()
            
            # 3. Final SSE event with metadata
            yield f"data: {json.dumps({'type': 'sources', 'sources': unique_sources})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Error generating response.'})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')


if __name__ == '__main__':
    # Run the application
    app.run(host="0.0.0.0", port=8080, debug=True)

