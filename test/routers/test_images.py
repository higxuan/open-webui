import json

from open_webui.routers.images import (
    apply_image_edit_defaults,
    build_responses_image_input,
    build_responses_image_tool,
    extract_response_image_b64,
    has_responses_image_generation_config,
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


def test_apply_image_edit_defaults_reuses_responses_generation_connection():
    values = {
        'ENABLE_IMAGE_GENERATION': True,
        'IMAGE_GENERATION_ENGINE': 'openai',
        'IMAGE_GENERATION_MODEL': 'gpt-5.5',
        'IMAGES_OPENAI_API_BASE_URL': 'https://newapi.example/v1',
        'IMAGES_OPENAI_API_KEY': 'sk-generation',
        'IMAGES_OPENAI_API_VERSION': '',
        'IMAGES_OPENAI_API_PARAMS': {'api_type': 'responses'},
        'ENABLE_IMAGE_EDIT': False,
        'IMAGE_EDIT_ENGINE': 'openai',
        'IMAGE_EDIT_MODEL': '',
        'IMAGE_EDIT_SIZE': '',
        'IMAGES_EDIT_OPENAI_API_BASE_URL': 'https://api.openai.com/v1',
        'IMAGES_EDIT_OPENAI_API_KEY': '',
        'IMAGES_EDIT_OPENAI_API_VERSION': '',
    }

    normalized = apply_image_edit_defaults(values)

    assert normalized['ENABLE_IMAGE_EDIT'] is True
    assert normalized['IMAGE_EDIT_ENGINE'] == 'openai'
    assert normalized['IMAGE_EDIT_MODEL'] == 'gpt-5.5'
    assert normalized['IMAGES_EDIT_OPENAI_API_BASE_URL'] == 'https://newapi.example/v1'
    assert normalized['IMAGES_EDIT_OPENAI_API_KEY'] == 'sk-generation'


def test_has_responses_image_generation_config_accepts_json_string_params():
    assert has_responses_image_generation_config(
        {
            'ENABLE_IMAGE_GENERATION': True,
            'IMAGE_GENERATION_ENGINE': 'openai',
            'IMAGES_OPENAI_API_PARAMS': '{"api_type":"responses"}',
        }
    )
