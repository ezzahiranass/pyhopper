from __future__ import annotations

import os
from langchain_openai import ChatOpenAI


def get_llm():

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
        streaming=True,
    )
