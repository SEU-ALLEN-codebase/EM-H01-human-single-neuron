import requests 
import logging
import re
import datetime
from pathlib import Path
import sys
import os

import openai
def init_logging():
    current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    logging.basicConfig(level=logging.DEBUG, 
                        filename=f'info_collection_{current_time}.log', 
                        filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        encoding='utf-8')


#Authorization: Bearer uid-sid1,uid-sid2,uid-sid3 ip搜索限制日100，多ip轮转
refresh_token = '66dda89dec3b340a0ef71a6e-e5102ac1953e4affb6072511e3e03e2c' 
#    api_url = 'https://stepfreeapi.shadow.cloudns.org/v1/chat/completions' 
api_base ='https://metasofreeapi.shadow.cloudns.org/v1/chat/completions'
def get_response_from_api(user_input): 
    headers = { 
        'Authorization': f'Bearer {refresh_token}', 
        'Content-Type': 'application/json' 
    } 
    # 全网model名称支持 -> 简洁：concise / 深入：detail / 研究：research
    # 学术model名称支持 -> 学术-简洁：concise-scholar / 学术-深入：detail-scholar / 学术-研究：research-scholar
    # model乱填的话，可以通过tempature参数来控制（但不支持学术）：简洁：< 0.4 / 深入：>= 0.4 && < 0.7 / 研究：>= 0.7
    # model乱填的话，还可以通过消息内容包含指令来控制：↓↓↓
    # 简洁 -> 简洁搜索 / 深入 -> 深入搜索 / 研究 -> 研究搜索
    # 学术-简洁 -> 学术简洁搜索：/ 学术-深入 -> 学术深入搜索 / 学术研究 -> 学术研究搜索
    # 优先级：model > 消息内容指令 > tempature

    # "finish reason":"stop"

    data = { 
        "model": "metaso", 
        "messages": [ 
            { 
                "role": "user", 
                "content": user_input 
            } 
        ], 
        "stream": False 
    } 
    #response = requests.post(api_url, headers=headers, json=data) 
    response = requests.post(api_base, headers=headers, json=data) 
    print(response)
    return response.json() 

def response_process(text):
    text = re.sub(r'\s+', ' ', text)  
    sentences = re.findall(r'.+?[。？！：]', text)
    unique_sentences = []
    for sentence in sentences:
        if sentence.strip() and sentence not in unique_sentences:
            unique_sentences.append(sentence)
    filtered_text = '\n'.join([sentence for sentence in unique_sentences if sentence.strip()])
    return filtered_text


# ini_task_msg='''You are a task-solving planner.Your task is to create a detailed task-solving plan for user_input. Here is some information for your reference, but you don't need to incorporate it fully into your plan. Please use your discretion based on your own plan
# Your approach should be divided into the following three sections:
#     1.Task Objectives and Functional Description: Clearly articulate the overall objectives, functional requirements, and expected outcomes of the task.
#     2.Solving Plan Steps and Implementation Details: Provide a step-by-step description of the specific algorithms required to accomplish the task, including methods and technical details for each step.
#     3.Specific Constraints: List any specific constraints or conditions that need to be considered during implementation, such as computational resources, time complexity, accuracy requirements, etc.
# 
# Note:You do not need to write specific code, just provide a detailed plan and thought process.Return in bullet point and no extra content.
# '''

ini_task_msg='''You are a task-solving planner.Your task is to create a detailed task-solving plan for user_input. Consider the following information, focusing on the most important points that are relevant to your task.
 Your approach should be divided into the following four sections:
    1.Task Objectives and Functional Description: Clearly articulate the overall objectives, functional requirements, and expected outcomes of the task.
    2.Solving Plan Steps and Implementation Details: Provide a step-by-step description of the specific algorithms required to accomplish the task, including methods and technical details for each step.
    3.Specific Constraints: List any specific constraints or conditions that need to be considered during implementation, such as computational resources, time complexity, accuracy requirements, etc.
    4.The useful content you utilized from the reference information to generate the plan
 Note:You do not need to write specific code, just provide a detailed plan and thought process.Return in bullet point and no extra content.'''
# info_msg='''You are a scientist, according to the task requested before, please analyze and provide the two themes you believe are the most necessary background knowledge that can serve as keywords for related information search which could be used in solving plan generation for the request. 
#             Return the answer in two concise sentences which could summarize the most important point of solving the request, using the format info_request[[][]]'''

