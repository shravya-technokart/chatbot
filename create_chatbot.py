import os
import json 
import pymongo
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)
client_mongo = pymongo.MongoClient(os.environ.get("mongodb_url"))
db = client_mongo['chatbot-details']
collection = db['docs-data']

chat_bot = "Trainer"
manager_email = "manager@gmail.com"

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
                "limit": 8
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
    chunk_data = "Context = "
    count = 0
    for doc in results:
        if doc['manager_email']==manager_email and doc['chat_bot'] == chat_bot:
            chunk_data += doc['chunk']
            count += 1
        if count==6:
            break
    return chunk_data 

user_query = "Adobe logo."
chunk_data = vector_search(user_query, collection)
print(chunk_data)

class ChatBot:
    def __init__(self):
        self.chatbot_name = input("Enter Chatbot Name: ")
        self.personality = "You are Chatbot."
        self.company = ""
        self.services = ""
        self.others = ""

    def get_domain_knowledge(self) -> dict:
        personality = input("Personality of Chatbot: ")
        if personality != "":
            self.personality = """
                As a chatbot you need to maintain your PERSONALITY as described below.
                PERSONALITY - '{personality}'
            ----------------------------------------------------------------------------------------------------
            """
        company = input("Company Details: ")
        if company!="":
            self.company = """
                Company_Details under which you are acting as a chatbot is described below.
                Company_Details - '{company}'
            ----------------------------------------------------------------------------------------------------
            """
        services = input("Service Details: ")
        if services!="":
            self.services = """
                Service_Details which your company provides is described below.
                Service_Details - '{services}'
            ----------------------------------------------------------------------------------------------------
            """
        other = input("Other Details : ")
        if other!="":
            self.other = """
                Other_Details which your company provides is described below.
                Other_Details - '{other}'
            ----------------------------------------------------------------------------------------------------
            """
        return {"personality":self.personality, "company":self.company, "services":self.services, "other_details": self.others}

    def get_documents(self):
        pass

    def generate_system_message(self) -> str:
        system_prompt = """
            You are a chatbot designed to reply user based on Context that would be given to you. 
            
            Some of the Characteristic Information for you is given below - 
            {self.personality}
            {self.comapany}
            {self.services}
            {self.others}
            
        """
        return system_prompt