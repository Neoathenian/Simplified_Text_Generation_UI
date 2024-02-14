import json
from functools import partial
from pathlib import Path

import gradio as gr
from PIL import Image
import os
import time
from datetime import datetime

from modules import chat, shared, ui, utils
from modules.html_generator import chat_html_wrapper
from modules.text_generation import stop_everything_event
from modules.utils import gradio
from modules.shared import settings


from modules.script import generate_css,generate_html,filter_cards,custom_js,select_character,cards



inputs = ('Chat input', 'interface_state')
reload_arr = ('Logs', 'name1', 'name2', 'character_menu')# 'mode',, 'chat_style', 'name1', 'name2'
clear_arr = ('delete_chat-confirm', 'delete_chat', 'delete_chat-cancel')


def create_ui():
    mu = shared.args.multi_user

    shared.gradio['Chat input'] = gr.State()
    shared.gradio['Logs'] = gr.State({'internal': [], 'visible': [], "likes":[]})

    with gr.Tab('Chat', elem_id='chat-tab', elem_classes=("old-ui" if shared.args.chat_buttons else None)):
        with gr.Row():
            with gr.Column(elem_id='chat-col'):
                shared.gradio['display'] = gr.HTML(value=chat_html_wrapper({'internal': [], 'visible': []}, '', '', 'chat', ''))
                #shared.gradio['display'] = gr.HTML(value=chat_html_wrapper({'internal': [], 'visible': []}, '', '', 'chat', 'cai-chat', ''))
                with gr.Row(elem_id="chat-input-row"):
                    with gr.Column(scale=1, elem_id='gr-hover-container'):
                        gr.HTML(value='<div class="hover-element" onclick="void(0)"><span style="width: 100px; display: block" id="hover-element-button">&#9776;</span><div class="hover-menu" id="hover-menu"></div>', elem_id='gr-hover')

                    with gr.Column(scale=10, elem_id='chat-input-container'):
                        shared.gradio['textbox'] = gr.Textbox(label='', placeholder='Send a message', elem_id='chat-input', elem_classes=['add_scrollbar'])
                        shared.gradio['show_controls'] = gr.Checkbox(value=shared.settings['show_controls'], label='Show controls (Ctrl+S)', elem_id='show-controls')
                        shared.gradio['typing-dots'] = gr.HTML(value='<div class="typing"><span></span><span class="dot1"></span><span class="dot2"></span></div>', label='typing', elem_id='typing-container')

                    with gr.Column(scale=1, elem_id='generate-stop-container'):
                        with gr.Row():
                            shared.gradio['Stop'] = gr.Button('Stop', elem_id='stop', visible=False)
                            shared.gradio['Generate'] = gr.Button('Generate', elem_id='Generate', variant='primary')

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
                bot, [shared.gradio["chatbot"],shared.gradio["character_menu"],shared.gradio["unique_id"]],
                  shared.gradio["chatbot"], api_name="bot_response"
            )
            txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)
            
            shared.gradio["chatbot"].like(print_like_dislike, gradio('unique_id', 'character_menu'), None)
            
            
            gallery.select(select_character, None, shared.gradio['character_menu'])

        
def create_chat_settings_ui():
    mu = shared.args.multi_user
    with gr.Tab('Character'):
        with gr.Row():
            with gr.Column(scale=8):
                #with gr.Row():
                #    shared.gradio['character_menu'] = gr.Dropdown(value=None, choices=utils.get_available_characters(), label='Character', elem_id='character-menu', info='Used in chat and chat-instruct modes.', elem_classes='slim-dropdown')
#                    ui.create_refresh_button(shared.gradio['character_menu'], lambda: None, lambda: {'choices': utils.get_available_characters()}, 'refresh-button', interactive=not mu)
#                    shared.gradio['save_character'] = gr.Button('💾', elem_classes='refresh-button', interactive=not mu)
#                    shared.gradio['delete_character'] = gr.Button('🗑️', elem_classes='refresh-button', interactive=not mu)
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
    #with gr.Tab('Instruction template'):
    #    with gr.Row():
    #        with gr.Column():
    #            with gr.Row():
    #                shared.gradio['instruction_template'] = gr.Dropdown(choices=utils.get_available_instruction_templates(), label='Saved instruction templates', value='Select template to load...', elem_classes='slim-dropdown')
    #                ui.create_refresh_button(shared.gradio['instruction_template'], lambda: None, lambda: {'choices': utils.get_available_instruction_templates()}, 'refresh-button', interactive=not mu)
    #                shared.gradio['load_template'] = gr.Button("Load", elem_classes='refresh-button')
    #                shared.gradio['save_template'] = gr.Button('💾', elem_classes='refresh-button', interactive=not mu)
    #                shared.gradio['delete_template'] = gr.Button('🗑️ ', elem_classes='refresh-button', interactive=not mu)
