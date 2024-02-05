import copy
from pathlib import Path

import gradio as gr
import yaml

import extensions
from modules import shared

with open(Path(__file__).resolve().parent / '../css/NotoSans/stylesheet.css', 'r') as f:
    css = f.read()
with open(Path(__file__).resolve().parent / '../css/main.css', 'r') as f:
    css += f.read()
with open(Path(__file__).resolve().parent / '../js/main.js', 'r') as f:
    js = f.read()
with open(Path(__file__).resolve().parent / '../js/save_files.js', 'r') as f:
    save_files_js = f.read()
with open(Path(__file__).resolve().parent / '../js/switch_tabs.js', 'r') as f:
    switch_tabs_js = f.read()
with open(Path(__file__).resolve().parent / '../js/show_controls.js', 'r') as f:
    show_controls_js = f.read()
with open(Path(__file__).resolve().parent / '../js/update_big_picture.js', 'r') as f:
    update_big_picture_js = f.read()

refresh_symbol = '🔄'
delete_symbol = '🗑️'
save_symbol = '💾'

theme = gr.themes.Default(
    font=['Noto Sans', 'Helvetica', 'ui-sans-serif', 'system-ui', 'sans-serif'],
    font_mono=['IBM Plex Mono', 'ui-monospace', 'Consolas', 'monospace'],
).set(
    border_color_primary='#c5c5d2',
    button_large_padding='6px 12px',
    body_text_color_subdued='#484848',
    background_fill_secondary='#eaeaea'
)

if Path("notification.mp3").exists():
    audio_notification_js = "document.querySelector('#audio_notification audio')?.play();"
else:
    audio_notification_js = ""


def list_interface_input_elements():
    elements = [
        #'max_new_tokens',
        #'auto_max_new_tokens',
        #'max_tokens_second',
        #'max_updates_second',
        #'prompt_lookup_num_tokens',
        #'seed',
        #'temperature',
        #'temperature_last',
        #'dynamic_temperature',
        #'dynatemp_low',
        #'dynatemp_high',
        #'dynatemp_exponent',
        #'top_p',
        #'min_p',
        #'top_k',
        #'typical_p',
        #'epsilon_cutoff',
        #'eta_cutoff',
        #'repetition_penalty',
        #'presence_penalty',
        #'frequency_penalty',
        #'repetition_penalty_range',
        #'encoder_repetition_penalty',
        #'no_repeat_ngram_size',
        #'min_length',
        #'do_sample',
        #'penalty_alpha',
        #'num_beams',
        #'length_penalty',
        #'early_stopping',
        #'mirostat_mode',
        #'mirostat_tau',
        #'mirostat_eta',
        #'grammar_string',
        #'negative_prompt',
        #'guidance_scale',
        #'add_bos_token',
        #'ban_eos_token',
        #'custom_token_bans',
        #'truncation_length',
        #'custom_stopping_strings',
        #'skip_special_tokens',
        #'stream',
        #'tfs',
        #'top_a',
    ]

    # Chat elements
    elements += [
        'textbox',
        #'start_with',
        'character_menu',
        'history',
        'name1',
        'name2',
        'greeting',
        #'context',
        #'mode',
        #'custom_system_message',
        #'instruction_template_str',
        #'chat_template_str',
        #'chat_style',
        #'chat-instruct_command',
    ]

    return elements


def gather_interface_values(*args):
    output = {}
    for i, element in enumerate(list_interface_input_elements()):
        output[element] = args[i]

    if not shared.args.multi_user:
        shared.persistent_interface_state = output

    return output


def apply_interface_values(state, use_persistent=False):
    if use_persistent:
        state = shared.persistent_interface_state

    elements = list_interface_input_elements()
    if len(state) == 0:
        return [gr.update() for k in elements]  # Dummy, do nothing
    else:
        return [state[k] if k in state else gr.update() for k in elements]


def create_refresh_button(refresh_component, refresh_method, refreshed_args, elem_class, interactive=True):
    """
    Copied from https://github.com/AUTOMATIC1111/stable-diffusion-webui
    """
    def refresh():
        refresh_method()
        args = refreshed_args() if callable(refreshed_args) else refreshed_args

        return gr.update(**(args or {}))

    refresh_button = gr.Button(refresh_symbol, elem_classes=elem_class, interactive=interactive)
    refresh_button.click(
        fn=lambda: {k: tuple(v) if type(k) is list else v for k, v in refresh().items()},
        inputs=[],
        outputs=[refresh_component]
    )

    return refresh_button
