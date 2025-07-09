from openai import OpenAI
import base64
from pathlib import Path

#  base 64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
        
base64_image = encode_image("./paper_image/table_sta1.png")

text_path = Path("./prompt/demo.txt")

with text_path.open("r", encoding="utf-8") as f:
    text_content = f.read().strip() 

client = OpenAI(
    api_key="",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen-vl-max-latest",
    messages=[
        {
            "role": "system",
            "content": [
                {"type": "text", "text": "You are a helpful assistant."}
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    },
                },
                {
                    "type": "text",
                    "text": text_content 
                },
            ],
        },
    ],
)

print(completion.choices[0].message.content)