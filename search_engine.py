import sys
from common_helper import create_embedding
import openai

class SearchEngine:
    def __init__(self, milvus_client, milvus_collection_name):
      self.milvus_client = milvus_client
      self.milvus_collection_name = milvus_collection_name
  
    def query_milvus(self, embedding):
        result_count = 5
        # print(f"=query_milvus================{self.milvus_collection_name}=============\n{embedding}")
        result = self.milvus_client.search(
            collection_name=self.milvus_collection_name,
            data=[embedding],
            limit=result_count,
            output_fields=["path", "text"],
            search_params={"metric_type": "IP","params": {}}
        )
            
  
        list_of_knowledge_base = list(map(lambda match: match['entity']['text'], result[0]))
        list_of_sources = list(map(lambda match: match['entity']['path'], result[0]))
        # print(result)
        return {
            'list_of_knowledge_base': list_of_knowledge_base,
            'list_of_sources': list_of_sources
        }
  
    def query_vector_db(self, embedding):
        return self.query_milvus(embedding)
  
    def ask_chatgpt(self, knowledge_base, user_query):
        # system_content = """You are an AI coding assistant designed to help users with their programming needs based on the Knowledge Base provided.
        # If you dont know the answer, say that you dont know the answer. You will only answer questions related to fly.io, any other questions, you should say that its out of your responsibilities.
        # Only answer questions using data from knowledge base and nothing else.
        # """
        system_content = """You are an assistant for the Cryptnox website.
        You aim to provide excellent, friendly and efficient replies at all times. 
        Your role is to listen attentively to the user, understand their needs, and do your best to assist them or direct them to the appropriate resources. 
        If a question is not clear, ask clarifying questions. Please answer simply and correctly.
        """
  
        user_content = f"""
            Knowledge Base:
            ---
            {knowledge_base}
            ---
            User Query: {user_query}
            Answer:
        """
        system_message = {"role": "system", "content": system_content}
        user_message = {"role": "user", "content": user_content}
        OPENAI_API_KEY="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"
        client = openai.Client(api_key=OPENAI_API_KEY)
        chatgpt_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            system_message,
            user_message
        ],
        stream=True
        )
        for chunk in chatgpt_response:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
                print("---")
                text = chunk.choices[0].delta.content
                print(text)
                yield f"data: {text}\n\n"
        # return chatgpt_response
  
    def search(self, user_query):
        embedding = create_embedding(user_query)        
        result = self.query_vector_db(embedding)
  
        print("sources")
        for source in result['list_of_sources']:
            print(source)
  
        knowledge_base = "\n".join(result['list_of_knowledge_base'])

        system_content = """You are an assistant for the Cryptnox website.
        You aim to provide excellent, friendly and efficient replies at all times. 
        Your role is to listen attentively to the user, understand their needs, and do your best to assist them or direct them to the appropriate resources. 
        Respond with simple, direct answers.
        Base all responses on verified information from the knowledge base. Double-check facts to ensure reliability.
        """
        addition_info = """Users can buy the cryptonox card in Amazon and cryptonox.com"""
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
        OPENAI_API_KEY="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"
        client = openai.Client(api_key=OPENAI_API_KEY)
        chatgpt_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            system_message,
            user_message
        ],
        stream=True
        )
        for chunk in chatgpt_response:
            if chunk.choices[0].delta.content is not None:
                # print(chunk.choices[0].delta.content, end="")
                text = chunk.choices[0].delta.content
                yield f"{text}"



        # response = self.ask_chatgpt(knowledge_base, user_query)
  
        # return {
        #     'sources': result['list_of_sources'],
        #     'response': response
        # }
  