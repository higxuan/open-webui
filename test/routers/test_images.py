import json

from open_webui.routers.images import extract_response_image_b64


def test_extract_response_image_b64_uses_latest_partial_image():
    first = 'aW1hZ2UtMQ=='
    second = 'aW1hZ2UtMg=='
    stream = '\n'.join(
        [
            f'data: {json.dumps({"type": "response.image_generation_call.partial_image", "partial_image_b64": first})}',
            f'data: {json.dumps({"type": "response.image_generation_call.partial_image", "partial_image_b64": second})}',
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
