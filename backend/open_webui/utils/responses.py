import json
import time
from uuid import uuid4

from open_webui.utils.response import normalize_usage


def response_id() -> str:
    return f'resp_{uuid4().hex}'


def message_id(prefix: str = 'msg') -> str:
    return f'{prefix}_{uuid4().hex}'


def _content_part_to_text(part: dict) -> str:
    if not isinstance(part, dict):
        return str(part)

    if part.get('type') in ('input_text', 'output_text', 'text'):
        return part.get('text', '')

    if part.get('type') == 'image_url':
        image_url = part.get('image_url', '')
        if isinstance(image_url, dict):
            image_url = image_url.get('url', '')
        return f'[image: {image_url}]' if image_url else '[image]'

    if part.get('type') == 'input_image':
        image_url = part.get('image_url', '')
        return f'[image: {image_url}]' if image_url else '[image]'

    return part.get('text') or json.dumps(part, ensure_ascii=False)


def responses_input_to_messages(input_value, instructions: str | None = None) -> list[dict]:
    messages: list[dict] = []

    if instructions:
        messages.append({'role': 'system', 'content': instructions})

    if input_value is None:
        return messages

    if isinstance(input_value, str):
        messages.append({'role': 'user', 'content': input_value})
        return messages

    if not isinstance(input_value, list):
        messages.append({'role': 'user', 'content': str(input_value)})
        return messages

    pending_user_parts: list[str] = []

    def flush_pending_user_parts():
        nonlocal pending_user_parts
        if pending_user_parts:
            messages.append({'role': 'user', 'content': '\n'.join(part for part in pending_user_parts if part)})
            pending_user_parts = []

    for item in input_value:
        if isinstance(item, str):
            pending_user_parts.append(item)
            continue

        if not isinstance(item, dict):
            pending_user_parts.append(str(item))
            continue

        item_type = item.get('type')

        if item_type == 'message' or 'role' in item:
            flush_pending_user_parts()
            role = item.get('role', 'user')
            content = item.get('content', '')

            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = '\n'.join(_content_part_to_text(part) for part in content)
            else:
                text = str(content)

            messages.append({'role': role, 'content': text})
        elif item_type == 'function_call':
            flush_pending_user_parts()
            messages.append(
                {
                    'role': 'assistant',
                    'content': '',
                    'tool_calls': [
                        {
                            'id': item.get('call_id') or item.get('id') or message_id('call'),
                            'type': 'function',
                            'function': {
                                'name': item.get('name', ''),
                                'arguments': item.get('arguments', '{}'),
                            },
                        }
                    ],
                }
            )
        elif item_type == 'function_call_output':
            flush_pending_user_parts()
            messages.append(
                {
                    'role': 'tool',
                    'tool_call_id': item.get('call_id', ''),
                    'content': item.get('output', ''),
                }
            )
        elif item_type in ('input_text', 'output_text', 'text'):
            pending_user_parts.append(item.get('text', ''))
        else:
            pending_user_parts.append(_content_part_to_text(item))

    flush_pending_user_parts()
    return messages


def responses_tools_to_chat_tools(tools: list | None) -> list | None:
    if not isinstance(tools, list):
        return tools

    converted = []
    for tool in tools:
        if not isinstance(tool, dict):
            converted.append(tool)
            continue

        if tool.get('type') == 'function' and 'function' not in tool:
            function = {
                'name': tool.get('name', ''),
                'description': tool.get('description', ''),
                'parameters': tool.get('parameters', {}),
            }
            if 'strict' in tool:
                function['strict'] = tool['strict']
            converted.append({'type': 'function', 'function': function})
        else:
            converted.append(tool)

    return converted


def responses_payload_to_chat_payload(payload: dict, previous_messages: list[dict] | None = None) -> dict:
    chat_payload = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            'input',
            'instructions',
            'max_output_tokens',
            'text',
            'truncation',
            'store',
            'metadata',
            'reasoning',
            'previous_response_id',
        }
    }

    new_messages = responses_input_to_messages(payload.get('input'), payload.get('instructions'))
    if previous_messages:
        if payload.get('instructions'):
            previous_messages = [msg for msg in previous_messages if msg.get('role') != 'system']
        chat_payload['messages'] = [*previous_messages, *new_messages]
    else:
        chat_payload['messages'] = new_messages

    if 'max_output_tokens' in payload:
        chat_payload['max_tokens'] = payload['max_output_tokens']

    if 'tools' in chat_payload:
        chat_payload['tools'] = responses_tools_to_chat_tools(chat_payload['tools'])

    reasoning = payload.get('reasoning')
    if isinstance(reasoning, dict) and reasoning.get('effort'):
        chat_payload['reasoning_effort'] = reasoning.get('effort')

    return chat_payload


def chat_message_to_responses_output(message: dict | None, fallback_text: str = '') -> list[dict]:
    if not message:
        message = {}

    output = message.get('output')
    if isinstance(output, list) and output:
        return output

    content = message.get('content', fallback_text)
    if isinstance(content, list):
        text = '\n'.join(_content_part_to_text(part) for part in content)
    else:
        text = content or ''

    return [
        {
            'type': 'message',
            'id': message_id('msg'),
            'status': 'completed',
            'role': 'assistant',
            'content': [{'type': 'output_text', 'text': text}],
        }
    ]


def responses_output_text(output: list | None) -> str:
    text_parts: list[str] = []
    for item in output or []:
        if not isinstance(item, dict) or item.get('type') != 'message':
            continue

        content = item.get('content', []) or []
        if isinstance(content, str):
            text_parts.append(content)
            continue
        if isinstance(content, dict):
            content = [content]

        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and (
                part.get('type') in ('input_text', 'output_text', 'text') or 'text' in part
            ):
                value = part.get('text', '')
                text_parts.append(value if isinstance(value, str) else str(value))

    return ''.join(text_parts)


def chat_response_to_responses_response(
    *,
    id: str,
    model: str,
    output: list,
    usage: dict | None = None,
    metadata: dict | None = None,
    instructions: str | None = None,
    previous_response_id: str | None = None,
    status: str = 'completed',
) -> dict:
    now = int(time.time())
    normalized_usage = normalize_usage(usage or {})

    response = {
        'id': id,
        'object': 'response',
        'created_at': now,
        'status': status,
        'model': model,
        'output': output,
        'output_text': responses_output_text(output),
        'parallel_tool_calls': True,
        'tool_choice': 'auto',
        'tools': [],
        'metadata': metadata or {},
        'usage': {
            'input_tokens': normalized_usage.get('input_tokens', 0),
            'output_tokens': normalized_usage.get('output_tokens', 0),
            'total_tokens': normalized_usage.get('total_tokens', 0),
        },
    }

    if instructions:
        response['instructions'] = instructions
    if previous_response_id:
        response['previous_response_id'] = previous_response_id

    return response
