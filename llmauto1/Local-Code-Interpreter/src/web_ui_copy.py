import gradio as gr
import tiff
from response_parser import *
from core import initialization, get_bot_backend, switch_model, add_text, bot
from functools import lru_cache
import time
from config import get_config, CONFIG
import asyncio
import sys
import os
from typing import Dict, List, Tuple
import copy
import openai
from PIL import Image
import logging
from datetime import datetime
import numpy as np
import re

logging.basicConfig(level=logging.DEBUG, 
                    filename='app1.log', 
                    filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@lru_cache(maxsize=1000)
def count_tokens(text: str, model: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def initialization(state_dict: Dict) -> None:
    #state["current_model"] = "GPT-4"
    if not os.path.exists('cache'):
        os.mkdir('cache')
    if state_dict["bot_backend"] is None:
        state_dict["bot_backend"] = BotBackend()
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']


# def get_bot_backend(state_dict: Dict) -> BotBackend:
#     return state_dict["bot_backend"]
def get_bot_backend(state_dict: Dict) -> BotBackend:
    if state_dict.get("bot_backend") is None:
        state_dict["bot_backend"] = BotBackend()
    logging.info("GET BOTBACKEND")
    return state_dict["bot_backend"]



def switch_to_deepseeker(state_dict: Dict, whether_switch: bool) -> None:
    bot_backend = get_bot_backend(state_dict)
    if whether_switch:
        bot_backend.update_gpt_model_choice("GPT-4o")
    else:
        bot_backend.update_gpt_model_choice("GPT-4")


def add_text(state_dict: Dict, history: List, text: str) -> Tuple[List, Dict]:
    logging.info(f"Received user input: {text}")
    if not text or not text.strip():
        logging.warning("Empty input received")
        return history, gr.update(value="", interactive=True)
    
    try:
        bot_backend = get_bot_backend(state_dict)
        bot_backend.add_text_message(user_text=text)
        
        history = history + [(text, None)]
        logging.info("User input processed successfully")
        logging.info(f"debug!!!!{bot_backend.conversation}")
        return history, gr.update(value="", interactive=False)
    except Exception as e:
        logging.error(f"Error processing user input: {str(e)}")
        return history, gr.update(value="", interactive=True)

def add_file(state_dict: Dict, history: List, files) -> List:
    bot_backend = get_bot_backend(state_dict)
    for file in files:
        path = file.name
        filename = os.path.basename(path)

        bot_msg = [f'📁[{filename}]', None]
        history.append(bot_msg)
        bot_backend.add_file_message(path=path, bot_msg=bot_msg)
        #普通图像直接显示缩略图
        _, suffix = os.path.splitext(filename)
        if suffix in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}:
            copied_file_path = f'{bot_backend.jupyter_work_dir}/{filename}'
            width, height = get_image_size(copied_file_path)
            bot_msg[0] += \
                f'\n<img src=\"file={copied_file_path}\" style=\'{"" if width < 800 else "width: 800px;"} max-width' \
                f':none; max-height:none\'> '
            #tif图像显示二维mip缩略图
        elif suffix == '.tif':
        # 读取tif图像并计算MIP
            with tiff.TiffFile(path) as tif:
                image_data = tif.asarray()
                mip = image_data.max(axis=0)
                mip_image = Image.fromarray(mip)
                # 创建缩略图路径
                thumbnail_path = f'{bot_backend.jupyter_work_dir}/{os.path.splitext(filename)[0]}_mip_thumbnail.png'
                mip_image.save(thumbnail_path)

                width, height = get_image_size(thumbnail_path)
                bot_msg[0] += \
                    f'\n<img src=\"file={thumbnail_path}\" style=\'{"" if width < 800 else "width: 800px;"} max-width' \
                    f':none; max-height:none\'> '

    return history


def undo_upload_file(state_dict: Dict, history: List) -> Tuple[List, Dict]:
    bot_backend = get_bot_backend(state_dict)
    bot_msg = bot_backend.revoke_file()

    if bot_msg is None:
        return history, gr.Button(interactive=False)

    else:
        assert history[-1] == bot_msg
        del history[-1]
        if bot_backend.revocable_files:
            return history, gr.Button(interactive=True)
        else:
            return history, gr.Button(interactive=False)


def refresh_file_display(state_dict: Dict) -> List[str]:
    bot_backend = get_bot_backend(state_dict)
    work_dir = bot_backend.jupyter_work_dir
    filenames = os.listdir(work_dir)
    paths = []
    for filename in filenames:
        path = os.path.join(work_dir, filename)
        if not os.path.isdir(path):
            paths.append(path)
    return paths


def refresh_token_count(state_dict: Dict):
    bot_backend = get_bot_backend(state_dict)
    if bot_backend is None:
        return "**错误：Bot后端未初始化**"
    
    total_tokens = bot_backend.get_total_tokens()
    model_choice = bot_backend.get_current_model()
    sliced = bot_backend.sliced
    token_count = bot_backend.context_window_tokens
    token_limit = CONFIG['model_context_window'][CONFIG['model'][model_choice]['model_name']]
    display_text = f"**Context token:** {token_count}/{token_limit}"
    if sliced:
        display_text += '\n\nToken limit exceeded, conversation has been sliced.'
    return display_text


def restart_ui(history: List) -> Tuple[List, Dict, Dict, Dict, Dict, Dict, Dict,Dict]:
    history.clear()
    return (
        history,
        gr.Textbox(value="", interactive=False),
        gr.Button(interactive=False),
        gr.Button(interactive=False),
        gr.Button(interactive=False),
        gr.Button(interactive=False),
        gr.Button(interactive=False),
        gr.Button(visible=False)
    )


def restart_bot_backend(state_dict: Dict) -> None:
    bot_backend = get_bot_backend(state_dict)
    bot_backend.restart()


def stop_generating(state_dict: Dict) -> None:
    bot_backend = get_bot_backend(state_dict)
    if bot_backend.code_executing:
        bot_backend.send_interrupt_signal()
    else:
        bot_backend.update_stop_generating_state(stop_generating=True)


def bot(state_dict: Dict, history: List, progress=gr.Progress()) -> List:
    bot_backend = get_bot_backend(state_dict)
    start_time = datetime.now()

    while bot_backend.finish_reason in ('new_input', 'function_call'):
        if history[-1][1]:
            history.append([None, ""])
        else:
            history[-1][1] = ""

        try:
            response = chat_completion(bot_backend=bot_backend)
            for i, chunk in enumerate(progress.tqdm(response)):
                if chunk['choices'] and chunk['choices'][0]['finish_reason'] == 'function_call':
                    if bot_backend.function_name in bot_backend.jupyter_kernel.available_functions:
                        yield history, gr.Button(value='⏹️ Interrupt execution'), gr.Button(visible=False)
                    else:
                        yield history, gr.Button(interactive=False), gr.Button(visible=False)

                if bot_backend.stop_generating:
                    response.close()
                    if bot_backend.content:
                        bot_backend.add_gpt_response_content_message()
                    if bot_backend.display_code_block:
                        bot_backend.update_display_code_block(
                            display_code_block="\n⚫Stopped:\n```python\n{}\n```".format(bot_backend.code_str)
                        )
                        history = copy.deepcopy(bot_backend.bot_history)
                        history[-1][1] += bot_backend.display_code_block
                        bot_backend.add_function_call_response_message(function_response=None)

                    bot_backend.reset_gpt_response_log_values()
                    break

                history, whether_exit = parse_response(
                    chunk=chunk,
                    history=history,
                    bot_backend=bot_backend
                )

                yield (
                    history,
                    gr.Button(
                        interactive=False if bot_backend.stop_generating else True,
                        value='⏹️ Stop generating'
                    ),
                    gr.Button(visible=False)
                )
                if whether_exit:
                    exit(-1)

                # Simulate progress
                # progress(i/10, desc="Processing")
                # time.sleep(0.1)

        except openai.OpenAIError as openai_error:
            bot_backend.reset_gpt_response_log_values(exclude=['finish_reason'])
            yield history, gr.Button(interactive=False), gr.Button(visible=True)
            raise openai_error

    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    bot_backend.logger.log_execution_time(execution_time)
    yield history, gr.Button(interactive=False, value='⏹️ Stop generating'), gr.Button(visible=False)
    # end_time = datetime.now()
    # execution_time = (end_time - start_time).total_seconds()
    # bot_backend.logger.log_execution_time(execution_time)
    # yield history, gr.Button(interactive=False, value='⏹️ Stop generating'), gr.Button(visible=False)


def switch_model(state_dict: Dict, use_gpt4: bool) -> str:
    bot_backend = get_bot_backend(state_dict)
    model = "GPT-4" if use_gpt4 else "GPT-4o"
    bot_backend.update_gpt_model_choice(model)
    return f"Current model: {model}"
# def switch_model(state, use_gpt4):
#     if use_gpt4:
#         state["current_model"] = "GPT-4"
#     else:
#         state["current_model"] = "GPT-3.5"
#     return state["current_model"]

ini_task_msg='''You are a task-solving planner.Your task is to create a detailed task-solving plan for user_input. 
Your approach should be divided into the following three sections:
    1.Task Objectives and Functional Description: Clearly articulate the overall objectives, functional requirements, and expected outcomes of the task.
    2.Algorithm Steps and Implementation Details: Provide a step-by-step description of the specific algorithms required to accomplish the task, including methods and technical details for each step.
    3.Specific Constraints: List any specific constraints or conditions that need to be considered during implementation, such as computational resources, time complexity, accuracy requirements, etc.
Note:You do not need to write specific code, just provide a detailed plan and thought process.Return in bullet point and no extra content.
'''
def txt_prompt_process(user_input_ini):
    llm_prompt = f'user_input: {user_input_ini} \n{ini_task_msg}'
    return llm_prompt

def txt_response_process(content):
    txt1 = content.split("###")
    ct1 = txt1[1]
    ct2 = txt1[2]
    ct3 = txt1[3]
    return ct1, ct2, ct3

# def code_prompt_process(prompt2, option):
#     code_prompt = prompt2 + f'进行基于{option}的脚本撰写","仅返回完整脚本，以"###"标记脚本结束,示例用法以"example"作为标记开始"'
#     return str(code_prompt)

def get_llm_text(state_dict: Dict,question: str):
    config = CONFIG
    openai.api_base = get_config('API_base')
    openai.api_key = get_config('API_KEY')
    question = txt_prompt_process(question)
    model = config['model']['GPT-4o']['model_name']
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            # {'role': 'system', 'content': "You are an expert majored in neuroscience and excellently good at analysing and schduleing plans according to relevant and confirmed theroratical supoort"},
            {'role': 'user', 'content': question}
        ],
        temperature=0,
        stream=True
    )

    full_reply_content = ''
    for chunk in response:
        message = chunk["choices"][0]["delta"].get("content", "")
        full_reply_content += message

    ct1, ct2, ct3 = txt_response_process(full_reply_content)
    logging.info(f"user_input: {question}\nfully_task_response: {full_reply_content}\nct1: {ct1}\n ct2: {ct2}\n ct3: {ct3}")
    
    return ct1, ct2, ct3

