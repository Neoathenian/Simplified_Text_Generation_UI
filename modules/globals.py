from openai import OpenAI
from dotenv import load_dotenv
from time import sleep
load_dotenv()

client=None
thread=None

current_assistant_key=None

def Start_client():
    global client
    client = OpenAI()


def _get_new_thread(history=[]):
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

    return client.beta.threads.create(messages=messages)

def Start_thread(history=[]):
    global thread
    global client

    thread=_get_new_thread(history)


def _Ask_question_to_thread(question,thread):
    curr_messages=client.beta.threads.messages.list(
        thread_id = thread.id
    )
    length_history=len(curr_messages.data)


    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
        )
    
    run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=current_assistant_key,
        )

    messages=client.beta.threads.messages.list(
      thread_id = thread.id
    )

    i=0
    #If we ever build a chatbot we can just check if it has increased, now we just check if it has answered the question (which is just when len>1)
    while len(messages.data)==length_history+1 and i<100:
      sleep(1)
      messages=client.beta.threads.messages.list(
        thread_id = thread.id
      )
      #print(messages.data)
      i+=1
      if i%10==0:
          print("Waiting for the assistant to answer the question,i=",i)

    response = messages.data[0].content[0].text.value
    iter=0
    #We´re doing this loop because it was giving us empty answers, and it seemed that waiting a bit gave us the answer
    while len(response)==0 and iter<100:
      sleep(1)
      messages=client.beta.threads.messages.list(
        thread_id = thread.id
      )
      response = messages.data[0].content[0].text.value
      
      iter+=1
      if iter%10==0:
          print("Waiting for the assistant to answer the question,iter=",iter)
    print("")
    print("messages",messages)

    print("the message should be:", messages.data[0].content[0].text.value)
    return messages.data[0].content[0].text.value
    

def Ask_question_to_thread(question,thread):
    try:
        return _Ask_question_to_thread(question,thread)
    except:
        return "The assistant failed for some reason to answer the question, please try again later"