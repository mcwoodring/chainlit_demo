import asyncio
import base64
from os import environ as env
from types import SimpleNamespace
from dotenv import load_dotenv

import chainlit as cl
from chainlit.cli import run_chainlit
import openai

load_dotenv()

_configurations = {
    'openai': SimpleNamespace(
        ai_name = 'OpenAI',
        endpoint_url = 'https://api.openai.com/v1',
        api_key = env['OPENAI_API_KEY'],
        model_kwargs = {
            'model': 'chatgpt-4o-latest',   # https://platform.openai.com/docs/models/gpt-4o
            'temperature': 0.3,
            'max_tokens': 500,
        },
        message_history_key = 'message_history',
    ),
    'runpod': SimpleNamespace(
        ai_name = 'Mistral',
        endpoint_url = f"https://api.runpod.ai/v2/{env['RUNPOD_SERVERLESS_ID']}/openai/v1",
        api_key = env['RUNPOD_API_KEY'],
        model_kwargs = {
            'model': 'mistralai/Mistral-7B-Instruct-v0.3',
            'temperature': 0.3,
            'max_tokens': 500
        },
        message_history_key = 'message_history',
    )
}

_config = _configurations['openai']
_client = openai.AsyncClient(api_key=_config.api_key, base_url=_config.endpoint_url)

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

    images = [file for file in message.elements if 'image' in file.mime] if message.elements else []

    if images:
        # Read the first image and encode it to base64
        with open(images[0].path, 'rb') as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        message_history.append({
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': message.content if message.content else "What's in this image?"
                },
                {
                    'type': 'image_url',
                    'image_url': {
                        'url': f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })
    else:
        message_history.append({'role': 'user', 'content': message.content})

    response_message = cl.Message(content='')
    await response_message.send()
    
    # Pass in the full message history for each request
    stream = await _client.chat.completions.create(
        messages=message_history, 
        stream=True,
        **_config.model_kwargs
    )

    prefix = f"[{_config.ai_name}] "
    prefix_streamed = False

    async for part in stream:
        if token := part.choices[0].delta.content or '':
            if not prefix_streamed:
                await response_message.stream_token(prefix)
                prefix_streamed = True

            await response_message.stream_token(token)

    await response_message.update()

    # Record the AI's response in the history
    message_history.append({'role': 'assistant', 'content': response_message.content})
    cl.user_session.set(_config.message_history_key, message_history)


# xref https://docs.chainlit.io/concepts/chat-lifecycle
#
@cl.on_stop
def on_stop():
    pass


async def main():
    run_chainlit(__file__)


if __name__ == '__main__':
    asyncio.run(main())