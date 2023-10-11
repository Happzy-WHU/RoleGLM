import os
import json
from pathlib import Path

from itertools import groupby

# source_path = "scripts/Trainspotting_script.txt"
# dest_path = "0911"

# all_files = [source_path] if os.path.isfile(source_path) else [os.path.join(source_path, file) for file in os.listdir(source_path)]
# os.makedirs(dest_path) if not os.path.exists(dest_path) else print("dest path exist.")

def judge_startwith(line, target):
    return len(line)>len(target) and line.startswith(target) and line[len(target)]!=" "

def erase_none(s):
    return s.replace("\n", "").replace("\t", "")

def judge_is_eplo(line, eplo_splits):
    for eplo_split in eplo_splits:
        if line.startswith(eplo_split):
            return True
    return False

def get_format_drama(source_data, narration_split, diag_split, name_split, skip_split, eplo_splits):
    act_id = 0
    added = False
    diags = []
    role = ""
    content = ""
    for line in source_data:
        if not line and line.startswith(skip_split):
            continue
        
        if judge_is_eplo(line, eplo_splits):
            content = ""
            if not added:
                act_id+=1
                added = True
            continue
        
        if judge_startwith(line, name_split) or (judge_startwith(line, skip_split) and line[len(skip_split)]!="("):
            content = erase_none(content)
            if content:
                diags.append({"act_id": act_id, "diag_id": 0, "role": erase_none(role), "content": content})
                if judge_startwith(line, name_split):
                    role = line.replace(name_split, "")
                else:
                    role = line.replace(skip_split, "")
                content = ""
                added = False
            continue

        if judge_startwith(line, diag_split):
            content = line.replace(diag_split, "") if not content else content+line.replace(diag_split, " ")
            continue

        if judge_startwith(line, narration_split):
            line = erase_none(line)
            if line:
                diags.append({"act_id": act_id, "diag_id": 0, "role": "narration", "content": line})
                added = False
            continue
    return diags

def parse_drama():
    for source_file in all_files:
        dest_file = os.path.join(dest_path, Path(source_file).name)
        with open(source_file, "r", encoding="utf-8") as f:
            source_data = f.readlines()
        
        narration_split = ""
        diag_split = "     "
        name_split = "                                   "
        skip_split = "                                    "
        eplo_splits = ["--------", "INT."]
        diags = get_format_drama(source_data, narration_split, diag_split, name_split, skip_split, eplo_splits)
        with open(dest_file, "w", encoding="utf-8") as f:
            for line in diags:
                f.write(json.dumps(line)+"\n")

def merge_dicts(dict_list):
    if not dict_list:
        return []

    merged_list = [dict_list[0].copy()]  # 开始于第一个元素

    for curr_dict in dict_list[1:]:  # 从第二个元素开始迭代
        # 如果当前字典的role和act_id与merged_list末尾的字典相同，就合并它们的content
        if curr_dict['role'] == merged_list[-1]['role'] and curr_dict['act_id'] == merged_list[-1]['act_id']:
            merged_list[-1]['content'] += curr_dict['content']
        else:
            # 否则，将当前字典添加到merged_list中
            merged_list.append(curr_dict.copy())

    return merged_list

def remove_until_by_name(lst, name):
    for sublist in lst:
        for i in reversed(range(len(sublist))):
            if 'role' in sublist[i] and sublist[i]['role'] == name:
                break
            else:
                del sublist[i]
    return lst
     

def parse_role(source_file, dest_file, name):
    
    with open(source_file, "r", encoding="utf-8") as f:
        source_data = f.readlines()
        source_data = [json.loads(line) for line in source_data]
        for item in source_data:
            if "act_id" not in item:
                item["act_id"] = item["episode_id"]
        source_data = merge_dicts(source_data)


    grouped_list = [list(group) for key, group in groupby(source_data, lambda x: x['act_id'])]
    grouped_list = remove_until_by_name(grouped_list, name)

    result = []
    act_id = 0
    diag_id = 0
    
    for diags in grouped_list:
        if not diags:
            continue
        for diag in diags:
            result.append({"act_id": act_id, "diag_id": diag_id, "role": diag["role"], "content": diag["content"]})
            if diag["role"] == name:
                diag_id+=1
        act_id+=1
    
    with open(dest_file, "w", encoding="utf-8") as f:
        for line in result:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

parse_role(source_file="甄嬛传-华妃.jsonl", dest_file="甄嬛传-华妃_prod.jsonl", name="华妃")
