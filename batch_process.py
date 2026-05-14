# batch_process.py
import os
import asyncio
import json
import re
from pathlib import Path
from pdf_processor import extract_text_from_pdf
from llm_extractor import extract_json_from_text


def extract_synopsis_commentary(text: str):
    """按行提取情节和注释，遇到结束标记行停止"""
    lines = text.splitlines()
    synopsis = ""
    commentary = ""
    
    # 1. 提取情节
    in_plot = False
    plot_lines = []
    for line in lines:
        if re.match(r'^情节\s*[:：]?\s*$', line.strip()):
            in_plot = True
            continue
        if in_plot:
            # 结束条件：遇到注释、##、【第、根据《戏考》、空行（可选）
            if (re.match(r'^注释\s*[:：]?\s*$', line.strip()) or
                re.match(r'^##', line) or
                re.match(r'^【第\d+场】', line) or
                re.search(r'根据《戏考》', line) or
                (line.strip() == "" and plot_lines)):
                break
            plot_lines.append(line.strip())
    if plot_lines:
        synopsis = " ".join(plot_lines)
        synopsis = re.sub(r'\s+', ' ', synopsis)
    
    # 2. 提取注释
    in_comment = False
    comment_lines = []
    for line in lines:
        if re.match(r'^注释\s*[:：]?\s*$', line.strip()):
            in_comment = True
            continue
        if in_comment:
            # 结束条件：遇到 ##、【第、根据《戏考》、情节、空行（可选）
            if (re.match(r'^##', line) or
                re.match(r'^【第\d+场】', line) or
                re.search(r'根据《戏考》', line) or
                re.match(r'^情节\s*[:：]?\s*$', line.strip()) or
                (line.strip() == "" and comment_lines)):
                break
            comment_lines.append(line.strip())
    if comment_lines:
        commentary = " ".join(comment_lines)
        commentary = re.sub(r'\s+', ' ', commentary)
    
    return synopsis, commentary

def extract_alternative_title(text: str) -> str:
    """提取剧本别名，例如“空城计（一名抚琴退敌）”"""
    import re
    patterns = [
        r'[（(]一名\s*([^）)]+)[）)]',          # 括号内“一名XXX”
        r'^一名\s*([^。\n]+)',                # 行首“一名XXX”
        r'《[^》]+》（一名([^）]+)）',          # 书名号后括号
        r'[（(]一名：?\s*([^）)]+)[）)]',       # 带冒号变体
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""

async def process_one_pdf(pdf_path: Path, output_dir: Path, error_dir: Path):
    file_id = pdf_path.stem
    output_path = output_dir / f"{file_id}.json"
    
    if output_path.exists():
        print(f"[跳过] {file_id} 已存在")
        return
    
    print(f"[开始] {file_id}")
    
    text = extract_text_from_pdf(str(pdf_path))
    if not text or len(text.strip()) < 200:
        (error_dir / f"{file_id}_empty.txt").write_text(f"文本过短: {pdf_path}")
        print(f"[失败] {file_id} 文本过短")
        return
    
    # 提取情节、注释、别名
    synopsis, commentary = extract_synopsis_commentary(text)
    alternative_title = extract_alternative_title(text)
    print(f"[DEBUG] 情节:{len(synopsis)} 注释:{len(commentary)} 别名:{len(alternative_title)}")
    
    try:
        result = await extract_json_from_text(text, file_id)
    except Exception as e:
        (error_dir / f"{file_id}_llm_error.txt").write_text(f"LLM错误: {e}\n文本预览:\n{text[:500]}")
        print(f"[LLM失败] {file_id}: {e}")
        return
    
    # 添加三个新字段
    result["synopsis"] = synopsis
    result["commentary"] = commentary
    result["metadata"]["alternative_title"] = alternative_title   # 别名放入 metadata
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[完成] {file_id} -> {output_path}")

async def batch_process(pdf_folder="pdfs", output_folder="output_json_1", error_folder="error_log"):
    pdf_dir = Path(pdf_folder)
    out_dir = Path(output_folder)
    err_dir = Path(error_folder)
    out_dir.mkdir(parents=True, exist_ok=True)
    err_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"发现 {len(pdf_files)} 个PDF文件")
    
    # 强制串行 + 间隔3秒，避免限流
    semaphore = asyncio.Semaphore(5)
    async def sem_task(p):
        async with semaphore:
            await process_one_pdf(p, out_dir, err_dir)
            await asyncio.sleep(1)      # 每个文件后等待1秒
    
    tasks = [sem_task(p) for p in pdf_files]
    await asyncio.gather(*tasks)
    print("全部处理完成！")

if __name__ == "__main__":
    asyncio.run(batch_process())