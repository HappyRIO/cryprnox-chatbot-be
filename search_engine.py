from common_helper import create_embedding
from database import ChatDatabase
import openai
import re
import json
import faiss
import numpy as np
import pandas as pd
from os import getenv

class SearchEngine:
    def __init__(self, index_file="faiss_index.bin", metadata_file="metadata.csv"):
        self.index_file = index_file
        self.metadata_file = metadata_file
        self.file_path = "intent.json"

        # Try loading Faiss index, else create a new one
        try:
            self.index = faiss.read_index(self.index_file)
            self.metadata_df = pd.read_csv(self.metadata_file)
        except:
            self.index = None
            self.metadata_df = pd.DataFrame(columns=["text", "path"])
    
    def query_faiss(self, embedding, k=5):
        if self.index is None or self.index.ntotal == 0:
            return {"list_of_knowledge_base": []}  # Return empty if no data

        # Convert embedding to the required format
        vector = np.array(embedding, dtype=np.float32).reshape(1, -1)
        
        # Search the Faiss index
        distances, indices = self.index.search(vector, k)

        # Retrieve corresponding metadata
        results = []
        for idx in indices[0]:
            if idx != -1:  # Valid index check
                results.append(self.metadata_df.iloc[idx]["text"])

        return {"list_of_knowledge_base": results}
    
    def query_vector_db(self, embedding):
        return self.query_faiss(embedding)
  
    def load_intents(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def match_greeting_intent(self, user_input, intents):
        for intent, data in intents['intents'].items():
            for pattern in data['patterns']:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return intent
        return None

    def response_to_intent(self, intent, intents):
        return intents['intents'][intent]['responses'][0]

    def search(self, msg):
        user_query = msg[-1].content
        intents = self.load_intents(self.file_path)
        intent = self.match_greeting_intent(user_query, intents)
        print(f"intent: {intent}")

        if intent == "greeting_intent" or intent == "introduction_intent" or intent == "end_intent":
            response = self.response_to_intent(intent, intents)
            texts = response.split(" ")
            for text in texts:
                yield f"{text} "
        else:
            additional_info = ""

            if intent == "price_intent":
                response = self.response_to_intent(intent, intents)
                additional_info = response
            
            embedding = create_embedding(user_query)        
            result = self.query_vector_db(embedding)

            knowledge_base = "\n".join(result['list_of_knowledge_base'])
            print(f"knowledge_base: {knowledge_base[:100]}")

            system_content = """You are an assistant for the Cryptnox website.
            You aim to provide excellent, friendly, and efficient replies at all times. 
            Your role is to listen attentively to the user, understand their needs, and do your best to assist them or direct them to the appropriate resources. 
            Respond with simple, direct answers.
            Base all responses on verified information from the knowledge base. Double-check facts to ensure reliability.
            Please answer shortly and clearly.
            """

            additional_info += """Users can buy the Cryptonox card on Amazon and official website. 
            Cryptnox shop url: https://shop.cryptnox.com
            Amazon product url: https://www.amazon.com/dp/B0B384JCP8

            """
            user_content = f"""
                Knowledge Base:
                ---
                {additional_info}
                {knowledge_base}
                ---
                User Query: {user_query}
                Answer:
            """
            system_message = {"role": "system", "content": system_content}
            user_message = {"role": "user", "content": user_content}
            
            client = openai.Client(api_key=getenv("OPENAI_API_KEY"))
            chatgpt_response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[system_message, msg.pop(), user_message],
                stream=True
            )

            answer = ''
            for chunk in chatgpt_response:
                if chunk.choices[0].delta.content is not None:
                    text = chunk.choices[0].delta.content
                    answer += text
                    yield f"{text}"
            
            chat_database = ChatDatabase()
            chat_database.insert_data(user_query, answer)
