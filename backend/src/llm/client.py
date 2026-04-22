from __future__ import annotations

import os
import re
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class LLMClient:
    model: str = "gpt-4o"

    def __post_init__(self) -> None:
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.vveai.com/v1"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    def build_context(self, schema_summary: str) -> str:
        return schema_summary

    def _system_prompt(self) -> str:
        return (
            "你是一个严格的 PostgreSQL SQL 生成助手。"
            "你只能使用用户给定的 Schema 上下文中明确存在的表名和列名。"
            "严禁臆造、猜测、推断不存在的字段名，例如 name、title、fullname 等。"
            "如果上下文中没有明确列名，不要编造；必须基于已知列名生成 SQL。"
            "如果无法根据上下文唯一确定表或列，请返回最保守、最简单的 SELECT 语句。"
            "只输出 SQL 本身，不要输出解释、注释、Markdown 或代码块。"
        )

    def _strip_code_fences(self, content: str) -> str:
        cleaned = content.strip()
        cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def generate_sql(self, prompt: str, context: str) -> str:
        response = self.client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", self.model),
            messages=[
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": f"Schema 上下文:\n{context}\n\n用户需求:\n{prompt}",
                },
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        return self._strip_code_fences(content)
