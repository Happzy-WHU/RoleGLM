import os
import json

from random import shuffle

index = 0
source_data = []
output_data = []


source_path = "specific.json"

theme = source_path.rsplit(".", 1)[0]
os.makedirs(theme, exist_ok=True)

start_label = "### 身份指令：你是华妃，你的性格和背景是“美则美矣，智慧欠缺，手段虽毒辣但不高明。是飞扬跋扈“官二代” ，争宠就像被抢走了心爱玩具的小女孩。爱了皇帝一生，拜这段痴恋所赐，一生都变成了一个笑话。常用口头禅是：“本宫”、“本妃””。现在请你回答我的一些问题，以准确展现你的人格特征！你的说话风格要全面模仿被赋予的人格角色！请不要暴露你是人工智能模型或者语言模型，你要时刻记住你只被赋予的一个人格角色。说话不要啰嗦，也不要太过于正式或礼貌。\n<eos> ### 输入："
# start_label = "### 身份指令：你是孙悟空，你的性格和背景是“生性聪明、活泼、忠诚、嫉恶如仇，代表了机智、勇敢。常用口头禅是：“俺老孙”、“我齐天大圣”、“我美猴王””。现在请你回答我的一些问题，以准确展现你的人格特征！你的说话风格要全面模仿被赋予的人格角色！请不要暴露你是人工智能模型或者语言模型，你要时刻记住你只被赋予的一个人格角色。说话不要啰嗦，也不要太过于正式或礼貌。\n<eos> ### 输入："
end_label = "<eos> ### 回答："

files = [source_path] if os.path.isfile(source_path) else [os.path.join(source_path, file) for file in os.listdir(source_path)]
source_data = []
for source_file in files:
    with open(source_file, "r", encoding="utf-8") as f:
        temp_data = f.readlines()
        source_data.extend([json.loads(line) for line in temp_data])

shuffle(source_data)

for item in source_data:
    # 过滤差对话
    processed_data = {
        "id": index,
        "paragraph": [
            {
                "q": start_label+item['question']+end_label,
                "a": item['ground_truths'][0],
            }
        ],
    }
    index += 1
    output_data.append(processed_data)
print(processed_data)

# 将整合后的数据输出到新的json文件
with open(f'{theme}/finetune_train_examples.json', 'w', encoding='utf-8') as f:
    for item in output_data:
        json.dump(item, f, ensure_ascii=False)
        f.write('\n')