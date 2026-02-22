import os
import time
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

from rag import rag_pipeline
from router import classify_query, get_model_for_classification
from evaluator import evaluate_response

load_dotenv()

app = FastAPI(title="ClearPath Chatbot API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
if not os.getenv("GROQ_API_KEY"):
    print("WARNING: GROQ_API_KEY is not set. API calls will fail.")
groq_client = Groq()

# In-memory storage for conversation memory (Bonus: Conversation Memory)
# Format: { "conv_id": [ {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."} ] }
conversations = {}

class QueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class SourceItem(BaseModel):
    document: str
    page: Optional[int] = None
    relevance_score: Optional[float] = None

class TokenUsage(BaseModel):
    input: int
    output: int

class Metadata(BaseModel):
    model_used: str
    classification: str
    tokens: TokenUsage
    latency_ms: int
    chunks_retrieved: int
    evaluator_flags: List[str]

class QueryResponse(BaseModel):
    answer: str
    metadata: Metadata
    sources: List[SourceItem]
    conversation_id: str

@app.on_event("startup")
def startup_event():
    # Build the FAISS index on startup
    print("Building RAG Index on startup...")
    rag_pipeline.build_index()
    print("Startup complete.")

@app.post("/query", response_model=QueryResponse)
def query_chatbot(req: QueryRequest):
    start_time = time.time()
    
    question = req.question
    conv_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:8]}"

    # 1. Routing Layer
    classification = classify_query(question)
    model_used = get_model_for_classification(classification)

    # 2. Retrieval Layer (RAG)
    retrieved_chunks = rag_pipeline.retrieve(question, top_k=3)
    
    # Format context for LLM
    context_text = "\n\n".join([f"Source: {c['document']} (Page {c['page']})\nText: {c['text']}" for c in retrieved_chunks])
    
    # 3. Construct Prompt with Conversation Memory
    system_prompt = (
        "You are the Clearpath customer support chatbot. "
        "Answer the user's question using ONLY the provided context. "
        "If you do not know the answer or the context does not contain the information, explicitly say that you cannot find the information or you don't know.\n\n"
        f"Context:\n{context_text}"
    )

    history = conversations.get(conv_id, [])
    
    messages = [{"role": "system", "content": system_prompt}]
    # Add up to last 4 messages of history to keep context window manageable
    messages.extend(history[-4:])
    messages.append({"role": "user", "content": question})

    # 4. LLM Generation
    try:
        response = groq_client.chat.completions.create(
            model=model_used,
            messages=messages,
            temperature=0.0,
            max_tokens=1024
        )
        answer = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
    except Exception as e:
        print(f"Groq API Error: {e}")
        # Fallback if API fails
        answer = f"Error communicating with LLM: {str(e)}"
        input_tokens = 0
        output_tokens = 0

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # 5. Output Evaluation Layer
    flags = evaluate_response(answer, len(retrieved_chunks))

    # 6. Logging
    log_entry = {
        "query": question,
        "classification": classification,
        "model_used": model_used,
        "tokens_input": input_tokens,
        "tokens_output": output_tokens,
        "latency_ms": latency_ms
    }
    print(f"ROUTING LOG: {log_entry}")

    # Update conversation history
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})
    conversations[conv_id] = history

    # Construct response
    sources = [
        SourceItem(
            document=c["document"],
            page=c["page"],
            relevance_score=c["relevance_score"]
        ) for c in retrieved_chunks
    ]

    return QueryResponse(
        answer=answer,
        metadata=Metadata(
            model_used=model_used,
            classification=classification,
            tokens=TokenUsage(input=input_tokens, output=output_tokens),
            latency_ms=latency_ms,
            chunks_retrieved=len(retrieved_chunks),
            evaluator_flags=flags
        ),
        sources=sources,
        conversation_id=conv_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
