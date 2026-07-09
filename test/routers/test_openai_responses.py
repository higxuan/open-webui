import json

from open_webui.models.models import BUILTIN_IMAGE_MODEL_ID, Models
from open_webui.routers.openai import (
    _build_openai_chat_request,
    _extract_responses_stream_result,
    _is_responses_stream_required,
    convert_responses_result,
)


def test_is_responses_stream_required_detects_provider_error():
    error = {'error': {'message': 'Stream must be set to true'}}

    assert _is_responses_stream_required(error) is True


def test_extract_responses_stream_result_reads_completed_response():
    response = {
        'id': 'resp_1',
        'model': 'gpt-5.5',
        'output': [
            {
                'type': 'message',
                'role': 'assistant',
                'content': [{'type': 'output_text', 'text': '{"name":"edit_image"}'}],
            }
        ],
    }
    stream = '\n'.join(
        [
            f'data: {json.dumps({"type": "response.completed", "response": response})}',
            'data: [DONE]',
        ]
    )

    result = convert_responses_result(_extract_responses_stream_result(stream))

    assert result['choices'][0]['message']['content'] == '{"name":"edit_image"}'


def test_builtin_image_model_requests_responses_api():
    model = Models._get_builtin_model_by_id(BUILTIN_IMAGE_MODEL_ID)

    assert model.meta.model_dump().get('response_api') is True


def test_responses_chat_request_forces_upstream_streaming_for_non_stream_call():
    request_url, payload, _ = _build_openai_chat_request(
        'https://newapi.example/v1',
        {
            'model': 'gpt-5.5',
            'messages': [{'role': 'user', 'content': 'title this'}],
            'stream': False,
        },
        {'api_type': 'responses'},
        use_responses=True,
    )

    assert request_url == 'https://newapi.example/v1/responses'
    assert payload['stream'] is True
