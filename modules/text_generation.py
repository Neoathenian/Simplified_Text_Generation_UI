import ast
import copy
import html
import pprint
import random
import re
import time
import traceback
from time import sleep
import numpy as np
import torch
import transformers
from transformers import LogitsProcessorList, is_torch_xpu_available

import modules.shared as shared
from modules.callbacks import (
    Iteratorize,
    Stream,
    _StopEverythingStoppingCriteria
)
from modules.extensions import apply_extensions
from modules.grammar.grammar_utils import initialize_grammar
from modules.grammar.logits_process import GrammarConstrainedLogitsProcessor
from modules.html_generator import generate_4chan_html, generate_basic_html
from modules.logging_colors import logger
#from modules.models import clear_torch_cache, local_rank
from modules import globals

def generate_reply(*args, **kwargs):
    shared.generation_lock.acquire()
    try:
        for result in _generate_reply(*args, **kwargs):
            yield result
    finally:
        shared.generation_lock.release()

#Here´s where you actually generate the replies
#def _generate_reply(question, state, stopping_strings=None, is_chat=False, escape_html=False, for_ui=False):
#    print("The question is", question)
#    print("state", state)
#    print("stopping_strings", stopping_strings)
#    print("is_chat", is_chat)
#    print("escape_html", escape_html)
#    print("for_ui", for_ui)
#    yield "Respuesta automática"


def _generate_reply(question, state, stopping_strings=None, is_chat=False, escape_html=False, for_ui=False):
    print(state["history"])
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

    print(len(state["history"]),length_history)
    print(curr_messages)
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
            assistant_id="asst_77uQsIfNDETCxNLbUJF4suDn",
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

    yield messages.data[0].content[0].text.value
   #yield "Soy felix y tengo hambre."
    

def stop_everything_event():
    #This would be great to fix (but probably a pain)
    #Like this function works, but it would need to be integrated into _generate_reply
    shared.stop_everything = True


