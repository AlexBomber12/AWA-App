from services.common.llm import generate


async def draft_email(prompt: str) -> str:
    return await generate(prompt)
