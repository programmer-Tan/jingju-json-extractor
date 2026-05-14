# schema.py
"""通用京剧剧本结构化JSON Schema"""

JSON_SCHEMA_DESCRIPTION = """
{
  "metadata": {
    "file_id": "字符串，PDF文件名（不含扩展名）",
    "title": "字符串，剧本名称",
    "period": "字符串，历史时期（如三国、唐朝等，未知则空）",
    "total_scenes": "整数，总场次数"
  },
  "characters": [
    {
      "name": "字符串，角色名",
      "role_type": "字符串，行当大类：老生/小生/武生/旦/净/丑/末",
      "role_subtype": "字符串，细分行当（无则空）",
      "gender": "字符串，男/女/未知",
      "age_range": "字符串，老年/中年/青年/少年/未知",
      "personality_keywords": ["字符串数组，最多3个"],
      "identity": "字符串，身份描述"
    }
  ],
  "scenes": [
    {
      "scene_id": "整数，从1开始",
      "title": "字符串，场次标题（无则空）",
      "characters_on_stage": ["字符串数组，本场所有角色名"],
      "segments": [
        {
          "type": "字符串，dialogue/lyric/stage_direction",
          "speaker": "字符串，说话人（非对话则为null）",
          "mode": "字符串，板式或念白类型（可选）",
          "content": "字符串，内容"
        }
      ],
      "stats": {
        "line_count": "整数",
        "lyric_ratio": "浮点数",
        "stage_direction_count": "整数"
      }
    }
  ]
}
"""

SYSTEM_PROMPT = f"""你是一位京剧剧本分析专家。请根据用户提供的剧本文本，严格按照以下JSON Schema输出结构化数据。
只输出JSON对象，不要包含任何额外解释或注释。

输出格式定义：
{JSON_SCHEMA_DESCRIPTION}

提取规则：
1. 角色行当：根据年龄、性别、性格、身份推断。老生(稳重老年男性)、小生(青年才俊)、武生(勇武青年)、旦(女性)、净(花脸、粗犷或奸诈)、丑(诙谐或卑微)。
2. 场次划分：寻找“【第X场】”、“第X场”或“(XX上)”等标记。若无标记，按人物上场/下场变化划分。
3. 角色名：从“主要角色”段落、上场提示、对话标记中提取所有角色。
4. 对话归属：正确归属说话人。
5. 唱腔标记：遇到“（西皮摇板）”等，对应segment的type设为"lyric"，mode记录板式。
6. 统计：line_count按行数估算；lyric_ratio = 唱腔行数/总行数；stage_direction_count统计括号内动作提示数量。
7. 缺失字段用空字符串""、空数组[]或0，不要省略。
"""