import os
import json
import jieba

from random import sample
from rank_bm25 import BM25Okapi
from concurrent import futures
from loguru import logger
from gpt_api import call_gpt

task_instruction = "现在请你回答我的一些问题，以准确展现你的人格特征！你的说话风格要全面模仿被赋予的人格角色！请不要暴露你是人工智能模型或者语言模型，" \
                   "你要时刻记住你只被赋予的一个人格角色。说话不要啰嗦，也不要太过于正式或礼貌"
path_to_data = '/data1/zhongyuan_peng/Data/belle_6000.jsonl'
do_question_style_transfer = False
max_workers = 2

user_name = "孙悟空"
world = 'xiyou'
screenplay_name = '西游记'

dest_file = f"output/{user_name}.json"
dir_to_worlds = f"../screenplay"
path_to_profile = f"../screenplay/profile_{world}"

def question_style_transfer(personality, description, question):
    input_prompt = ""
    input_prompt += f"{personality}的人格描述是“{description}”。" \
                    f"我想和{personality}说话，但是我需要将我的话转变说法以适应{personality}的时代背景和说话风格等。" \
                    f"我想说的话是：“{question}\n" \
                    f"你能帮我改写这句话吗？直接回复我改写后的话就可以，不要啰嗦，也不用翻译！" 
    history = [{"role": "system", "content": "你是一个说话风格迁移模型。"}]
    return call_gpt(history, input_prompt)

def wrap_fs_dialogue_engr_prompts(personality, description, profile, question, do_question_style_transfer=False):
    # 对话生成器函数，用于构建对话样本的输入提示
    if personality not in question:
        question = f"{personality}，{question}"
     # 在问题前添加角色的特征描述，以确保问题与角色的特征相关
    if do_question_style_transfer:
         # 如果需要进行问题的风格转换
        input_prompt = question_style_transfer(personality, description, question)
        # 调用 question_style_transfer 函数，将问题进行风格转换
    else:
        input_prompt = question
        
    if input_prompt.startswith("“"):
        input_prompt = input_prompt[1:]
    if input_prompt.endswith("”"):
        input_prompt = input_prompt[:-1]
        
    history = [{"role": "system", "content": f"你是{personality}，你的性格和背景是“{description}”。{task_instruction}。"}]
    # 遍历 profile 中的每个对话，将问题和回答添加到提示列表 prompt 中
    for each in profile:
        question = each[0]
        answer = each[1] if "：" not in each[1] else each[1].split("：", 1)[1]
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
    return history, input_prompt

