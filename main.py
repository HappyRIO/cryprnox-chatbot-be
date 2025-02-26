from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from search_engine import SearchEngine
from indexer import Indexer
from pymilvus import MilvusClient
import mysql.connector
from datetime import datetime

load_dotenv()

milvus_client = MilvusClient(
    uri="https://in03-db4abcb440194ad.serverless.gcp-us-west1.cloud.zilliz.com",
    token="5187d07c9a94be76400415936a302c0ffb8e4fb7fe52c9f6493eadedd1b01c22a82a1efc7beef2ce838d9875ba70d191cf3820d6"
)

milvus_collection_name = 'cryptnox'

### connection database
def connect_db():
    try:
        connection = mysql.connector.connect(
            host='localhost',            # e.g., 'localhost' or '127.0.0.1'
            user='rio',        # Your MySQL username
            password='jj123!@#',    # Your MySQL password
            database='chat_history'     # Your MySQL database name
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

indexer = Indexer(milvus_client, milvus_collection_name)
searchEngine = SearchEngine(milvus_client, milvus_collection_name)
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
    result = searchEngine.search(inp.msg)
    
    answer = ''
    for text in result:
        answer += text
    
    print(f"--- {answer} ---")
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        timestamp = datetime.now()
        user = inp.msg
        try:
            insert_query = """
                INSERT INTO conversation (user, bot, timestamp)
                VALUES (%s, %s, %s)
            """
            data_tuple = (user, answer, timestamp)
            cursor.execute(insert_query, data_tuple)
            connection.commit()
            
            print("Chat history saved successfully")

        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("Failed to connect to the database")
    # return StreamingResponse(event_stream())
    
    return StreamingResponse(searchEngine.search(inp.msg), media_type='text/event-stream')

@app.post("/create_index")
async def create_index(inp: Msg):
    result = indexer.index_website(inp.msg)
    return { "message": "Indexing complete" }