#
    #        with gr.Column():
    #            pass
#
        #with gr.Row():
            #with gr.Column():
            #    shared.gradio['custom_system_message'] = gr.Textbox(value=shared.settings['custom_system_message'], lines=2, label='Custom system message', info='If not empty, will be used instead of the default one.', elem_classes=['add_scrollbar'])
            #    shared.gradio['instruction_template_str'] = gr.Textbox(value='', label='Instruction template', lines=24, info='Change this according to the model/LoRA that you are using. Used in instruct and chat-instruct modes.', elem_classes=['add_scrollbar', 'monospace'])
    #            with gr.Row():
    #                shared.gradio['send_instruction_to_default'] = gr.Button('Send to default', elem_classes=['small-button'])
    #                shared.gradio['send_instruction_to_notebook'] = gr.Button('Send to notebook', elem_classes=['small-button'])
    #                shared.gradio['send_instruction_to_negative_prompt'] = gr.Button('Send to negative prompt', elem_classes=['small-button'])
#
            #with gr.Column():
            #    shared.gradio['chat_template_str'] = gr.Textbox(value=shared.settings['chat_template_str'], label='Chat template', lines=22, elem_classes=['add_scrollbar', 'monospace'])
            #    shared.gradio['chat-instruct_command'] = gr.Textbox(value=shared.settings['chat-instruct_command'], lines=4, label='Command for chat-instruct mode', info='<|character|> gets replaced by the bot name, and <|prompt|> gets replaced by the regular chat prompt.', elem_classes=['add_scrollbar'])
#
    #with gr.Tab('Chat history'):
    #    with gr.Row():
    #        with gr.Column():
    #            shared.gradio['save_chat_history'] = gr.Button(value='Save history')
#
            with gr.Column():
                shared.gradio['load_chat_history'] = gr.File(type='binary', file_types=['.json', '.txt'], label='Upload History JSON')
#
    #with gr.Tab('Upload character'):
    #    with gr.Tab('YAML or JSON'):
    #        with gr.Row():
    #            shared.gradio['upload_json'] = gr.File(type='binary', file_types=['.json', '.yaml'], label='JSON or YAML File', interactive=not mu)
    #            shared.gradio['upload_img_bot'] = gr.Image(type='pil', label='Profile Picture (optional)', interactive=not mu)
#
    #        shared.gradio['Submit character'] = gr.Button(value='Submit', interactive=False)
#
    #    with gr.Tab('TavernAI PNG'):
    #        with gr.Row():
    #            with gr.Column():
    #                shared.gradio['upload_img_tavern'] = gr.Image(type='pil', label='TavernAI PNG File', elem_id='upload_img_tavern', interactive=not mu)
    #                shared.gradio['tavern_json'] = gr.State()
    #            with gr.Column():
    #                shared.gradio['tavern_name'] = gr.Textbox(value='', lines=1, label='Name', interactive=False)
    #                shared.gradio['tavern_desc'] = gr.Textbox(value='', lines=4, max_lines=4, label='Description', interactive=False)
#
    #        shared.gradio['Submit tavern character'] = gr.Button(value='Submit', interactive=False)



