# backend/llm_pipeline/llm_client.py
from openai import OpenAI
import logging

logger = logging.getLogger(f'excel_agent.{__name__}')

class LLMClient:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model

    def chat(self, prompt, system=None):
        """
        通用对话接口
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if content is None:
                logger.error("LLM returned None content")
                return ""
            return content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return ""

    def stream_chat(self, prompt, system=None):
        """
        支持流式输出 (SSE)
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        with self.client.chat.completions.stream(
            model=self.model,
            messages=messages,
            temperature=0.3,
        ) as stream:
            for event in stream:
                if event.type == "message.delta":
                    yield event.delta
                elif event.type == "message.completed":
                    break
