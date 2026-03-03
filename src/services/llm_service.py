from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from utils.prompts import system_prompt
from src.services.vector_service import VectorService

# In-memory dictionary for active chat sessions
# In production, this can be backed by Redis or directly bound to DB queries
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Returns the chat history for a given session."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

class LLMService:
    def __init__(self, streaming=False, callbacks=None):
        """Initializes the LLM with conversational RAG capabilities."""
        self.vector_service = VectorService()
        self.retriever = self.vector_service.get_retriever()
        
        # Upgraded to ChatOpenAI with GPT-4o-mini
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.4,
            max_tokens=600,
            streaming=streaming,
            callbacks=callbacks
        )
        self.setup_chain()

    def setup_chain(self):
        """Sets up the history-aware retrieval chain."""
        
        # 1. History-aware Retriever Prompt
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )

        # 2. Answer question prompt (incorporates context and chat history)
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        # 3. Final retrieval chain
        self.rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # 4. Wrap with message history logic
        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def invoke(self, session_id: str, query: str):
        """Invokes the conversational chain for a standard non-streaming response."""
        response = self.conversational_rag_chain.invoke(
            {"input": query},
            config={"configurable": {"session_id": session_id}}
        )
        return response

    async def astream(self, session_id: str, query: str):
        """Asynchronously streams chunks back to the client."""
        async for chunk in self.conversational_rag_chain.astream(
            {"input": query},
            config={"configurable": {"session_id": session_id}}
        ):
            yield chunk

