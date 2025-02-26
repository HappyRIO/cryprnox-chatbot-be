
import openai
import numpy as np
# from openai import OpenAI
OPENAI_API_KEY="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"
client = openai.Client(api_key=OPENAI_API_KEY)
def create_embedding(text):
    embedding = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
        encoding_format="float"
    )

    embeddings_array = np.array([data.embedding for data in embedding.data])

    return embeddings_array[0]
