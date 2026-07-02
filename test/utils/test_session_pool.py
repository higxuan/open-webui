import aiohttp
import pytest

from open_webui.utils.session_pool import stream_wrapper


class OversizedLineContent:
    def __aiter__(self):
        raise aiohttp.http_exceptions.LineTooLong(b'data: ...', 131072)

    async def iter_chunked(self, chunk_size):
        yield b'data: ' + (b'x' * 200000) + b'\n\n'


class FakeResponse:
    def __init__(self):
        self.content = OversizedLineContent()
        self.closed = False

    def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_stream_wrapper_reads_raw_streams_in_chunks_for_oversized_sse_lines():
    response = FakeResponse()

    chunks = [chunk async for chunk in stream_wrapper(response)]

    assert chunks == [b'data: ' + (b'x' * 200000) + b'\n\n']
    assert response.closed
