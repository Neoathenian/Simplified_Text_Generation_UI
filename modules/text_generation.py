from time import sleep
import modules.shared as shared
from modules.logging_colors import logger
from modules import globals
import re

def generate_reply(*args, **kwargs):
    shared.generation_lock.acquire()
    try:
        for result in _generate_reply(*args, **kwargs):
            yield result
    finally:
        shared.generation_lock.release()

def _generate_reply(question, state, stopping_strings=None, is_chat=False, escape_html=False, for_ui=False):
    if globals.current_assistant_key is None:
        yield "Vă rugăm să selectați mai întâi un asistent din fila de selecție a caracterelor de mai jos (derulați în jos)"
        #yield "Please select an assistant first from the character selection tab below (scroll down)"
        return
    #print(state["history"])
    #Write me a poem of why there are infinite prime numbers
    #yield "Soy felix y tengo hambre."
    if globals.client is None:
        globals.Start_client()
        globals.Start_thread()
    if globals.thread is None:
        globals.Start_thread(state["history"]["visible"])

    curr_messages=globals.client.beta.threads.messages.list(
        thread_id = globals.thread.id
    )
    length_history=len(curr_messages.data)

    #yield "I´m hungryyyy"
    #print("question", question)
    #print("state", state)
    #yield "Respuesta automática"
    message = globals.client.beta.threads.messages.create(
        thread_id=globals.thread.id,
        role="user",
        content=question
        )
    
    run = globals.client.beta.threads.runs.create(
            thread_id=globals.thread.id,
            assistant_id=globals.current_assistant_key,
        )

    messages=globals.client.beta.threads.messages.list(
      thread_id = globals.thread.id
    )

    i=0
    #If we ever build a chatbot we can just check if it has increased, now we just check if it has answered the question (which is just when len>1)
    while len(messages.data)==length_history+1 and i<100:
      sleep(1)
      messages=globals.client.beta.threads.messages.list(
        thread_id = globals.thread.id
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
      messages=globals.client.beta.threads.messages.list(
        thread_id = globals.thread.id
      )
      response = messages.data[0].content[0].text.value
      
      iter+=1
      if iter%10==0:
          print("Waiting for the assistant to answer the question,iter=",iter)
    print("")
    print("messages",messages)

    print("the message should be:", messages.data[0].content[0].text.value)

    yield delete_sursa(messages.data[0].content[0].text.value)
    #yield "Soy felix y tengo hambre."


def delete_sursa(text):
    result = re.sub(r"【.*?sur.*?】", "", text)
    result = re.sub(r"【.*?source.*?】", "", result)    
    return result



def stop_everything_event():
    #This would be great to fix (but probably a pain)
    #Like this function works, but it would need to be integrated into _generate_reply
    shared.stop_everything = True