def create_event_handlers():

    # Obsolete variables, kept for compatibility with old extensions
    shared.input_params = gradio(inputs)
    shared.reload_inputs = gradio(reload_arr)

    shared.gradio['Generate'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda x: (x, ''), gradio('textbox'), gradio('Chat input', 'textbox'), show_progress=False).then(
        chat.generate_chat_reply_wrapper, gradio(inputs), gradio('display', 'history'), show_progress=False).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.save_history, gradio('history', 'unique_id', 'character_menu'), None).then(
        lambda: None, None, None, _js=f'() => {{{ui.audio_notification_js}}}')

    shared.gradio['textbox'].submit(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda x: (x, ''), gradio('textbox'), gradio('Chat input', 'textbox'), show_progress=False).then(
        chat.generate_chat_reply_wrapper, gradio(inputs), gradio('display', 'history'), show_progress=False).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.save_history, gradio('history', 'unique_id', 'character_menu'), None).then(
        lambda: None, None, None, _js=f'() => {{{ui.audio_notification_js}}}')

    shared.gradio['Regenerate'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        partial(chat.generate_chat_reply_wrapper, regenerate=True), gradio(inputs), gradio('display', 'history'), show_progress=False).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.save_history, gradio('history', 'unique_id', 'character_menu'), None).then(
        lambda: None, None, None, _js=f'() => {{{ui.audio_notification_js}}}')

    shared.gradio['Continue'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        partial(chat.generate_chat_reply_wrapper, _continue=True), gradio(inputs), gradio('display', 'history'), show_progress=False).then(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.save_history, gradio('history', 'unique_id', 'character_menu'), None).then(
        lambda: None, None, None, _js=f'() => {{{ui.audio_notification_js}}}')

    shared.gradio['Replace last reply'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.replace_last_reply, gradio('textbox', 'interface_state'), gradio('history')).then(
        lambda: '', None, gradio('textbox'), show_progress=False).then(
        chat.redraw_html, gradio(reload_arr), gradio('display')).then(
        chat.save_history, gradio('history', 'unique_id', 'character_menu'), None)

    shared.gradio['Remove last'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.remove_last_message, gradio('history'), gradio('textbox', 'history'), show_progress=False).then(
        chat.redraw_html, gradio(reload_arr), gradio('display')).then(
        chat.save_history, gradio('history', 'unique_id', 'character_menu'), None)

    shared.gradio['Stop'].click(
        stop_everything_event, None, None, queue=False).then(
        chat.redraw_html, gradio(reload_arr), gradio('display'))

    if not shared.args.multi_user:
        shared.gradio['unique_id'].select(
            chat.load_history, gradio('unique_id', 'character_menu'), gradio('history')).then(
            chat.redraw_html, gradio(reload_arr), gradio('display'))

    shared.gradio['Start new chat'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.start_new_chat, gradio('interface_state'), gradio('history')).then(
        chat.redraw_html, gradio(reload_arr), gradio('display')).then(
        lambda x: gr.update(choices=(histories := chat.find_all_histories(x)), value=histories[0]), gradio('interface_state'), gradio('unique_id'))

    shared.gradio['delete_chat'].click(lambda: [gr.update(visible=True), gr.update(visible=False), gr.update(visible=True)], None, gradio(clear_arr))
    shared.gradio['delete_chat-cancel'].click(lambda: [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)], None, gradio(clear_arr))
    shared.gradio['delete_chat-confirm'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda x, y: str(chat.find_all_histories(x).index(y)), gradio('interface_state', 'unique_id'), gradio('temporary_text')).then(
        chat.delete_history, gradio('unique_id', 'character_menu'), None).then(
<<<<<<< HEAD
        chat.load_history_after_deletion, gradio('interface_state', 'temporary_text'), gradio('unique_id')).then(
        #chat.redraw_html, gradio(reload_arr), None).then(
=======
        chat.load_history_after_deletion, gradio('interface_state', 'temporary_text'), gradio('history', 'unique_id')).then(
        chat.redraw_html, gradio(reload_arr), gradio('display')).then(
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
<<<<<<< HEAD
        chat.load_history_json, gradio('load_chat_history'),shared.gradio["chatbot"]).then(
        #chat.New_chat, gradio('interface_state'), shared.gradio["chatbot"]).then(
        #chat.redraw_html, gradio(reload_arr), None).then(
=======
        chat.start_new_chat, gradio('interface_state'), gradio('history')).then(
        chat.load_history_json, gradio('load_chat_history', 'history'), gradio('history')).then(
        chat.redraw_html, gradio(reload_arr), gradio('display')).then(
        lambda x: gr.update(choices=(histories := chat.find_all_histories(x)), value=histories[0]), gradio('interface_state'), gradio('unique_id')).then(
        chat.save_history, gradio('Logs', 'unique_id', 'character_menu'), None).then(
        lambda: None, None, None, _js=f'() => {{{ui.switch_tabs_js}; switch_to_chat()}}')

    shared.gradio['character_menu'].change(
        chat.load_character, gradio('character_menu', 'name1', 'name2'), gradio('name1', 'name2', 'character_picture', 'greeting', 'context')).success(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
<<<<<<< HEAD
        chat.load_latest_history, gradio('interface_state'),None).then(
        #chat.redraw_html, gradio(reload_arr), None).then(
=======
        chat.load_latest_history, gradio('interface_state'), gradio('history')).then(
        chat.redraw_html, gradio(reload_arr), gradio('display')).then(
        lambda x: gr.update(choices=(histories := chat.find_all_histories(x)), value=histories[0]), gradio('interface_state'), gradio('unique_id')).then(
        lambda: None, None, None, _js=f'() => {{{ui.update_big_picture_js}; updateBigPicture()}}')