info_msg='''As a scientist, based on the previous task, analyze and identify the two key themes necessary for solving the request. These themes will guide related information searches for generating a solution plan. 
Provide the answer in two concise sentences using the format info_request[[][]].'''
def process_info_theme(info_request):
    if not isinstance(info_request, str):
        raise ValueError("Input must be a string")
    # 使用正则表达式提取双括号 [[ ]] 内的主题
    pattern = r"\[\[([^\]]+)\]\]"
    themes = re.findall(pattern, info_request)
    return len(themes), themes

def get_keytheme(user_input,info_msg):
    openai.api_base = "https://api.openai.com/v1"
    #openai.api_key = get_config('API_KEY')
    openai.api_key =  "sk-proj-asxX9MfDsQ5Fez0VtRDwT3BlbkFJ8J6bL1PfOOgtLUpTkcED"
    #question = txt_prompt_process(question)
    model='gpt-4o'
    #model = config['model']['GPT-4o']['model_name']
    question = f'task_request:{user_input}{info_msg}'
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            # {'role': 'system', 'content': "You are an expert majored in neuroscience and excellently good at analysing and schduleing plans according to relevant and confirmed theroratical supoort"},
            {'role': 'user', 'content': question}
        ], 
        stream=True
    )

    full_reply_content = ''
    for chunk in response:
        message = chunk["choices"][0]["delta"].get("content", "")
        full_reply_content += message
    key_theme_count,key_theme_info=process_info_theme(full_reply_content)
    return key_theme_count,key_theme_info

def txt_prompt_process(user_input_ini,info_collection):
    llm_prompt = f'user_input: {user_input_ini}\ninformation:{info_collection}\n{ini_task_msg}'
    return llm_prompt

def txt_response_process(content):
    txt1 = content.split("###")
    ct1 = txt1[1]
    ct2 = txt1[2]
    ct3 = txt1[3]
    return ct1, ct2, ct3



def get_llm_text(question: str):
    # config = CONFIG
    #openai.api_base = get_config('API_base')
    openai.api_base = "https://api.openai.com/v1"
    #openai.api_key = get_config('API_KEY')
    openai.api_key =  "sk-proj-asxX9MfDsQ5Fez0VtRDwT3BlbkFJ8J6bL1PfOOgtLUpTkcED"
    #question = txt_prompt_process(question)
    model='gpt-4o'
    #model = config['model']['GPT-4o']['model_name']
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            # {'role': 'system', 'content': "You are an expert majored in neuroscience and excellently good at analysing and schduleing plans according to relevant and confirmed theroratical supoort"},
            {'role': 'user', 'content': question}
        ], 
        stream=True
    )
    print(question)
    full_reply_content = ''
    for chunk in response:
        message = chunk["choices"][0]["delta"].get("content", "")
        full_reply_content += message

    ct1, ct2, ct3 = txt_response_process(full_reply_content)
  
    return full_reply_content,ct1, ct2, ct3

def main(): 
    init_logging()
    while True: 
        user_input = input("请输入你的问题（输入886退出）: ") 
        logging.info(user_input)
        if user_input == '886': 
            print("程序退出。") 
            break 
        key_theme_count,key_theme_info=get_keytheme(user_input,info_msg)
        if not key_theme_info:
            print('--!!info collection fail!!!')
            continue
        print('---------------------------\nKeytheme extraction done!\n---------------------------')
        print(key_theme_count,key_theme_info)
        logging.info(key_theme_count)
        logging.info(key_theme_info)
        info_all=''
        for theme in key_theme_info :
            response = get_response_from_api(key_theme_info) 
            response_answer =response_process(response['choices'][0]['message']['content'])
            info_all+=response_answer

        
        logging.info(info_all)
        print("测试回答"+info_all)
        if info_all :
            print('---------------------------\nInformation collection done!\n---------------------------')
            logging.info(info_all)
            gpt_user_input =txt_prompt_process(user_input_ini=user_input,info_collection=info_all)
            full_reply_content,ct1, ct2, ct3=get_llm_text(gpt_user_input)
           
            if full_reply_content:
                logging.info(f"fully_task_plan_response: {full_reply_content}\nct1: {ct1}\n ct2: {ct2}\n ct3: {ct3}")
                print('---------------------------\nplan generation ok!\n---------------------------')
                print(f"fully_task_plan_response: {full_reply_content}\nct1: {ct1}\n ct2: {ct2}\n ct3: {ct3}")
            else:
                print('--!!generate plan fail!!!')
if __name__ == "__main__": 
    main()