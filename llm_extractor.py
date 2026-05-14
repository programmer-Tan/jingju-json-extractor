# llm_extractor.py
import os
import json
import re
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from schema import SYSTEM_PROMPT

load_dotenv()

API_KEY = os.getenv("ARK_API_KEY")
BASE_URL = os.getenv("ARK_BASE_URL")
MODEL_ID = os.getenv("ARK_MODEL_ID")

if not all([API_KEY, BASE_URL, MODEL_ID]):
    raise ValueError("请检查.env文件")

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

def is_truncated_json(text: str) -> bool:
    """检测JSON是否被截断"""
    text = text.strip()
    if text.endswith('...') or (text.count('{') > text.count('}')):
        return True
    try:
        json.loads(text)
        return False
    except json.JSONDecodeError as e:
        if "Unterminated" in str(e) or "Expecting" in str(e):
            return True
        return False

def extract_json_robust(raw: str) -> dict:
    """鲁棒提取JSON"""
    raw = raw.strip()
    try:
        return json.loads(raw)
    except:
        pass
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    match = re.search(r'(\{.*\})', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    raise ValueError(f"无法提取JSON。原始内容前500字符: {raw[:500]}")

# 注意：不再使用 @retry，因为我们要一次性成功，失败就记录并移动文件
async def extract_json_from_text(play_text: str, file_id: str, max_tokens=16000) -> dict:
    """
    异步调用大模型，max_tokens 增大到 16000 以减少截断可能。
    不进行多次重试，一旦失败或截断，直接抛出异常。
    """
    print(f"[DEBUG] 调用API，文本长度: {len(play_text)}")
    response = await client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + " 输出一个紧凑的JSON对象（不要换行和多余空格），不要有任何额外内容。"},
            {"role": "user", "content": f"输出紧凑JSON，不要任何其他文字。\n剧本：\n{play_text}\n文件ID：{file_id}"}
        ],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    print(f"[DEBUG] 返回内容长度: {len(content)} 字符")
    
    # 检测是否截断
    if is_truncated_json(content):
        raise ValueError(f"JSON被截断，返回内容长度 {len(content)}，可能需要更大的 max_tokens")
    
    # 解析JSON
    data = extract_json_robust(content)
    data["metadata"]["file_id"] = file_id
    return data