# ClearPath RAG Chatbot - Take-Home Assignment

## Overview
This is the submission for the ClearPath Customer Support Chatbot. It implements a local RAG pipeline without managed services, deterministic rule-based model routing between `llama-3.1-8b-instant` and `llama-3.3-70b-versatile`, an output evaluator, and a vanilla HTML/JS frontend.

## Video Walkthrough
[Link](https://drive.google.com/file/d/1PZDpiSRJOoF8oIdhyH6FdnrZ_BH_UZaX/view?usp=sharing)

## Instructions to Run Locally

### Prerequisites
- Python 3.10+
- A Groq API Key

### Setup Options
1. Navigate to the project directory:
   ```bash
   cd lemnisca_takeHomeAssignment
   ```

2. Create and activate a Virtual Environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install requirements
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Configure your Environment Variables
   Create a `.env` file in the `backend/` directory and add your Groq key:
   ```env
   GROQ_API_KEY=your_actual_api_key_here
   ```

### Running the Application

1. **Start the Backend API:**
   ```bash
   cd backend
   python main.py
   ```
   *Note: On startup, the backend will process the 30 PDFs stored in the `clearpath_docs/` folder and build a FAISS vector index in memory. This might take 5-10 seconds.*

2. **Open the Frontend:**
   Just simply open `frontend/index.html` in your web browser (no web server needed, it hits `localhost:8000` via CORS).
   Alternatively, you can run a simple server inside the frontend folder:
   ```bash
   cd frontend
   python -m http.server 3000
   ```
   And visit `http://localhost:3000`.

## Bonus Challenges Attempted
- **Conversation Memory:** The API handles maintaining multi-turn conversation memory via the `conversation_id` parameter. The context history is managed in-memory, enabling follow-up questions to work smoothly.

## Known Limitations
- The FAISS index builds synchronously on application startup, which is functional for this scale but not viable for dynamic document ingestion.
- The conversation memory uses unbounded in-memory dictionaries. In a real environment, this should be backed by Redis with a TTL.
- **Deployment Limitations:** The application is fully functional locally. However, when deploying to free-tier cloud providers like Render (which limit RAM to 512MB and have strict 2-minute port binding timeouts), the application may crash with an `Out of memory` error or timeout during startup. This is because the local SentenceTransformers model (`all-MiniLM-L6-v2`) requires more memory and time to process 30 PDFs and build the FAISS vector index than the free tier provides. For a production deployment, the vector database loading and index building should be separated into a background worker or an external vector database (like Pinecone) should be used.