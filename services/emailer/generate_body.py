import os
import httpx

LLM_URL = os.getenv("LLM_URL", "http://llm:8000/llm")


async def local_llm(prompt: str, temp: float = 0.7, tokens: int = 256) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            LLM_URL, json={"prompt": prompt, "temperature": temp, "max_tokens": tokens}
        )
        r.raise_for_status()
        return r.json()["completion"]


async def generate_body(prompt: str, *, temperature: float = 0.7, max_tokens: int = 256) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        try:
            from openai import AsyncOpenAI
        except Exception:
            key = None
    if key:
        client = AsyncOpenAI(api_key=key)
        resp = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content
    return await local_llm(prompt, temp=temperature, tokens=max_tokens)
