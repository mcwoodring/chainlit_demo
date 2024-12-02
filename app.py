import asyncio
from os import environ as env
from types import SimpleNamespace
from dotenv import load_dotenv

import chainlit as cl
import openai

# https://platform.openai.com/docs/models/gpt-4o
_config = SimpleNamespace(
    endpoint_url = "https://api.openai.com/v1",
    model_kwargs = {
        "model": "chatgpt-4o-latest",
        "temperature": 0.3,
        "max_tokens": 500,
    }
)

_globals = SimpleNamespace(
    client = None,
)

@cl.on_message
async def on_message(message: cl.Message):
    response = await _globals.client.chat.completions.create(
        messages=[{"role": "user", "content": message.content}],
        **_config.model_kwargs
    )

    # https://platform.openai.com/docs/guides/chat-completions/response-format
    response_content = response.choices[0].message.content

    await cl.Message(
        content=response_content,
    ).send()

# 'main'
#
load_dotenv()
_globals.client = openai.AsyncClient(api_key=env['OPENAI_API_KEY'], base_url=_config.endpoint_url)
