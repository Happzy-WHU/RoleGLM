# RoleGLM流程

项目路径：https://github.com/Happzy-WHU/RoleGLM



## 1 配置文件

### 1.1 解析剧本

profile_xiyou/desc.json    

这个文件记录了剧本中所有角色的性格、背景。可以手写或者借助gpt工具。



profile_xiyou/西游记-孙悟空.jsonl

这个文件记录了西游记中孙悟空有关的对话。需要将原始剧本解析为profile文件。每个剧本的情况不同，大致流程是先从剧本中解析出所有人的对话，再解析得到人物对话。



### 1.2 格式化

运行format_role_to_last.py，保证每段对话的最后一句一定来自要进行风格化的角色。



## 2 RoleGPT

修改相关参数user_name、world、screenplay_name。

执行RoleGPT/rolegpt.py，即可获取风格化的general原始数据集。



## 3 训练数据集

执行make_lora_dataset.py，即可得到用于lora训练的数据集。



## 4 训练

1. 将第三步得到的finetune_train_examples.json文件放到glm2_train/data路径下。

2. rm -rf output  这一步可以删除之前生成的训练数据。
3. python data_utils.py  这一步可以重新生成训练数据。
4. python train.py 训练