def get_screenplay_profile(path_to_profile, input_question, character, number_dialogues):
    def profile_filter(grouped_dialogues):
        # grouped_dialogues: {..., diag_id: [{"act_id": 0, "diag_id": 1, "role": '旁白', "content": '...'}], ...}

        # 过滤规则一：根据对话的次数筛选
       # 定义最大对话句子数 
        max_num_diag_sents = 6
        # 用于存储超过最大句子数的对话ID的列表
        to_pop_item_ids = []
        # 遍历 grouped_dialogues 字典的键值对
        for diag_id, diag in grouped_dialogues.items():
            # 如果对话的句子数大于最大对话句子数
            if len(diag) > max_num_diag_sents:
                 # 将该对话ID添加到待删除的列表
                to_pop_item_ids.append(diag_id)
        for item_id in to_pop_item_ids:
            grouped_dialogues.pop(item_id)

        # 过滤规则二：根据 character 角色的对话长度筛选
        pass

        # 过滤规则三：根据 character 角色的特色鲜明度来筛选
        pass

        return grouped_dialogues

    def in_context_example_selection(grouped_dialogues, number_samples, mode='random'):
        # 根据 mode 参数选择不同的对话样本筛选方式
        if mode == 'random':
        # 如果 mode 为 'random'，随机选取对话样本
        # 获取所有对话的 ID 列表
            ids = list(grouped_dialogues.keys())
            if number_samples > len(ids):
                # 如果需要的样本数大于总对话数，直接返回所有对话的 ID 列表
                return ids
            else:
                # 否则，从所有对话的 ID 列表中随机选取指定数量的样本
                return sample(ids, number_samples)

        elif mode == 'sparse-bm25':
            # grouped_dialogues: {..., diag_id: [{"act_id": 0, "diag_id": 1, "role": '旁白', "content": '...'}], ...}
            ids = list(grouped_dialogues.keys())
            # 将原始对话内容转换为 jieba 分词后的格式
            raw_dialogues = list(grouped_dialogues.values())
            dialogues = []
            for item in raw_dialogues:
                # item: {'id': 0, 'role': '旁白', 'content': '....'}, ...]
                content = ""
                for each in item:
                    # 每一行对话的角色
                    word = each["role"]
                    # 如果角色不在 jieba 分词的词汇表中，将其添加，并设置词频
                    if word not in jieba.lcut(word):
                        freq = jieba.suggest_freq(word)
                        jieba.add_word(word, freq=freq)
                    content += f"{word}：{each['content']}\n"
                # tokenize content with jieba
                content = jieba.lcut(content)
                dialogues.append(content)
            # 使用输入问题的分词作为查询语句
            query = jieba.lcut(input_question)
            # 使用 BM25 算法计算每个对话与查询语句的相似度得分 
            bm25 = BM25Okapi(dialogues)
            scores = bm25.get_scores(query)
            # 根据相似度得分排序，并选取得分最高的一部分对话作为样本
            sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            top_indices = sorted_indices[:number_samples]
            return [ids[i] for i in top_indices]

        else:
            raise NotImplementedError(f"Mode {mode} for in-context example selection is not implemented.")

    path_to_screenplay = path_to_profile

    # 根据剧本名称和角色构建剧本角色的配置文件路径
    path_to_profile = os.path.join(path_to_screenplay, f'{screenplay_name}-{character}.jsonl')

    # 打开描述文件 'desc.json'，读取角色的描述信息
    with open(os.path.join(path_to_screenplay, 'desc.json'), 'r', encoding='utf-8') as desc_file:
        desc_file_content = json.load(desc_file)
        description = desc_file_content[character]
    # 检查剧本角色的配置文件是否存在
    if not os.path.exists(path_to_profile):
        raise FileNotFoundError(
            f"Profile {path_to_profile} does not exist, we may not have the character {character} for the screenplay {screenplay_name}.")
    # 打开剧本角色的配置文件，读取文件中的内容并解析为对话对象
    with open(path_to_profile, 'r', encoding='utf-8') as file:
        # 读取文件中的内容
        lines = file.readlines()
        # 解析每行内容为对话对象
        dialogues = [json.loads(line) for line in lines]

        # 解析每行内容为对话对象，使用 json.loads 将每行转换为字典对象，放入列表 dialogues
        # 根据对话ID进行分组，将对话按照对话ID分组，存储在 grouped_dialogues 字典中
        grouped_dialogues = {}
        for dialogue in dialogues:
            dialogue_id = dialogue["diag_id"]
            if dialogue_id not in grouped_dialogues:
                grouped_dialogues[dialogue_id] = []
            grouped_dialogues[dialogue_id].append(dialogue)

        # 对 grouped_dialogues 进行过滤
        grouped_dialogues = profile_filter(grouped_dialogues)

        # 采样number_dialogues个对话ID
        sampled_dialogue_ids = in_context_example_selection(grouped_dialogues, number_dialogues,
                                                            mode='sparse-bm25')

        # 整理对话为(question, answer)格式的列表
        dialogues_formatted = []
        for dialogue_id in sampled_dialogue_ids:
            # 遍历采样得到的对话ID列表 sampled_dialogue_ids
            dialogue = grouped_dialogues[dialogue_id]
            # 根据对话ID从 grouped_dialogues 字典中获取对话内容
            question = ''
            answer = ''
            # 初始化问题和回答字符串为空
            for line in dialogue:
                # 遍历对话中的每一行内容
                role = line['role']
                content = line['content']
                if role == character:
                    answer += content
                    # 去除问题和回答字符串的首尾空格
                    question, answer = question.strip(), answer.strip()
                    if question != '' and answer != '':
                        dialogues_formatted.append((question, answer))
                    question = ''
                    answer = ''
                else:
                     # 将对话内容添加到问题字符串中，形式为 '角色: “对话内容”\n'
                    question += f"{role}: “{content}”\n"

    return description, dialogues_formatted

