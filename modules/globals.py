from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client=None
thread=None

current_assistant_key=None

def Start_client():
    global client
    client = OpenAI()

def Start_thread(history=[]):
    global thread
    global client

    if client is None:
        Start_client()
    #We can´t use any other role other than "user", so we must give it both Question and Answer in that same role :(
    if len(history)>1:
        messages=[{
            "role": "user" ,
            "content": "Q: "+x[0]+"\nA: "+x[1]
        } for x in history[1:]]
    else:
        messages=[]

    thread=client.beta.threads.create(messages=messages)