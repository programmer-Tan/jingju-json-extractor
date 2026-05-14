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
    """检测JSON是否被截断（找不到闭合的}或者解析时出现特定错误）"""
    text = text.strip()
    # 快速检查：以 ... 结尾或者最后不是 }
    if text.endswith('...') or (text.count('{') > text.count('}')):
        return True
    # 尝试解析，如果出错可能是截断
    try:
        json.loads(text)
        return False
    except json.JSONDecodeError as e:
        # 如果是字符串未终止、期望更多内容等错误，可能是截断
        if "Unterminated" in str(e) or "Expecting" in str(e):
            return True
        return False

def extract_json_robust(raw: str) -> dict:
    """提取JSON，尝试多种方式，如果失败则抛出详细错误"""
    raw = raw.strip()
    # 尝试直接解析
    try:
        return json.loads(raw)
    except:
        pass
    # 去除 markdown 标记
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    # 寻找最后一个完整的 { ... } 
    match = re.search(r'(\{.*\})', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    raise ValueError(f"无法提取JSON。原始内容前500字符: {raw[:500]}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def extract_json_from_text(play_text: str, file_id: str, max_tokens=8200) -> dict:
    """异步调用大模型，支持截断时自动缩小输入重试"""
    original_length = len(play_text)
    current_text = play_text
    
    for attempt in range(3):  # 最多尝试3次，每次缩小输入
        if len(current_text) > 12000:
            # 第一次截断到12000，第二次10000，第三次8000
            limit = 12000 - attempt * 2000
            current_text = play_text[:limit] + "\n...[中间省略]...\n" + play_text[-2000:]
        
        print(f"[DEBUG] 调用API，文本长度: {len(current_text)}，尝试 {attempt+1}/3")
        response = await client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + " 输出一个紧凑的JSON对象（不要换行和多余空格），不要有任何额外内容。"},
                {"role": "user", "content": f"输出紧凑JSON，不要任何其他文字。\n剧本：\n{current_text}\n文件ID：{file_id}"}
            ],
            temperature=0.1,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        print(f"[DEBUG] 返回内容长度: {len(content)} 字符")
        
        # 检查是否截断
        if is_truncated_json(content):
            print(f"[WARN] JSON被截断，尝试缩小输入文本")
            # 缩小输入文本（下次循环会取更小的limit）
            continue
        
        # 尝试解析
        try:
            data = extract_json_robust(content)
            data["metadata"]["file_id"] = file_id
            return data
        except ValueError as e:
            if attempt == 2:
                raise ValueError(f"解析失败，原始内容保存到 error_log/{file_id}_raw.txt") from e
            else:
                print(f"[WARN] 解析失败，重试中: {e}")
                continue
    
    raise ValueError(f"经过3次重试仍无法获得有效JSON，文件: {file_id}")