<<<<<<< HEAD
    #shared.gradio['your_picture'].change(
    #    chat.upload_your_profile_picture, gradio('your_picture'), None)#.then(
        #partial(chat.redraw_html, reset_cache=True), gradio(reload_arr), None)

    
=======
#    shared.gradio['load_template'].click(
#        chat.load_instruction_template, gradio('instruction_template'), gradio('instruction_template_str')).then(
#        lambda: "Select template to load...", None, gradio('instruction_template'))
#
#    shared.gradio['save_template'].click(
#        lambda: 'My Template.yaml', None, gradio('save_filename')).then(
#        lambda: 'instruction-templates/', None, gradio('save_root')).then(
#        chat.generate_instruction_template_yaml, gradio('instruction_template_str'), gradio('save_contents')).then(
#        lambda: gr.update(visible=True), None, gradio('file_saver'))
#
#    shared.gradio['delete_template'].click(
#        lambda x: f'{x}.yaml', gradio('instruction_template'), gradio('delete_filename')).then(
#        lambda: 'instruction-templates/', None, gradio('delete_root')).then(
#        lambda: gr.update(visible=True), None, gradio('file_deleter'))
#
#    shared.gradio['save_chat_history'].click(
#        lambda x: json.dumps(x, indent=4), gradio('history'), gradio('temporary_text')).then(
#        None, gradio('temporary_text', 'character_menu'), None, _js=f'(hist, char, mode) => {{{ui.save_files_js}; saveHistory(hist, char, mode)}}')
#
#    shared.gradio['Submit character'].click(
#        chat.upload_character, gradio('upload_json', 'upload_img_bot'), gradio('character_menu')).then(
#        lambda: None, None, None, _js=f'() => {{{ui.switch_tabs_js}; switch_to_character()}}')
#
#    shared.gradio['Submit tavern character'].click(
#        chat.upload_tavern_character, gradio('upload_img_tavern', 'tavern_json'), gradio('character_menu')).then(
#        lambda: None, None, None, _js=f'() => {{{ui.switch_tabs_js}; switch_to_character()}}')
#
#    shared.gradio['upload_json'].upload(lambda: gr.update(interactive=True), None, gradio('Submit character'))
#    shared.gradio['upload_json'].clear(lambda: gr.update(interactive=False), None, gradio('Submit character'))
#    shared.gradio['upload_img_tavern'].upload(chat.check_tavern_character, gradio('upload_img_tavern'), gradio('tavern_name', 'tavern_desc', 'tavern_json', 'Submit tavern character'), show_progress=False)
#    shared.gradio['upload_img_tavern'].clear(lambda: (None, None, None, gr.update(interactive=False)), None, gradio('tavern_name', 'tavern_desc', 'tavern_json', 'Submit tavern character'), show_progress=False)
    shared.gradio['your_picture'].change(
        chat.upload_your_profile_picture, gradio('your_picture'), None).then(
        partial(chat.redraw_html, reset_cache=True), gradio(reload_arr), gradio('display'))

    #shared.gradio['send_instruction_to_negative_prompt'].click(
    #    ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #    lambda x: x.update({'mode': 'instruct', 'history': {'internal': [], 'visible': []}}), gradio('interface_state'), None).then(
    #    partial(chat.generate_chat_prompt, 'Input'), gradio('interface_state'), gradio('negative_prompt')).then(
    #    lambda: None, None, None, _js=f'() => {{{ui.switch_tabs_js}; switch_to_generation_parameters()}}')

    shared.gradio['show_controls'].change(None, gradio('show_controls'), None, _js=f'(x) => {{{ui.show_controls_js}; toggle_controls(x)}}')
