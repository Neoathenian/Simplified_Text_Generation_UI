import json
from functools import partial
from pathlib import Path

import gradio as gr
from PIL import Image

from modules import chat, shared, ui, utils
from modules.text_generation import stop_everything_event
from modules.utils import gradio
from modules.shared import settings
import os
import time

from modules.script import generate_css,generate_html,filter_cards,custom_js,select_character,cards

inputs = ('Chat input', 'interface_state')
reload_arr = ('history', 'name1', 'name2', 'character_menu')# 'mode',, 'chat_style', 'name1', 'name2'
clear_arr = ('delete_chat-confirm', 'delete_chat', 'delete_chat-cancel')


def New_chat(history, name1, name2,  character):  
    shared.gradio["chatbot"].update(visible=False)
    #return []

def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)

def bot(history):
    response = "**That's cool!**"
    #print(history)
    history[-1][1] = ""
    for character in response:
        history[-1][1] += character
        time.sleep(0.05)
        yield history

def add_text(history, text):
    history = history + [(text, None)]
    #history=[history[-1]]#This would make it so that you only see the last message
    return history, gr.Textbox(value="", interactive=False)


#def add_file(history, file):
#    history = history + [((file.name,), None)]
#    return history



def create_ui():
    mu = shared.args.multi_user

    shared.gradio['Chat input'] = gr.State()
    shared.gradio['history'] = gr.State({'internal': [], 'visible': []})

    with gr.Tab('Chat', elem_id='chat-tab', elem_classes=("old-ui" if shared.args.chat_buttons else None)):
        with gr.Column(elem_id='chat-col'):
            shared.gradio["chatbot"] = gr.Chatbot(
                [(None,"Hello")],
                elem_id="chat2",
                bubble_full_width=False,
                show_label=False,
                avatar_images=(None, ("characters/IFire (CARLA).png")),
            )

            shared.gradio["chatbot"].update(avatar_images=(None,None))
            txt = gr.Textbox(
                    scale=4,
                    show_label=False,
                    placeholder="Send a message",
                    container=False,
                    elem_id="input_textbox",
                )
            txt_msg = txt.submit(add_text, [shared.gradio["chatbot"], txt], [shared.gradio["chatbot"], txt], queue=False).then(
                bot, shared.gradio["chatbot"], shared.gradio["chatbot"], api_name="bot_response"
            )
            txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)
            
            shared.gradio["chatbot"].like(print_like_dislike, None, None)

        # Hover menu buttons
        with gr.Column(elem_id='chat-buttons'):
            with gr.Row():
                shared.gradio['Regenerate'] = gr.Button('Regenerate (Ctrl + Enter)', elem_id='Regenerate')
                shared.gradio['Continue'] = gr.Button('Continue (Alt + Enter)', elem_id='Continue')
                shared.gradio['Remove last'] = gr.Button('Remove last reply (Ctrl + Shift + Backspace)', elem_id='Remove-last')

            with gr.Row():
                shared.gradio['Replace last reply'] = gr.Button('Replace last reply (Ctrl + Shift + L)', elem_id='Replace-last')
                shared.gradio['Copy last reply'] = gr.Button('Copy last reply (Ctrl + Shift + K)', elem_id='Copy-last')

        with gr.Row(elem_id='past-chats-row', elem_classes=['pretty_scrollbar']):
            with gr.Column():
                with gr.Row():
                    shared.gradio['unique_id'] = gr.Dropdown(label='Past chats', elem_classes=['slim-dropdown'], interactive=not mu)

                with gr.Row():
                    shared.gradio['rename_chat'] = gr.Button('Rename', elem_classes='refresh-button', interactive=not mu)
                    shared.gradio['delete_chat'] = gr.Button('🗑️', elem_classes='refresh-button', interactive=not mu)
                    shared.gradio['delete_chat-confirm'] = gr.Button('Confirm', variant='stop', visible=False, elem_classes='refresh-button')
                    shared.gradio['delete_chat-cancel'] = gr.Button('Cancel', visible=False, elem_classes='refresh-button')
                    shared.gradio['Start new chat'] = gr.Button('New chat', elem_classes='refresh-button')

                with gr.Row(elem_id='rename-row'):
                    shared.gradio['rename_to'] = gr.Textbox(label='Rename to:', placeholder='New name', visible=False, elem_classes=['no-background'])
                    shared.gradio['rename_to-confirm'] = gr.Button('Confirm', visible=False, elem_classes='refresh-button')
                    shared.gradio['rename_to-cancel'] = gr.Button('Cancel', visible=False, elem_classes='refresh-button')

        with gr.Row(elem_id='character-gallery-row', elem_classes=['pretty_scrollbar']):
            with gr.Accordion("Character gallery", open=settings["gallery-open"], elem_id='gallery-extension'):
                gr.HTML(value="<style>" + generate_css() + "</style>")
                with gr.Row():
                    filter_box = gr.Textbox(label='', placeholder='Filter', lines=1, max_lines=1, container=False, elem_id='gallery-filter-box')
                    update = gr.Button("Search", elem_classes='refresh-button')

                gallery = gr.Dataset(
                    components=[gr.HTML(visible=False)],
                    label="",
                    samples=generate_html(),
                    elem_classes=["character-gallery"],
                    samples_per_page=settings["gallery-items_per_page"]
                )
                shared.gradio['character_menu'] = gr.Dropdown(value=None, choices=utils.get_available_characters(), elem_id='character-menu', elem_classes='slim-dropdown')

            filter_box.change(lambda: None, None, None, _js=f'() => {{{custom_js()}; gotoFirstPage()}}').success(
                filter_cards, filter_box, gallery).then(
                lambda x: gr.update(elem_classes='highlighted-border' if x != '' else ''), filter_box, filter_box, show_progress=False)

            update.click(generate_html, [], None).success(
                filter_cards, filter_box, gallery)
            
            
            
            gallery.select(select_character, None, shared.gradio['character_menu'])

        
