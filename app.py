import asyncio
from os import environ as env
from types import SimpleNamespace
from dotenv import load_dotenv

import chainlit as cl
from chainlit.cli import run_chainlit
import openai


_config = SimpleNamespace(
    endpoint_url = "https://api.openai.com/v1",
    model_kwargs = {
        "model": "chatgpt-4o-latest",   # https://platform.openai.com/docs/models/gpt-4o
        "temperature": 0.3,
        "max_tokens": 500,
    },
    msg_counter_key = 'msg_counter',
)
_client = openai.AsyncClient(api_key=env['OPENAI_API_KEY'], base_url=_config.endpoint_url)


# xref https://docs.chainlit.io/concepts/chat-lifecycle
#
@cl.on_chat_start
def on_chat_start():
    # xref https://docs.chainlit.io/concepts/user-session
    #
    cl.user_session.set(_config.msg_counter_key, 0)


# xref https://docs.chainlit.io/concepts/chat-lifecycle
#
@cl.on_message
async def on_message(message: cl.Message):
    # xref https://docs.chainlit.io/concepts/user-session
    #
    msg_counter = cl.user_session.get(_config.msg_counter_key)
    msg_counter += 1
    cl.user_session.set(_config.msg_counter_key, msg_counter)
                        
    response = await _client.chat.completions.create(
        messages=[{"role": "user", "content": message.content}],
        **_config.model_kwargs
    )
    
    # xref https://platform.openai.com/docs/guides/chat-completions/response-format
    #
    response_content = f"[{msg_counter}] {response.choices[0].message.content}"

    await cl.Message(
        content=response_content,
    ).send()


# xref https://docs.chainlit.io/concepts/chat-lifecycle
#
@cl.on_stop
def on_stop():
    pass


async def main():
    load_dotenv()
    run_chainlit(__file__)


if __name__ == "__main__":
    asyncio.run(main())