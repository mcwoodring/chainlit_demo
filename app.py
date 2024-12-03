import asyncio
from os import environ as env
from types import SimpleNamespace
from dotenv import load_dotenv

import chainlit as cl
from chainlit.cli import run_chainlit
import openai

load_dotenv()

# _config_open_ai = SimpleNamespace(
#     endpoint_url = "https://api.openai.com/v1",
#     model_kwargs = {
#         "model": "chatgpt-4o-latest",   # https://platform.openai.com/docs/models/gpt-4o
#         "temperature": 0.3,
#         "max_tokens": 500,
#     },
#     message_history_key = 'message_history',
# )
# _client_open_ai = openai.AsyncClient(api_key=env['OPENAI_API_KEY'], base_url=_config_open_ai.endpoint_url)


_config_runpod = SimpleNamespace(
    endpoint_url = f"https://api.runpod.ai/v2/{env['RUNPOD_SERVERLESS_ID']}/openai/v1",
    model_kwargs = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "temperature": 0.3,
        "max_tokens": 500
    },
    message_history_key = 'message_history',
)
_client_runpod = openai.AsyncClient(api_key=env['RUNPOD_API_KEY'], base_url=_config_runpod.endpoint_url)


_config = _config_runpod
_client = _client_runpod

# xref https://docs.chainlit.io/concepts/chat-lifecycle
#
@cl.on_chat_start
def on_chat_start():
    # xref https://docs.chainlit.io/concepts/user-session
    #
    pass


# xref https://docs.chainlit.io/concepts/chat-lifecycle
#
@cl.on_message
async def on_message(message: cl.Message):
    # Maintain an array of messages in the user session
    message_history = cl.user_session.get(_config.message_history_key, [])
    message_history.append({"role": "user", "content": message.content})

    response_message = cl.Message(content="")
    await response_message.send()
    
    # Pass in the full message history for each request
    stream = await _client.chat.completions.create(
        messages=message_history, 
        stream=True,
        **_config.model_kwargs
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)

    await response_message.update()

    # Record the AI's response in the history
    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set(_config.message_history_key, message_history)


# xref https://docs.chainlit.io/concepts/chat-lifecycle
#
@cl.on_stop
def on_stop():
    pass


async def main():
    run_chainlit(__file__)


if __name__ == "__main__":
    asyncio.run(main())