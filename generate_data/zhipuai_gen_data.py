import os
import random
import json
import yaml 
from tqdm import tqdm
# from dotenv import load_dotenv
from zhipuai import ZhipuAI


with open('config.yml', 'r', encoding='utf-8') as f:
    configs = yaml.load(f.read(), Loader=yaml.FullLoader)

load_dotenv()
client = ZhipuAI(api_key=configs['zhiouai_api_key'])

def zhipu_api(data, emo):

    def getText(role, content, text = []):
        jsoncon = {}
        jsoncon['role'] = role
        jsoncon['content'] = content
        text.append(jsoncon)
        return text

    prompt = f'''你是一个研究过无数具有心理健康问题的病人与心理健康医生对话的专家，请你构造一些符合实际情况的具有心理健
康问题的病人和心理健康医生的连续的多轮对话记录。要求病人的问题属于{data}场景，具有{emo}情感，医生的回复尽可能包含心理辅导知识，并且能够一步步诱导病人说出自己的问题进而提供解决问题的可行方案。注意，构造的数据必须以医生的陈述为结束语，每次只需要构造一个案例并且不需要写案例一、二等等，请只返回完整的对话内容。请以如下格式返回生成的数据：
病人：病人的咨询或陈述 
医生：医生的安抚和建议
    '''
    
    top_p = round(random.uniform(0.1, 0.9), 2)
    messages = getText('user', prompt)
    response = client.chat.completions.create(
        model='glm-4',
        messages=messages,
        top_p=top_p,
    )

    return response.choices[0].message.content


def convert(conversation):
    ret, one_conversation = {}, {}
    ret['conversation'] = []
    one_conversation['system'] = '现在你是一个心理专家，我有一些心理问题，请你用专业的知识帮我解决。'
    
    while '病人：' in conversation and '医生：' in conversation:
        one_conversation['input'] = conversation.split('病人：')[1].split('医生：')[0]
        one_conversation['output'] = conversation.split('病人：')[1].split('医生：')[1].split('病人：')[0]
        conversation = '病人：' + '病人：'.join(conversation.split('病人：')[2:])
        ret['conversation'].append(one_conversation)
        one_conversation = {}

    return ret


def save_jsonl(data_lis, file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data_lis:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    emotions_lis = configs['emotions_list']
    areas_of_life = configs['areas_of_life']

    conversation_lis = []
    for emo in emotions_lis:
        for area in areas_of_life:
            if os.path.exists(f'./zhipuai/{area}/{emo}.jsonl'):
                print(f'./zhipuai/{area}/{emo}.jsonl exists')
                continue
            for i in tqdm(range(5), desc='{emo}, {area}'.format(emo=emo, area=area)):
                res = zhipu_api(area, emo)
                print(res)
                if res == 'null':
                    print(area, emo, 'error')
                    continue
                conversation_lis.append(convert(res))
            save_jsonl(conversation_lis, f'./zhipuai/{area}/{emo}.jsonl')
            print(f'generate ./zhipuai/{area}/{emo}.jsonl')
            conversation_lis = []
