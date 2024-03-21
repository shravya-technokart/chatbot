import os
import json 
import pymongo
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)
mongodb_url = "mongodb+srv://shravya:shetty34@chatbot-details.icmkkzh.mongodb.net"
client_mongo = pymongo.MongoClient(mongodb_url)
db = client_mongo['chatbot-details']
collection = db['docs-data']
collection_chatbot = db['chatbot-details']

chat_bot = "LCBGTECH"
manager_email = "manager@gmail.com"

def chatbot():
    doc = collection_chatbot.find_one({"chat_bot": chat_bot, "manager_email":manager_email})
    system_prompt = doc["system_prompt"]

    print(chat_bot, manager_email, system_prompt)

    messages = [{"role": "system", "content": system_prompt}]

    chatting = True

    while chatting:
        user_query = input("Enter user query: ")
        print(user_query)

        def get_embedding(text, model="text-embedding-3-small"):
            text = text.replace("\n", " ")
            return client.embeddings.create(input=text, model=model, dimensions=1536).data[0].embedding

        def vector_search(user_query, collection):
            query_embedding = get_embedding(user_query)
            pipeline = [
            {
            "$vectorSearch": {
                "index": "chatbot-vector",
                "queryVector":query_embedding,
                "path":"embedded_chunk",
                "numCandidates": 1536,
                "limit": 6
            }
            },
            {
            '$project': {
                '_id': 0,
                'chat_bot': 1,
                'manager_email': 1,  
                'chunk': 1
            }
            }
            ]

            results = collection.aggregate(pipeline)
            chunk_data = ""
            for doc in results:
                if doc['manager_email']==manager_email and doc['chat_bot'] == chat_bot:
                    chunk_data += doc['chunk']
            return chunk_data 
 
        chunk_data = vector_search(user_query, collection)

        user_prompt = f"""
            The Context based on which you have to respond to user query is provided below.

            Context = {chunk_data}
        ----------------------------------------------------------------------------------------------

            User_Query for which you have to respond based on above given Context.
            User_Query = {user_query}
        """

        messages.append({'role':'user', 'content':user_prompt})
     
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo-0125"
        )
        assistant = chat_completion.choices[0].message
        messages.append(assistant)
        print(assistant.content)

chatbot()