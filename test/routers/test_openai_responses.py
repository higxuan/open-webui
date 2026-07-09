import json

from open_webui.models.models import BUILTIN_IMAGE_MODEL_ID, Models
from open_webui.routers.openai import (
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
