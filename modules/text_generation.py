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

def _generate_reply(question, state, stopping_strings=None, is_chat=False, escape_html=False, for_ui=False,n_retries=2):
    #print(shared.settings['show_controls'],shared.settings['say_sources'])
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

    response= globals.Ask_question_to_thread(question,globals.thread)

    #Sometimes it doesn´t find the answer->we´ll ask 2 more times
    iter_not_found=0
    while iter_not_found<n_retries and "Nu am reușit să găsesc informațiile în documente" in response:
        new_thread=globals._get_new_thread(state["history"]["visible"])
        response= globals.Ask_question_to_thread(question,globals.thread)
        iter_not_found+=1


    response= delete_sursa(response)
    #yield "Soy felix y tengo hambre."

    if shared.settings["say_sources"]:
        #new_thread=globals._get_new_thread(state["history"]["visible"])
        response+= "\nCitat: "+delete_sursa(globals.Ask_question_to_thread("Spune-mi citatul exact din care ai luat-o",globals.thread))
        response+= "\nSursa: "+delete_sursa(globals.Ask_question_to_thread("Spune-mi fișierele din care ai luat-o",globals.thread))
        #response+= "\nQuote: "+delete_sursa(globals.Ask_question_to_thread("Tell me the exact quote/s you got that from",globals.thread))
        #response+= "\nSursa: "+delete_sursa(globals.Ask_question_to_thread("Tell me the file/s you got that from",globals.thread))
    yield response  



def delete_sursa(text):
    result = re.sub(r"【.*?sur.*?】", "", text)
    result = re.sub(r"【.*?source.*?】", "", result)    
    return result



def stop_everything_event():
    #This would be great to fix (but probably a pain)
    #Like this function works, but it would need to be integrated into _generate_reply
    shared.stop_everything = True