def switch_to_chat():
    return gr.update()


# def code_extract(question: str):
#     config = CONFIG
#     model = config['model']['GPT-4o']['model_name']
#     response = openai.ChatCompletion.create(
#         model=model,
#         messages=[
#             {'role': 'user', 'content': question}
#         ],
#         temperature=0,
#         stream=True
#     )

#     full_reply_content = ''
#     for chunk in response:
#         message = chunk["choices"][0]["delta"].get("content", "")
#         full_reply_content += message

#     code_blocks = re.findall(r'```(.*?)```', full_reply_content, re.DOTALL)
#     if code_blocks:
#         code = code_blocks[0]
#         language, script = code.split("\n", 1)
#         script = script.strip()
#         example = re.findall(r'example(.*?)$', full_reply_content, re.DOTALL)
#         example = example[0] if example else ""
#         return full_reply_content, language, script, example
#     else:
#         return full_reply_content, "", "", ""

# def edit_text(txt1, txt2, txt3, option):
#     merged_text = f'{txt1}\n{txt2}\n{txt3},进行基于{option}的脚本撰写","注意：1/仅返回完整脚本，以"###"标记脚本结束,2/给出示例用法,以"example"作为标记开始"'
#     txt4, lan, script, eg = code_extract(merged_text)
#     script = "'''\n" + script + "'''\n"
#     return txt4, lan, script, eg
def get_image_size(file_path):
    with Image.open(file_path) as img:
        return img.size


