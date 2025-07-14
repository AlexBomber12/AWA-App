from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import subprocess

MODEL = "/models/llama3-q4_K_M.gguf"
BIN = "/llama/main"


class Req(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7


app = FastAPI()


@app.post("/llm")
def gen(r: Req) -> Dict[str, str]:
    try:
        out = subprocess.check_output(
            [
                BIN,
                "-m",
                MODEL,
                "-p",
                r.prompt,
                "-n",
                str(r.max_tokens),
                "-t",
                "8",
                "-ngl",
                "1",
                "-temp",
                str(r.temperature),
                "-c",
                "2048",
                "--silent-prompt",
                "--silent-eos",
            ],
            text=True,
        )
        return {"completion": out.strip()}
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, e.stderr)
