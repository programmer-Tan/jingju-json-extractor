# 京剧剧本结构化提取工具 (Peking Opera Script Extractor)

批量处理 PDF 格式的京剧剧本，通过大模型（LLM）自动提取角色、场次、台词、情节、注释、别名等结构化信息，输出规范的 JSON 文件。

## 功能特性

- 📄 **PDF 文本提取**：自动从 PDF 中提取剧本纯文本（基于 `pypdf`）
- 🤖 **智能结构化**：利用大模型识别角色、行当、年龄、性格、身份等元数据
- 🎭 **细粒度解析**：区分唱词（西皮/二黄等板式）、念白（白/念）、舞台指示
- 📝 **情节与注释**：自动提取“情节”和“注释”段落，并压缩多余空白
- 🏷️ **别名识别**：自动提取“一名XXX”作为剧本别名（如《空城计》一名《抚琴退敌》）
- ⚡ **异步并发**：支持可控并发（默认 1，避免 API 限流）
- 🔁 **断点续传**：已生成的 JSON 文件不会重复处理
- 🛡️ **容错机制**：长文本自动截断重试，JSON 解析失败时降级提取
- 🕒 **限流保护**：内置请求间隔（默认 3 秒），可灵活调整

## 环境要求

- Python 3.8+
- 大模型 API（支持 OpenAI 兼容接口，如火山引擎豆包、DeepSeek 等）
- PDF 解析库（`pypdf`）

## 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/...
   cd peking-opera-script-extractor
安装依赖

bash
pip install -r requirements.txt
配置环境变量
复制 .env.example 为 .env，并填入你的 API 信息：

bash
cp .env.example .env
编辑 .env：

ini
ARK_API_KEY=your_real_api_key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL_ID=your_model_id
使用方法
将待处理的 PDF 剧本放入 pdfs/ 文件夹

运行主程序

bash

使用 python main.py（如果已创建）

处理结果保存在 output_json_1/ 文件夹，同名 JSON 文件

处理失败的记录会保存在 error_log/ 文件夹

输出 JSON 格式示例
json
{
  "metadata": {
    "file_id": "01001001_空城计",
    "title": "空城计",
    "alternative_title": "抚琴退敌",
    "period": "三国",
    "total_scenes": 5
  },
  "synopsis": "三国时，马谡死读兵书...",
  "commentary": "此剧唱、做兼优者，首推小叫天...",
  "characters": [...],
  "scenes": [...]
}

配置参数
在 batch_process.py 中可以调整：

pdf_folder：PDF 输入文件夹（默认 pdfs）

output_folder：JSON 输出文件夹（默认 output_json_1）

error_folder：错误日志文件夹（默认 error_log）

semaphore：并发数（默认 1，避免限流）

await asyncio.sleep(3)：每个文件处理后的固定等待秒数

在 llm_extractor.py 中可以调整：

max_tokens：API 返回的最大 token 数（默认 8200）

temperature：生成温度（默认 0.1）

重试策略：stop_after_attempt(5)，指数退避 min=10, max=60

文件结构
text
.
├── batch_process.py        # 批处理主程序（含情节/注释/别名提取）
├── llm_extractor.py        # 大模型调用与 JSON 解析（含重试、截断处理）
├── schema.py               # 系统提示词和 JSON Schema（含 alternative_title）
├── pdf_processor.py        # PDF 文本提取与清洗
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
├── pdfs/                   # 存放待处理的 PDF 文件
├── output_json_1/          # 输出的 JSON 文件
├── error_log/              # 错误日志
└── README.md

注意事项
限流处理：代码默认采用串行（并发=1）且每个文件后等待 3 秒，适合大多数 API 配额（如 20 RPM）。如果您的 API 配额更高，可自行调整并发和等待时间。

情节与注释：自动识别 情节、注释 标题（支持冒号），并在遇到 根据《戏考》、【第X场】、## 或空行时停止，避免误包含正文。

别名：支持 （一名XXX）、一名XXX 等常见格式，提取后存入 metadata.alternative_title。

API 调用会产生费用，请合理控制总处理量。