if __name__ == '__main__':
    try:
        config = CONFIG
        if not config:
            print("警告：无法加载配置。使用默认值。")
            logging.warning("警告：无法加载配置。使用默认值。")
            # config = {
            #     'model': {
            #         'GPT-3.5': {'available': True, 'model_name': 'gpt-3.5-turbo-0613'},
            #         'GPT-4': {'available': True, 'model_name': 'gpt-4-0613'}
            #     },
            #     'model_context_window': {
            #         'gpt-3.5-turbo-0613': 4096,
            #         'gpt-4-0613': 8192
            #     }
            # }
        with gr.Blocks(theme=gr.themes.Base()) as block:
            gr.HTML("""
        <style>
        #generate_plan_btn, #generate_code_btn {
            background-color: orange;
            color: black; /* 设置文字颜色 */
        }
        </style>
        """
    )
            gr.HTML(
                """
                <script>
                function switchTab() {
                    let chatTab = document.querySelector('button[title="Chat"]');
                    if (chatTab) {
                        chatTab.click();
                    }
                }
                </script>
                """
            )
            # UI components
            state = gr.State(value={"bot_backend": None, "current_model": "GPT-4"})
            
            gr.Markdown("")
            gr.Markdown(
        """
        <h1 style='text-align: center; font-size: 3em;'>😊Auto-llM Chatbot Interface</h1>
        """
    )
            
            with gr.Tab("Task Initialization") as task_tab:
                gr.Markdown("### Define and Generate Task Plan###")

                # 任务描述行
                with gr.Row(equal_height=True, spacing=10):
                    task_input = gr.Textbox(label="Task Description", lines=3)
                generate_plan_btn = gr.Button("✨Generate Task Plan",elem_id="generate_plan_btn")
                
                # 目标和约束部分
                gr.Markdown("### Task Details")
                with gr.Row(equal_height=True, spacing=10):
                    task_goal = gr.Textbox(label="Task Goal", lines=3)
                    algorithm_steps = gr.Textbox(label="Algorithm Steps", lines=3)
                    constraints = gr.Textbox(label="Constraints", lines=3)
                
                # 代码生成部分
                gr.Markdown("### Code Generation")
                with gr.Row(equal_height=True, spacing=10):
                    code_language = gr.Dropdown(["Python", "JavaScript", "Java", "C++"], label="Code Language", value="Python")
                    generate_code_btn = gr.Button("🚀Start ！",elem_id="generate_code_btn")
            
            with gr.Tab("Chat") as chat_tab:
                gr.Markdown("### Chat and Code iteration###")
                chatbot = gr.Chatbot([], elem_id="chatbot", label="Auto-LLM", height=750)
                #输入行
                with gr.Row():
                    #request query input
                    with gr.Column(scale=0.85):
                        text_box = gr.Textbox(
                            show_label=False,
                            placeholder="Enter text and press enter, or upload a file",
                            container=False
                        )
                    with gr.Column(scale=0.10, min_width=0):
                        text_upload_button = gr.Button(value='✔️Send')
                    with gr.Column(scale=0.15, min_width=0):
                        file_upload_button = gr.UploadButton("📁", file_count='multiple', file_types=['file'])
                #功能按钮行
                with gr.Row(equal_height=True):
                    with gr.Column(scale=0.15, min_width=0):
                        model_choice = gr.Checkbox(label="Use GPT-4", value=False)
                        model_switch_btn = gr.Button("Switch Model")
                        model_status = gr.Textbox(label="Current Model", value="GPT-4", interactive=False)
                    with gr.Column(scale=0.314, min_width=0):
                        model_token_limit = config['model_context_window'][config['model']['GPT-4']['model_name']]
                        token_count_display_text = f"**Context token:** 0/{model_token_limit}"
                        token_monitor = gr.Markdown(value=token_count_display_text)
                    with gr.Column(scale=0.15, min_width=0):
                        retry_button = gr.Button(value='🔂OpenAI Error, click here to retry', visible=False)
                    with gr.Column(scale=0.15, min_width=0):
                        stop_generation_button = gr.Button(value='⏹️ Stop generating', interactive=False)
                    with gr.Column(scale=0.15, min_width=0):
                        restart_button = gr.Button(value='🔄 Restart')
                    with gr.Column(scale=0.15, min_width=0):
                        undo_file_button = gr.Button(value="↩️Undo upload file", interactive=False)

            with gr.Tab("Files") as file_tab:
                gr.Markdown("###check and download your files###")
                file_output = gr.Files()

            # Components function binding
            generate_plan_btn.click(
                fn=get_llm_text,
                inputs=[task_input],
                outputs=[task_goal, algorithm_steps, constraints]
            )

            # generate_code_btn.click(
            #     # fn=edit_text,
            #     # inputs=[task_goal, algorithm_steps, constraints, code_language],
            #     #outputs=[code_output]
            # ).then(
            #     lambda: gr.Tabs(selected="Chat"),  # 添加这一行来切换到Chat标签页
            #     inputs=None,
            #     outputs=gr.Tabs()
            # )
            generate_code_btn.click(switch_to_chat, None, None).then(lambda: gr.HTML('<script>switchTab();</script>'))


            txt_msg = text_box.submit(add_text, [state, chatbot, text_box], [chatbot, text_box], queue=False).then(
                lambda: gr.Button(interactive=False), None, [undo_file_button], queue=False
            ).then(
                bot, [state, chatbot], [chatbot, stop_generation_button, retry_button]
            )
            txt_msg.then(fn=refresh_file_display, inputs=[state], outputs=[file_output])
            txt_msg.then(lambda: gr.update(interactive=True), None, [text_box], queue=False)
            txt_msg.then(fn=refresh_token_count, inputs=[state], outputs=[token_monitor])
            text_upload_button.click(
                add_text, [state, chatbot, text_box], [chatbot, text_box], queue=False
            ).then(
                lambda: gr.Button(interactive=False), None, [undo_file_button], queue=False
            ).then(
                bot, [state, chatbot], [chatbot, stop_generation_button, retry_button]
            ).then(
                fn=refresh_file_display, inputs=[state], outputs=[file_output]
            ).then(
                lambda: gr.update(interactive=True), None, [text_box], queue=False
            ).then(
                fn=refresh_token_count, inputs=[state], outputs=[token_monitor]
            )

            retry_button.click(lambda: gr.Button(visible=False), None, [retry_button], queue=False).then(
                bot, [state, chatbot], [chatbot, stop_generation_button, retry_button]
            ).then(
                fn=refresh_file_display, inputs=[state], outputs=[file_output]
            ).then(
                lambda: gr.update(interactive=True), None, [text_box], queue=False
            ).then(
                fn=refresh_token_count, inputs=[state], outputs=[token_monitor]
            )

            file_msg = file_upload_button.upload(
                add_file, [state, chatbot, file_upload_button], [chatbot], queue=False
            )
            file_msg.then(lambda: gr.Button(interactive=True), None, [undo_file_button], queue=False)
            file_msg.then(fn=refresh_file_display, inputs=[state], outputs=[file_output])

            undo_file_button.click(
                fn=undo_upload_file, inputs=[state, chatbot], outputs=[chatbot, undo_file_button]
            ).then(
                fn=refresh_file_display, inputs=[state], outputs=[file_output]
            )

            stop_generation_button.click(fn=stop_generating, inputs=[state], queue=False).then(
                fn=lambda: gr.Button(interactive=False), inputs=None, outputs=[stop_generation_button], queue=False
            )

            restart_button.click(
                fn=restart_ui, inputs=[chatbot],
                outputs=[
                    chatbot, text_box, restart_button, file_upload_button, undo_file_button, stop_generation_button,
                    retry_button
                ]
            ).then(
                fn=restart_bot_backend, inputs=[state], queue=False
            ).then(
                fn=refresh_file_display, inputs=[state], outputs=[file_output]
            ).then(
                fn=lambda: (gr.Textbox(interactive=True), gr.Button(interactive=True),
                            gr.Button(interactive=True)),
                inputs=None, outputs=[text_box, restart_button, file_upload_button], queue=False
            ).then(
                fn=refresh_token_count,
                inputs=[state], outputs=[token_monitor]
            )

            model_switch_btn.click(
                fn=switch_model,
                inputs=[state, model_choice],
                outputs=[model_status]
            ).then(
                fn=refresh_token_count,
                inputs=[state],
                outputs=[token_monitor]
            )
            

            block.load(fn=initialization, inputs=[state])

        block.queue()
        block.launch(inbrowser=True)
    except Exception as e:
        logging.exception("An error occurred during initialization: %s", str(e))
        raise