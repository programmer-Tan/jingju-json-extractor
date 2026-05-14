# main.py
import asyncio
from batch_process import batch_process

if __name__ == "__main__":
    print("京剧剧本批量提取工具")
    print("请将PDF文件放入 ./pdfs/ 目录")
    input("按Enter开始处理...")
    asyncio.run(batch_process())