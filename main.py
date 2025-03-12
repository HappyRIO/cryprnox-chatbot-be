from dotenv import load_dotenv
from os import getenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from search_engine import SearchEngine
from indexer import Indexer
from database import ChatDatabase
from pymilvus import MilvusClient


load_dotenv()

milvus_client = MilvusClient(
    uri=getenv("MILVUS_URI"),
    token=getenv("MILVUS_TOKEN"),
)

milvus_collection_name = getenv("MILVUS_COLLECTION_NAME")

indexer = Indexer(milvus_client, milvus_collection_name)
searchEngine = SearchEngine(milvus_client, milvus_collection_name)
chat_database = ChatDatabase()
print("running-----")

### API for indexing & AI search

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Include OPTIONS method
    allow_headers=["*"],
)

class Msg(BaseModel):
    msg: str

@app.get("/")
async def root():
    return {"message": "/search"}

@app.post("/search")
async def search(inp: Msg):
    db_result = chat_database.query_database(inp.msg)

    if db_result:
        return StreamingResponse(db_result, media_type='text/event-stream')
    
    search_result = searchEngine.search(inp.msg)

    return StreamingResponse(search_result, media_type='text/event-stream')

@app.post("/create_index")
async def create_index(inp: Msg):
    result = indexer.index_website(inp.msg)
    return { "message": "Indexing complete" }