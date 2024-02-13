from pathlib import Path

import gradio as gr

from modules.html_generator import get_image_cache
from modules.shared import gradio, settings


cards = []


def generate_css():
    css = ""
    return css


def generate_html():
    global cards
    cards = []
    # Iterate through files in image folder
    for file in sorted(Path("characters").glob("*")):
        if file.suffix in [".json", ".yml", ".yaml"]:
            character = file.stem
            container_html = '<div class="character-container">'
            image_html = "<div class='placeholder'></div>"

            for path in [Path(f"characters/{character}.{extension}") for extension in ['png', 'jpg', 'jpeg']]:
                if path.exists():
                    image_html = f'<img src="file/{get_image_cache(path)}">'
                    break

            container_html += f'{image_html} <span class="character-name">{character}</span>'
            container_html += "</div>"
            cards.append([container_html, character])

    return cards


def filter_cards(filter_str=''):
    if filter_str == '':
        return cards

    filter_upper = filter_str.upper()
    return [k for k in cards if filter_upper in k[1].upper()]


def select_character(evt: gr.SelectData):
    return (evt.value[1])


def custom_js():
    path_to_js = Path(__file__).parent.resolve() / 'script.js'
    return open(path_to_js, 'r').read()


def ui():
    with gr.Accordion("Character gallery", open=settings["gallery-open"], elem_id='gallery-extension'):
        gr.HTML(value="<style>" + generate_css() + "</style>")
        with gr.Row():
            filter_box = gr.Textbox(label='', placeholder='Filter', lines=1, max_lines=1, container=False, elem_id='gallery-filter-box')
            gr.ClearButton(filter_box, value='Clear', elem_classes='refresh-button')
            update = gr.Button("Refresh", elem_classes='refresh-button')

        gallery = gr.Dataset(
            components=[gr.HTML(visible=False)],
            label="",
            samples=generate_html(),
            elem_classes=["character-gallery"],
            samples_per_page=settings["gallery-items_per_page"]
        )

    filter_box.change(lambda: None, None, None, _js=f'() => {{{custom_js()}; gotoFirstPage()}}').success(
        filter_cards, filter_box, gallery).then(
        lambda x: gr.update(elem_classes='highlighted-border' if x != '' else ''), filter_box, filter_box, show_progress=False)

    update.click(generate_html, [], None).success(
        filter_cards, filter_box, gallery)

    
    gallery.select(select_character, None, gradio['character_menu'])
