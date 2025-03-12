from common_helper import create_embedding
from database import ChatDatabase
import openai
import re
import json
from os import getenv


class SearchEngine:
    def __init__(self, milvus_client, milvus_collection_name):
      self.milvus_client = milvus_client
      self.milvus_collection_name = milvus_collection_name
      self.file_path = "intent.json"
  
    def query_milvus(self, embedding):
        result_count = 5
        result = self.milvus_client.search(
            collection_name=self.milvus_collection_name,
            data=[embedding],
            limit=result_count,
            output_fields=["path", "text"],
            search_params={"metric_type": "IP","params": {}}
        )
            
  
        list_of_knowledge_base = list(map(lambda match: match['entity']['text'], result[0]))
        # list_of_sources = list(map(lambda match: match['entity']['path'], result[0]))
        return {
            'list_of_knowledge_base': list_of_knowledge_base,
            # 'list_of_sources': list_of_sources
        }
  
    def query_vector_db(self, embedding):
        return self.query_milvus(embedding)
  
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

    def search(self, user_query):
        intents = self.load_intents(self.file_path)
        intent = self.match_greeting_intent(user_query, intents)
        print(f"intent: {intent}")
        if intent == "greeting_intent" or intent == "introduction_intent":
            response = self.response_to_intent(intent, intents)
            texts = response.split(" ")
            for text in texts:
                yield f"{text} "
        else:
            addition_info = ""

            if intent == "price_intent":
                response = self.response_to_intent(intent, intents)
                addition_info = response
            
            embedding = create_embedding(user_query)        
            result = self.query_vector_db(embedding)
    
            # print("sources")
            # for source in result['list_of_sources']:
            #     print(source)
    
            knowledge_base = "\n".join(result['list_of_knowledge_base'])

            system_content = """You are an assistant for the Cryptnox website.
            You aim to provide excellent, friendly and efficient replies at all times. 
            Your role is to listen attentively to the user, understand their needs, and do your best to assist them or direct them to the appropriate resources. 
            Respond with simple, direct answers.
            Base all responses on verified information from the knowledge base. Double-check facts to ensure reliability.
            Please answer shortly and clearly.
            Get more out of your Markdown responses by using Markdown formatting.
            """
            addition_info += """Users can buy the cryptonox card in Amazon and cryptonox.com
            """
            user_content = f"""
                Knowledge Base:
                ---
                {addition_info}
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
            messages=[
                system_message,
                user_message
            ],
            stream=True
            )
            answer = ''
            for chunk in chatgpt_response:
                if chunk.choices[0].delta.content is not None:
                    # print(chunk.choices[0].delta.content, end="")
                    text = chunk.choices[0].delta.content
                    answer += text
                    yield f"{text}"
            # print("answer")
            # print(answer)
            chat_database = ChatDatabase()
            chat_database.insert_data(user_query, answer)
  