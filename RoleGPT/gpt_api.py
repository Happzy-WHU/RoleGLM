import requests
import json

from time import sleep

url = "http://218.255.85.205:7102/prompt?Content-Type=application/json;charset=utf-8"
headers = {
  'Content-Type': 'application/json'
}

def call_gpt(history, prompt):
    json_data = {"history":history, "prompt":prompt}
    for _ in range(3):
        response = requests.request("POST", url, headers=headers, data=json.dumps(json_data))
        if response.status_code == 200:
            return response.text
        elif "content filter" in response.json()["error"]:
            json_data["bad"] = True
        sleep(3)

    # 调用出现错误
    print(response.json()["error"])
    return None

# 例子
if __name__ == "__main__":
    history = [{"role": "system", "content": ""}, {"role": "user", "content": "1+1=？"}, {"role": "assistant", "content": "很抱歉，作为一个AI，我无法回顾你之前说过的话。请提醒我你刚刚说了什么内容。"}]
    prompt = "我刚刚说了什么"
    ret = call_gpt(history, prompt)
    if ret:
        print(ret)
    else:
        print("调用失败")
