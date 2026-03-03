# 🩺 Medical RAG Chatbot (LangChain + Pinecone)

A production-ready, full-stack medical question-answering conversational AI built with **LangChain**, **Pinecone**, and **Flask**. 
This application reads medical PDF documents and answers user queries using **Retrieval-Augmented Generation (RAG)**, drastically reducing hallucinations by grounding the AI in factual medical documents.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/flask-latest-green)

---

## ✨ Features (Refactored & Upgraded)

- **Conversational Memory**: Remembers past interactions per session using SQLite and LangChain's `RunnableWithMessageHistory`.
- **Real-Time Streaming**: Uses Server-Sent Events (SSE) to stream GPT-4o-mini responses to the UI just like ChatGPT.
- **Dynamic PDF Uploads**: Directly upload new medical PDFs from the UI. Documents are chunked and ingested into Pinecone on the fly.
- **Source Citations**: Every AI response tracks and displays the exact document sources and page numbers used to generate the answer.
- **Chat History & Sessions**: Creates and manages multiple chat sessions using a robust SQLite database backend (`SQLAlchemy`).
- **Markdown & Code UI**: A modern Light/Dark themed UI with typing indicators, markdown parsing (`marked.js`), and smooth auto-scrolling.
- **Export to PDF**: Single-click export of any chat session into a formatted PDF using `html2pdf.js`.
- **Voice Support**: Integrated Web Speech API for voice-to-text dictation mapping directly into the chat input.
- **Rate Limiting**: Integrated `Flask-Limiter` to protect API endpoints from spam and abuse.

---

## 🛠 Tech Stack

- **Backend Framework**: Python / Flask / Flask-SQLAlchemy / Flask-Limiter
- **AI & RAG Pipeline**: LangChain Classic / OpenAI API (`gpt-4o-mini`)
- **Vector Database**: Pinecone Serverless
- **Embeddings**: HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`)
- **Frontend**: Vanilla JS (ES6), HTML5, CSS3, FontAwesome
- **Deployment**: Docker

---

## 📂 Project Structure

```text
medical-rag-chatbot/
├── .env                     # Environment variables (Ignored in Git)
├── app.py                   # Flask Application API & Controller
├── config.py                # App Configuration & Env Validations
├── database.py              # SQLite Database configuration
├── models.py                # SQL Models (ChatSession, ChatMessage)
├── Dockerfile               # Containerization configuration
├── requirements.txt         # Python dependencies
├── src/
│   └── services/
│       ├── doc_service.py   # Handles PDF upload, chunking, and indexing
│       ├── llm_service.py   # RAG pipeline, LLM connections, memory
│       └── vector_service.py# Pinecone embedding wrappers
├── utils/
│   ├── rate_limiter.py      # Flask-Limiter definitions
│   └── prompts.py           # System prompts with hardcoded medical disclaimers
├── static/
│   ├── css/style.css        # Responsive, themable styling
│   └── js/chat.js           # Frontend interactions, SSE streaming, Web Speech
└── templates/
    └── chat.html            # Core UI layout
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/Shehjad2019/medical-rag-chatbot.git
cd medical-rag-chatbot
```

### 2️⃣ Environment Variables
Create a `.env` file in the root directory:
```env
PINECONE_API_KEY=your_pinecone_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_INDEX_NAME=medicalbot
```
*(Need keys? Get them at [Pinecone](https://www.pinecone.io) and [OpenAI](https://platform.openai.com/).)*

### 3️⃣ Run Locally (Virtual Environment)
```bash
# Create venv and activate
python -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```
**Access the app:** `http://localhost:8080`

### 4️⃣ Run via Docker (Recommended for Production)
```bash
# Build the image
docker build -t medical-rag:latest .

# Run the container (pass env variables or use --env-file)
docker run -p 8080:8080 \
  -e OPENAI_API_KEY="your_openai_key" \
  -e PINECONE_API_KEY="your_pinecone_key" \
  medical-rag:latest
```

---

## ⚠️ Disclaimer & Notes

- **Educational Purposes Only**: This project is built for learning, prototyping, and portfolio purposes. 
- **Not Medical Advice**: The AI includes strict system prompt disclaimers warning against using its outputs to replace professional medical diagnosis or treatment.
- **Data Dependency**: The quality of the RAG responses heavily relies upon the quality of the PDFs uploaded to the Pinecone index.

---

## 👨‍💻 Author

**Shehjad Patel**  
Computer Engineering | GenAI & LangChain Enthusiast

⭐ **If you like this project, please consider giving it a star on GitHub!** 😊
