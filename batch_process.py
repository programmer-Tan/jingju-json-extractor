# batch_process.py
import os
import asyncio
import json
from pathlib import Path
from pdf_processor import extract_text_from_pdf
from llm_extractor import extract_json_from_text   # 这是异步函数

async def process_one_pdf(pdf_path: Path, output_dir: Path, error_dir: Path):
    file_id = pdf_path.stem
    output_path = output_dir / f"{file_id}.json"
    
    # 如果 JSON 已存在，跳过处理
    if output_path.exists():
        print(f"[跳过] {file_id} 已存在，不再处理")
        return
    
    print(f"[开始] {file_id}")
    
    text = extract_text_from_pdf(str(pdf_path))
    if not text or len(text.strip()) < 200:
        (error_dir / f"{file_id}_empty.txt").write_text(f"文本过短: {pdf_path}")
        print(f"[失败] {file_id} 文本过短")
        return
    
    try:
        # 关键：这里必须加 await
        result = await extract_json_from_text(text, file_id)
    except Exception as e:
        (error_dir / f"{file_id}_llm_error.txt").write_text(f"LLM错误: {e}\n文本预览:\n{text[:500]}")
        print(f"[LLM失败] {file_id}: {e}")
        return
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[完成] {file_id} -> {output_path}")

async def batch_process(pdf_folder="pdfs", output_folder="output_json", error_folder="error_log"):
    pdf_dir = Path(pdf_folder)
    out_dir = Path(output_folder)
    err_dir = Path(error_folder)
    out_dir.mkdir(parents=True, exist_ok=True)
    err_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"发现 {len(pdf_files)} 个PDF文件")
    
    semaphore = asyncio.Semaphore(5)
    async def sem_task(p):
        async with semaphore:
            await process_one_pdf(p, out_dir, err_dir)
    
    tasks = [sem_task(p) for p in pdf_files]
    await asyncio.gather(*tasks)
    print("全部处理完成！")

if __name__ == "__main__":
    asyncio.run(batch_process())