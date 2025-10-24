from awa_common.llm import generate


async def draft_email(prompt: str) -> str:
    result = await generate(prompt)
    if not isinstance(result, str):
        raise TypeError("generate() returned a non-string result")
    return result
