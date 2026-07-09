import json

from open_webui.routers.images import (
    build_responses_image_input,
    build_responses_image_tool,
    extract_response_image_b64,
)


def test_extract_response_image_b64_uses_latest_partial_image():
    first = 'aW1hZ2UtMQ=='
    second = 'aW1hZ2UtMg=='
    first_event = {'type': 'response.image_generation_call.partial_image', 'partial_image_b64': first}
    second_event = {'type': 'response.image_generation_call.partial_image', 'partial_image_b64': second}
    stream = '\n'.join(
        [
            f'data: {json.dumps(first_event)}',
            f'data: {json.dumps(second_event)}',
            'data: [DONE]',
        ]
    )

    assert extract_response_image_b64(stream) == second


def test_extract_response_image_b64_reads_completed_response_output():
    image = 'aW1hZ2U='
    stream = (
        'data:'
        + json.dumps(
            {
                'type': 'response.completed',
                'response': {
                    'output': [
                        {
                            'type': 'image_generation_call',
                            'result': image,
                        }
                    ]
                },
            }
        )
    )

    assert extract_response_image_b64(stream) == image


def test_build_responses_image_input_includes_reference_images():
    prompt = 'Generate a new avatar from this reference'
    images = ['data:image/png;base64,aW1nMQ==', 'data:image/jpeg;base64,aW1nMg==']

    input_items = build_responses_image_input(prompt, images)

    assert input_items == [
        {
            'role': 'user',
            'content': [
                {'type': 'input_text', 'text': prompt},
                {'type': 'input_image', 'image_url': images[0]},
                {'type': 'input_image', 'image_url': images[1]},
            ],
        }
    ]


def test_build_responses_image_tool_merges_configured_tool_options():
    assert build_responses_image_tool('1024x1024', {'tool': {'quality': 'high'}}) == {
        'type': 'image_generation',
        'size': '1024x1024',
        'quality': 'high',
    }
