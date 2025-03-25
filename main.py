from dotenv import load_dotenv
from os import getenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from search_engine import SearchEngine
from indexer import Indexer
from database import ChatDatabase
from typing import List

load_dotenv()

# Initialize Faiss-based Indexer & SearchEngine
index_file = "faiss_index.bin"
metadata_file = "metadata.csv"
embedding_dim = 1536  # Adjust based on your embedding model

indexer = Indexer(index_file, metadata_file, embedding_dim)
searchEngine = SearchEngine(index_file, metadata_file)
chat_database = ChatDatabase()

print("✅ Server is running...")

### API for indexing & AI search
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Include OPTIONS method
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class MessageRequest(BaseModel):
    msg: List[Message]

class IndexRequest(BaseModel):
    url: str

@app.post("/api/search")
async def search(inp: MessageRequest):
    print(f"💬 User: {inp.msg}")

    search_result = searchEngine.search(inp.msg)

    return StreamingResponse(search_result, media_type='text/event-stream')

@app.post("/api/create_index")
async def create_index(inp: IndexRequest):
    indexer.index_website(inp.url)
    return {"message": "✅ Indexing complete"}

# Serve static files
# app.mount("/", StaticFiles(directory="static", html=True), name="static")
