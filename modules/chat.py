import base64
import copy
import functools
import html
import json
import re
from datetime import datetime
from functools import partial
from pathlib import Path

import gradio as gr
import yaml
from jinja2.sandbox import ImmutableSandboxedEnvironment
from PIL import Image

import modules.shared as shared
from modules import utils
from modules.extensions import apply_extensions
from modules.html_generator import chat_html_wrapper, make_thumbnail
from modules.logging_colors import logger
from modules.text_generation import generate_reply
from modules.utils import delete_file, get_available_characters, save_file

from modules import globals
# Copied from the Transformers library
jinja_env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)




def start_new_chat(state):
    ##################################
    #Added by me
    ##################################
    if globals.current_assistant_key is not None:
        globals.Start_thread() 
    ##################################


    #mode = state['mode']
    history = {'internal': [], 'visible': []}

    if True:#mode != 'instruct':
        greeting = replace_character_names(state['greeting'], state['name1'], state['name2'])
        if greeting != '':
            history['internal'] += [['<|BEGIN-VISIBLE-CHAT|>', greeting]]
            history['visible'] += [['', apply_extensions('output', greeting, state, is_chat=True)]]

    unique_id = datetime.now().strftime('%Y%m%d-%H-%M-%S')
    save_history(history, unique_id, state['character_menu'])#, state['mode'])

    return history


def get_history_file_path(unique_id, character):#, mode):
    return Path(f'logs/chat/{character}/{unique_id}.json')

def save_history(history, unique_id, character):#, mode):
    p = get_history_file_path(unique_id, character)#, mode)
    print("Saving history to:",p)
    if not p.parent.is_dir():
        p.parent.mkdir(parents=True)

    with open(p, 'w', encoding='utf-8') as f:
        print(p,history)
        f.write(json.dumps(history, indent=4))


def rename_history(old_id, new_id, character):#, mode):
    if shared.args.multi_user:
        return

    old_p = get_history_file_path(old_id, character)#), mode)
    new_p = get_history_file_path(new_id, character)#), mode)
    if new_p.parent != old_p.parent:
        logger.error(f"The following path is not allowed: {new_p}.")
    elif new_p == old_p:
        logger.info("The provided path is identical to the old one.")
    else:
        logger.info(f"Renaming {old_p} to {new_p}")
        old_p.rename(new_p)


def find_all_histories(state):
    if shared.args.multi_user:
        return ['']

    #if state['mode'] == 'instruct':
    #    paths = Path('logs/instruct').glob('*.json')
    #else:
    if True:
        character = state['character_menu']

        # Handle obsolete filenames and paths
        old_p = Path(f'logs/{character}_persistent.json')
        new_p = Path(f'logs/persistent_{character}.json')
        if old_p.exists():
            logger.warning(f"Renaming {old_p} to {new_p}")
            old_p.rename(new_p)
        if new_p.exists():
            unique_id = datetime.now().strftime('%Y%m%d-%H-%M-%S')
            p = get_history_file_path(unique_id, character)#, state['mode'])
            logger.warning(f"Moving {new_p} to {p}")
            p.parent.mkdir(exist_ok=True)
            new_p.rename(p)

        paths = Path(f'logs/chat/{character}').glob('*.json')

    histories = sorted(paths, key=lambda x: x.stat().st_mtime, reverse=True)
    histories = [path.stem for path in histories]

    return histories


def load_latest_history(state):
    '''
    Loads the latest history for the given character in chat or chat-instruct
    mode, or the latest instruct history for instruct mode.
    '''

    if shared.args.multi_user:
        return start_new_chat(state)

    histories = find_all_histories(state)

    if len(histories) > 0:
        history = load_history(histories[0], state['character_menu'])#, state['mode'])
    else:
        history = start_new_chat(state)

    return history


def load_history_after_deletion(state, idx):
    '''
    Loads the latest history for the given character in chat or chat-instruct
    mode, or the latest instruct history for instruct mode.
    '''

    if shared.args.multi_user:
        return start_new_chat(state)

    histories = find_all_histories(state)
    idx = min(int(idx), len(histories) - 1)
    idx = max(0, idx)

    if len(histories) > 0:
        history = load_history(histories[idx], state['character_menu'])#, state['mode'])
    else:
        history = start_new_chat(state)
        histories = find_all_histories(state)

    return history, gr.update(choices=histories, value=histories[idx])


def load_history(unique_id, character):#, mode):
    p = get_history_file_path(unique_id, character)#, mode)

    f = json.loads(open(p, 'rb').read())
    print("f_dict",f)
    return f


def load_history_json(file, history):
    try:
        file = file.decode('utf-8')
        f = json.loads(file)
        if 'internal' in f and 'visible' in f:
            history = f
        else:
            history = {
                'internal': f['data'],
                'visible': f['data_visible']
            }

        return history
    except:
        return history


def delete_history(unique_id, character):#, mode):
    p = get_history_file_path(unique_id, character)#, mode)
    delete_file(p)


def replace_character_names(text, name1, name2):
    text = text.replace('{{user}}', name1).replace('{{char}}', name2)
    return text.replace('<USER>', name1).replace('<BOT>', name2)


def generate_pfp_cache(character):
    cache_folder = Path(shared.args.disk_cache_dir)
    if not cache_folder.exists():
        cache_folder.mkdir()

    for path in [Path(f"characters/{character}.{extension}") for extension in ['png', 'jpg', 'jpeg']]:
        if path.exists():
            original_img = Image.open(path)
            original_img.save(Path(f'{cache_folder}/pfp_character.png'), format='PNG')

            thumb = make_thumbnail(original_img)
            thumb.save(Path(f'{cache_folder}/pfp_character_thumb.png'), format='PNG')

            return thumb

    return None


def load_character(character, name1, name2):
    print(character,name1,name2)
    context = greeting = ""
    greeting_field = 'greeting'
    picture = None

    filepath = None
    for extension in ["yml", "yaml", "json"]:
        filepath = Path(f'characters/{character}.{extension}')
        if filepath.exists():
            break

    if filepath is None or not filepath.exists():
        logger.error(f"Could not find the character \"{character}\" inside characters/. No character has been loaded.")
        raise ValueError

    file_contents = open(filepath, 'r', encoding='utf-8').read()
    data = json.loads(file_contents) if extension == "json" else yaml.safe_load(file_contents)
    cache_folder = Path(shared.args.disk_cache_dir)
    
    ####################################################
    #Added by me
    if "assistant_id" in data:
        globals.current_assistant_key=data["assistant_id"]
    else:
        globals.current_assistant_key=None
    ####################################################


    for path in [Path(f"{cache_folder}/pfp_character.png"), Path(f"{cache_folder}/pfp_character_thumb.png")]:
        if path.exists():
            path.unlink()

    picture = generate_pfp_cache(character)

    # Finding the bot's name
    for k in ['name', 'bot', '<|bot|>', 'char_name']:
        if k in data and data[k] != '':
            name2 = data[k]
            break

    # Find the user name (if any)
    for k in ['your_name', 'user', '<|user|>']:
        if k in data and data[k] != '':
            name1 = data[k]
            break


    greeting = data.get(greeting_field, greeting)

    globals.character_info ={"name1":name1,"name2":name2,"greeting":greeting}
    return name1, name2, picture, greeting, context