def format_answer(s):
    s = s.replace(": ", "：").replace(":", "：")
    if s[-1] == "”" and "“" in s:
        return s[:-1].split("“")[1]
    elif "：" in s:
        return s.split("：", 1)[1]
    else:
        return s

# 定义名为 fs_dialogue_engr_dataset 的函数，并传入一个参数 args_tuple
def fs_dialogue_engr_dataset(args_tuple):
    # 解包 args_tuple，将元组中的元素分别赋值给 role 和 index, input_info 变量
    role = user_name
    index, input_info = args_tuple
    # 创建一个字符串 question，包含对 input_info 中的信息进行格式化的问题描述
    question = f'问题：<{input_info["question"]}>。'
    # 调用 get_screenplay_profile 函数获取剧本角色的描述信息 description 和剧本角色的配置文件 profile
    description, profile = get_screenplay_profile(path_to_profile, question, role, number_dialogues=3)
    # 将问题保存在 generated_question 中
    generated_question = question + f"参考回答：<{input_info['generated']}>。{user_name}，请你回答这个问题。"
    # 使用 wrap_fs_dialogue_engr_prompts 包装函数，生成一个提示语 prompt，用于调用 chatgpt 进行对话
    history, prompt = wrap_fs_dialogue_engr_prompts(role, description, profile, generated_question,
                                            do_question_style_transfer)
    # 调用 chatgpt 模型进行对话，将生成的回答保存在 generated 中
    generated = call_gpt(history, prompt)
    # 将生成的对话信息（index、问题、回答）以 JSON 格式写入文件，并添加到 role.json 中
    if generated:
        with open(dest_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id":index, 'question': input_info["question"], 'generated': format_answer(generated)}, ensure_ascii=False)+"\n")
        logger.info(f"finished: {index}")
    else:
        logger.warning(f"passed: {index}")

if __name__ == '__main__':
    # 使用指定路径 'path_to_data' 以只读方式、UTF-8编码打开文件
    with open(path_to_data, 'r', encoding='utf-8') as file:
        # 读取文件的所有行，将它们作为字符串的列表存储在 'all_lines' 中
        all_lines = file.readlines()

    # 将 'all_lines' 中的每一行（假设为JSON格式）转换成Python字典，并将它们存储在 'questions' 中
    questions = [json.loads(line) for line in all_lines]
    processed_indexs = set() 
    # 创建一个空集合 'processed_indexs' 用于存储已处理对话的索引

    # 检查名为 'dest_file' 的文件是否存在
    if os.path.exists(dest_file):
        # 如果 'dest_file' 存在，则以只读模式、UTF-8编码打开它
        with open(dest_file, "r", encoding="utf-8") as f:
            # 读取文件的所有行，将它们作为字符串的列表存储在 'old_lines' 中
            old_lines = f.readlines()
            # 从 'old_lines' 中提取每个JSON对象的 "id" 字段，并将所有的 "id" 字段值存储在 'processed_indexs' 中
            processed_indexs = {json.loads(line)["id"] for line in old_lines}
    
    # 计算未处理对话的索引集合，通过找到所有可能的索引和已处理索引之间的差异得到
    unpro_indexs = set(range(len(questions))) - processed_indexs

    # 使用日志记录器（logger）输出一条信息，显示待处理对话的数量
    logger.info(f"待处理对话数：{len(unpro_indexs)}")

    # 创建一个元组列表 'indexed_input'，其中每个元组包含一个未处理对话的索引和 'questions' 列表中对应的对话
    indexed_input = [(unpro_index, questions[unpro_index]) for unpro_index in unpro_indexs]
    # for item in indexed_input:
    #     fs_dialogue_engr_dataset(item)

    # 使用最大工作线程数为5的ThreadPoolExecutor
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 返回一个结果迭代器
        results = executor.map(fs_dialogue_engr_dataset, indexed_input)
