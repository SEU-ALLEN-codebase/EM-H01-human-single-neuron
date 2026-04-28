import gradio as gr
from response_parser import *
# from core import initialization, get_bot_backend, switch_model, add_text, bot
# from functools import lru_cache
import time
from config import get_config, CONFIG
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

ini_task_msg = '''You are a task-solving planner. Your task is to create a detailed task-solving plan for user_input. 
Your approach should be divided into the following three sections:
    1. Task Objectives and Functional Description: Clearly articulate the overall objectives, functional requirements, and expected outcomes of the task.
    2. Algorithm Steps and Implementation Details: Provide a step-by-step description of the specific algorithms required to accomplish the task, including methods and technical details for each step.
    3. Specific Constraints: List any specific constraints or conditions that need to be considered during implementation, such as computational resources, time complexity, accuracy requirements, etc.
Note: You do not need to write specific code, just provide a detailed plan and thought process. Return in bullet point and no extra content.
'''

modi_task_msg='''Based on the information you provided before, user did some modifications and confirmed the final plan and background as follows:'''

def txt_prompt_process(user_input_ini):
    llm_prompt = f'user_input: {user_input_ini} \n{ini_task_msg}'
    return llm_prompt

def txt_response_process(content):
    txt1 = content.split("###")
    ct1 = txt1[1]
    ct2 = txt1[2]
    ct3 = txt1[3]
    return ct1, ct2, ct3

def get_llm_text(state_dict: Dict,question: str):
    openai.api_base = get_config('API_base')
    openai.api_key = get_config('API_KEY')
    question = txt_prompt_process(question)
    #model = config['model']['GPT-4o']['model_name']
    #print(model)
    response = openai.ChatCompletion.create(
        model='GPT-4o',
        messages=[
            # {'role': 'system', 'content': "你是一名开发者"},
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

def user_info_confirm(txt1,txt2,txt3):
    final_user_input = f'''{modi_task_msg}
    Task Goal: {txt1}
    Algorithm Steps: {txt2}
    Constraints: {txt3}
    '''
    return final_user_input

if __name__ == '__main__':
    try:
        # Load your configuration here
        with gr.Blocks(theme=gr.themes.Base()) as block:
            gr.HTML("""
                <style>
                #generate_plan_btn, #generate_code_btn {
                    background-color: orange;
                    color: black;
                }
                </style>
            """)
            gr.HTML("""
                <script>
                function switchTab() {
                    let chatTab = document.querySelector('button[title="Chat"]');
                    if (chatTab) {
                        chatTab.click();
                    }
                }
                </script>
            """)
            
            state = gr.State(value={"bot_backend": None, "current_model": "GPT-4"})
            
            gr.Markdown(
                "<h1 style='text-align: center; font-size: 3em;'>😊Auto-llM Chatbot Interface</h1>"
            )
            
            with gr.Tab("Task Initialization") as task_tab:
                gr.Markdown("### Define and Generate Task Plan###")

                with gr.Row():
                    task_input = gr.Textbox(label="Task Description", lines=3)
                generate_plan_btn = gr.Button("✨Generate Task Plan", elem_id="generate_plan_btn")
                
                gr.Markdown("### Task Details")
                with gr.Row():
                    task_goal = gr.Textbox(label="Task Goal", lines=3)
                    algorithm_steps = gr.Textbox(label="Algorithm Steps", lines=3)
                    constraints = gr.Textbox(label="Constraints", lines=3)
                
                gr.Markdown("### Code Generation")
                with gr.Row():
                    code_language = gr.Dropdown(["Python", "JavaScript", "Java", "C++"], label="Code Language", value="Python")
                    generate_code_btn = gr.Button("🚀Start ！", elem_id="generate_code_btn")

            with gr.Tab("Code chat") as chat_tab:
                gr.Markdown("Chat!")
                chat_input = gr.Textbox(label="Chat Input", lines=3)
                
            generate_plan_btn.click(
                fn=get_llm_text,
                inputs=[task_input],
                outputs=[task_goal, algorithm_steps, constraints]
            )
            
            generate_code_btn.click(user_info_confirm, inputs=[task_goal, algorithm_steps, constraints], outputs=chat_tab)

            block.launch(inbrowser=True)
    except Exception as e:
        logging.error("An error occurred during initialization: %s", str(e))
        raise