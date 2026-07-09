import asyncio

from open_webui.utils import middleware


def test_image_edit_enabled_for_responses_generation_config(monkeypatch):
    async def fake_get_many(*keys):
        return {
            'images.edit.enable': False,
            'image_generation.enable': True,
            'image_generation.engine': 'openai',
            'image_generation.openai.params': {'api_type': 'responses'},
        }

    monkeypatch.setattr(middleware.Config, 'get_many', fake_get_many)

    assert asyncio.run(middleware.is_image_edit_enabled_for_generation_config()) is True


def test_image_edit_enabled_uses_explicit_edit_switch(monkeypatch):
    async def fake_get_many(*keys):
        return {
            'images.edit.enable': True,
            'image_generation.enable': False,
            'image_generation.engine': '',
            'image_generation.openai.params': {},
        }

    monkeypatch.setattr(middleware.Config, 'get_many', fake_get_many)

    assert asyncio.run(middleware.is_image_edit_enabled_for_generation_config()) is True
