from py2neo import Graph
import requests
import json
from prompt_list import *
from openai import OpenAI
import re

# decide the base model
use_model = "chatglm3-6b"

# chatglm3-6b
base_url = "http://0.0.0.0:8000"

# neo4j
graph = Graph("http://0.0.0.0:7474", auth=("neo4j", "neo4j"))



def prepare_dataset(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            line_data = line.strip().split('\t')
            data.append(line_data)
    return data

def str_match(info, entity_chains):
    return any(info in entity or entity in info for entity in entity_chains)



def create_chat_completion(model, messages, functions, use_stream=False):
    data = {
        "functions": functions,  # 函数定义
        "model": model,  # 模型名称
        "messages": messages,  # 会话历史
        "stream": use_stream,  # 是否流式响应
        "max_tokens": 300,  # 最多生成字数
        "temperature": 0,  # 温度
        "top_p": 0.8,  # 采样概率
    }
    content = ""
    response = requests.post(f"{base_url}/v1/chat/completions", json=data, stream=use_stream)
    if response.status_code == 200:
        if use_stream:
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')[6:]
                    try:
                        response_json = json.loads(decoded_line)
                        content = response_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        print(content)
                    except:
                        print("Special Token:", decoded_line)
        else:
            # 处理非流式响应
            decoded_line = response.json()
            content = decoded_line.get("choices", [{}])[0].get("message", "").get("content", "")
    else:
        print("Error:", response.status_code)
        return None
    return content


def construct_entity_chain_prompt(question):
    return entity_chain_prompt % question

def construct_select_node_prompt(question, uninvovled_info, candidates):
    return select_node_prompt.format(question, uninvovled_info, candidates)

def construct_info_match_prompt(question, entity, info):
    return info_match_prompt.format(question, entity, info)

def construct_answer_prompt(question, routes):
    return answer_prompt.format(question, routes)

def construct_prune_prompt(question, aim_info, entity, related_node):
    return prune_prompt.format(question, aim_info, entity, related_node)

#chatglm3-6b
def simple_chat(prompt, use_stream=False):
    functions = None
    chat_messages = [
        {
            "role": "system",
            "content": "You are ChatGLM3, a large language model trained by Zhipu.AI. Follow the user's instructions carefully. Respond using markdown.",
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    return create_chat_completion("chatglm3-6b", messages=chat_messages, functions=functions, use_stream=use_stream)




def chatgpt(prompt, model="gpt-3.5-turbo-16k"):
    client = OpenAI(
        api_key="your_api_key",
        base_url="https://api.openai.com"
    )

    completion = client.chat.completions.create(
        model= model,
        # model='gpt-4',
        messages=[
            {"role": "system", "content": "You are an AI assistant that helps people find information."},
            {"role": "user", "content": prompt}
        ],
        stream=False,  
        temperature=0  # 设置temperature为0
    )

    return completion.choices[0].message.content




def extract_entity_chain(question, model=use_model):
    prompt = construct_entity_chain_prompt(question)
    if model == "chatglm3-6b":
        response = simple_chat(prompt, use_stream=False)
    else:
        response = chatgpt(prompt, model)
    response_list = re.findall(r'[\(（](.*?)[\)）]', response)[0].split(",")
    new_list = [element.lstrip() for element in response_list]
    return new_list



def info_match(question, entity, info, model=use_model):
    prompt = construct_info_match_prompt(question, entity, info)
    if model == "chatglm3-6b":
        response = simple_chat(prompt, use_stream=False)
    else:
        response = chatgpt(prompt)
    # print(response)
    infos = re.findall(r"'(.*?)'", response)
    scores = re.findall(r"(\d+)分", response)
    max_score = '0'
    for score in scores:
        if score > max_score:
            max_score = score
    if max_score == '0':
        return []
    return infos[scores.index(max_score)]


def prune_node(question, aim_info, entity, related_node, model=use_model):
    prompt = construct_prune_prompt(question, aim_info, entity, related_node)
    if model == "chatglm3-6b":
        response = simple_chat(prompt, use_stream=False)
    else:
        response = chatgpt(prompt)
    pattern = r"\((.*?)\)"
    score_pattern = r"(\d+)分"
    matches = re.findall(pattern, response)
    scores = re.findall(score_pattern, response)
    result = []
    for i in range(len(matches)):
        match = matches[i].split(",")
        if len(match) != 2:
            continue
        if i == len(scores):
            break
        if scores[i] == '0':
            continue
        result.append((match[0].strip()[1:-1], match[1].strip()[1:-1], scores[i]))
    if len(result) > 10:
        result.sort(key=lambda x: int(x[2]), reverse=True)
        result = result[:10]
    return result


def select_node(question, uninvovled_info, candidates, model=use_model):
    prompt = construct_select_node_prompt(question, uninvovled_info, candidates)
    if model == "chatglm3-6b":
        response = simple_chat(prompt, use_stream=False)
    else:
        response = chatgpt(prompt)
    pattern = r"\((.*?)\)"
    score_pattern = r"(\d+)分"
    matches = re.findall(pattern, response)
    scores = re.findall(score_pattern, response)
    result = []
    for i in range(len(matches)):
        match = matches[i].split(",")
        if len(match) != 2:
            continue
        if i == len(scores):
            break
        if scores[i] == '0':
            continue
        result.append((match[0].strip()[1:-1], match[1].strip()[1:-1], scores[i]))
    if len(result) > 5:
        result.sort(key=lambda x: int(x[2]), reverse=True)
        result = result[:5]
    return result


def answer_question(question, routes, model=use_model):
    s = ''
    for r in routes:
        s += str(r) + ', '
    prompt = construct_answer_prompt(question, s)
    if model == "chatglm3-6b":
        response = simple_chat(prompt, use_stream=False)
    else:
        response = chatgpt(prompt)
    return response



def query_node(property_value):
    query = f"MATCH (n) WHERE n.name = '{property_value}' RETURN n"
    nodes = graph.run(query).data()
    result = []
    for node in nodes:
        label = node['n'].labels
        label = str(label).replace(":", "")
        name = str(node['n']['name'])
        id = str(node['n']['id'])
        result.append((label, name, id))
    return list(set(result))



def get_related_nodes_by_id(now_id):
    result = []
    related_nodes = graph.run(f"MATCH (n)-[r]-(related) WHERE n.id = '{now_id}' RETURN r, related").data()
    for node in related_nodes:
        r = type(node['r']).__name__
        label = node['related'].labels
        label = str(label).replace(":", "")
        name = str(node['related']['name'])
        id = str(node['related']['id'])
        result.append((label, name, id, r))
    return list(set(result))