def create_chat_settings_ui():
    mu = shared.args.multi_user
    with gr.Tab('Character'):
        with gr.Row():
            with gr.Column(scale=8):
#
                shared.gradio['name1'] = gr.Textbox(value=shared.settings['name1'], lines=1, label='Your name')
                shared.gradio['name2'] = gr.Textbox(value='', lines=1, label='Character\'s name')
                shared.gradio['context'] = gr.Textbox(value='', lines=10, label='Context', elem_classes=['add_scrollbar'])
                shared.gradio['greeting'] = gr.Textbox(value='', lines=5, label='Greeting', elem_classes=['add_scrollbar'])
#
            with gr.Column(scale=1):
                shared.gradio['character_picture'] = gr.Image(label='Character picture', type='pil', interactive=not mu)
                shared.gradio['your_picture'] = gr.Image(label='Your picture', type='pil', value=Image.open(Path('cache/pfp_me.png')) if Path('cache/pfp_me.png').exists() else None, interactive=not mu)

#
            with gr.Column():
                shared.gradio['load_chat_history'] = gr.File(type='binary', file_types=['.json', '.txt'], label='Upload History JSON')


def create_event_handlers():

    # Obsolete variables, kept for compatibility with old extensions
    shared.input_params = gradio(inputs)
    shared.reload_inputs = gradio(reload_arr)

    if not shared.args.multi_user:
        shared.gradio['unique_id'].select(
            chat.load_history, gradio('unique_id', 'character_menu'), gradio('history')).then(
            chat.redraw_html, gradio(reload_arr), None)

    shared.gradio['Start new chat'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.start_new_chat, gradio('interface_state'), gradio('history')).then(
        chat.redraw_html, gradio(reload_arr), None).then(
        lambda x: gr.update(choices=(histories := chat.find_all_histories(x)), value=histories[0]), 
            gradio('interface_state'), gradio('unique_id')).then(New_chat,gradio(reload_arr),shared.gradio["chatbot"])

    shared.gradio['delete_chat'].click(lambda: [gr.update(visible=True), gr.update(visible=False), gr.update(visible=True)], None, gradio(clear_arr))
    shared.gradio['delete_chat-cancel'].click(lambda: [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)], None, gradio(clear_arr))
    shared.gradio['delete_chat-confirm'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda x, y: str(chat.find_all_histories(x).index(y)), gradio('interface_state', 'unique_id'), gradio('temporary_text')).then(
        chat.delete_history, gradio('unique_id', 'character_menu'), None).then(
        chat.load_history_after_deletion, gradio('interface_state', 'temporary_text'), gradio('history', 'unique_id')).then(
        chat.redraw_html, gradio(reload_arr), None).then(
        lambda: [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)], None, gradio(clear_arr))

    shared.gradio['rename_chat'].click(
        lambda x: x, gradio('unique_id'), gradio('rename_to')).then(
        lambda: [gr.update(visible=True)] * 3, None, gradio('rename_to', 'rename_to-confirm', 'rename_to-cancel'), show_progress=False)

    shared.gradio['rename_to-cancel'].click(
        lambda: [gr.update(visible=False)] * 3, None, gradio('rename_to', 'rename_to-confirm', 'rename_to-cancel'), show_progress=False)

    shared.gradio['rename_to-confirm'].click(
        chat.rename_history, gradio('unique_id', 'rename_to', 'character_menu'), None).then(
        lambda: [gr.update(visible=False)] * 3, None, gradio('rename_to', 'rename_to-confirm', 'rename_to-cancel'), show_progress=False).then(
        lambda x, y: gr.update(choices=chat.find_all_histories(x), value=y), gradio('interface_state', 'rename_to'), gradio('unique_id'))

    shared.gradio['rename_to'].submit(
        chat.rename_history, gradio('unique_id', 'rename_to', 'character_menu'), None).then(
        lambda: [gr.update(visible=False)] * 3, None, gradio('rename_to', 'rename_to-confirm', 'rename_to-cancel'), show_progress=False).then(
        lambda x, y: gr.update(choices=chat.find_all_histories(x), value=y), gradio('interface_state', 'rename_to'), gradio('unique_id'))
#
    shared.gradio['load_chat_history'].upload(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.start_new_chat, gradio('interface_state'), gradio('history')).then(
        chat.load_history_json, gradio('load_chat_history', 'history'), gradio('history')).then(
        chat.redraw_html, gradio(reload_arr), None).then(
        lambda x: gr.update(choices=(histories := chat.find_all_histories(x)), value=histories[0]), gradio('interface_state'), gradio('unique_id')).then(
        chat.save_history, gradio('history', 'unique_id', 'character_menu'), None).then(
        lambda: None, None, None, _js=f'() => {{{ui.switch_tabs_js}; switch_to_chat()}}')

    shared.gradio['character_menu'].change(
        chat.load_character, gradio('character_menu', 'name1', 'name2'), gradio('name1', 'name2', 'character_picture', 'greeting', 'context')).success(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.load_latest_history, gradio('interface_state'), gradio('history')).then(
        chat.redraw_html, gradio(reload_arr), None).then(
        lambda x: gr.update(choices=(histories := chat.find_all_histories(x)), value=histories[0]), gradio('interface_state'), gradio('unique_id')).then(
        lambda: None, None, None, _js=f'() => {{{ui.update_big_picture_js}; updateBigPicture()}}')

    shared.gradio['your_picture'].change(
        chat.upload_your_profile_picture, gradio('your_picture'), None).then(
        partial(chat.redraw_html, reset_cache=True), gradio(reload_arr), None)

    