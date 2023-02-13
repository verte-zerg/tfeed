import http

import pytest
from aiohttp.test_utils import TestClient

from tfeed.app import Config, create_app


@pytest.fixture
async def client(aiohttp_client) -> TestClient:
    """Create test client."""
    config = Config(host='localhost', port=0, ttl=1)
    app = create_app(config)
    return await aiohttp_client(app)


@pytest.mark.parametrize(
    'channel', (
        'newyorktimes',
        'wildlife',
        'privateart',
        'netflix',
        'quote',
        'wallpaperselection',
        'internationalgeographic',
        'science',
        'onlyfood',
        'memes',
        'askmenow',
        'dailychannels',
    ),
)
async def test_handler(client: TestClient, channel: str) -> None:
    """Test handler."""
    response = await client.get(f'/{channel}')
    assert response.status == http.HTTPStatus.OK
