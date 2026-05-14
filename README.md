
## README.md 内容

```markdown
# 京剧剧本结构化提取工具 (Peking Opera Script Extractor)

批量处理 PDF 格式的京剧剧本，通过大模型（LLM）自动提取角色、场次、台词等结构化信息，输出规范的 JSON 文件。

## 功能特性

- 📄 **PDF 文本提取**：自动从 PDF 中提取剧本纯文本
- 🤖 **智能结构化**：利用大模型识别角色、行当、年龄、性格等元数据
- 🎭 **细粒度解析**：区分唱词（西皮/二黄等板式）、念白、舞台指示
- ⚡ **异步并发**：支持同时处理多个 PDF（默认并发数 5），提升效率
- 🔁 **断点续传**：已生成的 JSON 文件不会重复处理
- 🛡️ **容错机制**：长文本自动截断重试，JSON 解析失败时降级提取

## 环境要求

- Python 3.8+
- 大模型 API（支持 OpenAI 兼容接口，如豆包、DeepSeek 等）
- PDF 解析库（项目使用 `pypdf` 或 `pdfplumber`）

## 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/你的用户名/peking-opera-script-extractor.git
   cd peking-opera-script-extractor
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量  
   复制 `.env.example` 为 `.env`，并填入你的 API 信息：
   ```bash
   cp .env.example .env
   ```
   编辑 `.env`：
   ```ini
   ARK_API_KEY=your_real_api_key
   ARK_BASE_URL=https://your-api-endpoint.com/v1
   ARK_MODEL_ID=your_model_id
   ```

## 使用方法

1. 将待处理的 PDF 剧本放入 `pdfs/` 文件夹
2. 运行主程序
   ```bash
   python batch_process.py
   ```
3. 处理结果保存在 `output_json/` 文件夹，同名 JSON 文件
4. 处理失败的记录会保存在 `error_log/` 文件夹

## 输出 JSON 格式示例

```json
{
  "metadata": {
    "file_id": "01001001_空城计",
    "title": "空城计",
    "period": "三国",
    "total_scenes": 5
  },
  "synopsis": "三国时，马谡失街亭...",
  "commentary": "此剧唱、做兼优者，首推小叫天...",
  "characters": [
    {
      "name": "诸葛亮",
      "role_type": "老生",
      "gender": "男",
      "age_range": "老年",
      "personality_keywords": ["足智多谋", "谨慎镇定"],
      "identity": "蜀汉丞相"
    }
  ],
  "scenes": [
    {
      "scene_id": 1,
      "title": "帐中接报",
      "characters_on_stage": ["诸葛亮", "童儿", "旗牌"],
      "segments": [
        {
          "type": "stage_direction",
          "speaker": null,
          "mode": "",
          "content": "二童儿同上，诸葛亮上。"
        },
        {
          "type": "dialogue",
          "speaker": "诸葛亮",
          "mode": "念",
          "content": "兵扎祁山地，要擒司马懿。"
        },
        {
          "type": "lyric",
          "speaker": "诸葛亮",
          "mode": "西皮摇板",
          "content": "我用兵数十年从来谨慎..."
        }
      ],
      "stats": {
        "line_count": 65,
        "lyric_ratio": 0.062,
        "stage_direction_count": 16
      }
    }
  ]
}
```

## 配置参数

在 `batch_process.py` 中可以调整：

- `pdfs`：PDF 输入文件夹（
- `output_json`：JSON 输出文件夹
- `error_log`：错误日志文件夹
- `semaphore` 数值：并发数（默认 5）

在 `llm_extractor.py` 中可以调整：

- `max_tokens`：API 返回的最大 token 数（默认 8200）
- `temperature`：生成温度（默认 0.1，越低越稳定）

## 文件结构

```
.
├── batch_process.py        # 批处理主程序
├── llm_extractor.py        # 大模型调用与 JSON 解析
├── schema.py               # 系统提示词和 JSON Schema
├── pdf_processor.py        # PDF 文本提取（需自行实现或使用 pypdf/pdfplumber）
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
├── pdfs/                   # 存放待处理的 PDF 文件
├── output_json/            # 输出的 JSON 文件
├── error_log/              # 错误日志
└── README.md
```

## 注意事项

- 请确保 `pdf_processor.py` 中包含 `extract_text_from_pdf` 函数，可使用 `pypdf` 或 `pdfplumber` 实现。
- 长剧本（超过 12000 字符）会被自动截断，保留头尾部分。如果情节或注释位于被截断的中间区域，可能无法提取。建议提取前先用正则单独抓取。
- API 调用会产生费用，请合理控制并发和重试次数。

## 自定义 Schema

编辑 `schema.py` 中的 `SYSTEM_PROMPT` 和 `JSON_SCHEMA_DESCRIPTION`，即可让模型输出你需要的字段。


```


