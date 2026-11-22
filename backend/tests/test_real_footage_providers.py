import os
import json
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.api_schemas import SceneDetail, FootageClip, VisualPromptStyle
from app.providers.pexels_provider import PexelsProvider
from app.providers.pixabay_provider import PixabayProvider
from app.services.footage_service import footage_service
from app.services.query_intelligence import query_intelligence
from app.services.safety_service import safety_service
from app.config import settings

client = TestClient(app)

@pytest.mark.asyncio
async def test_pexels_parses_video_files_and_prefers_1080p(monkeypatch):
    """
    Verifies that PexelsProvider parses the API response and selects 1080p MP4.
    """
    mock_response = {
        "videos": [
            {
                "id": 998811,
                "duration": 6.5,
                "url": "https://www.pexels.com/video/998811/",
                "user": {"name": "Pexels Filmmaker", "url": "https://pexels.com/@filmmaker"},
                "video_files": [
                    {"id": 1, "file_type": "video/mp4", "width": 1280, "height": 720, "fps": 30.0, "link": "https://pexels.com/720p.mp4"},
                    {"id": 2, "file_type": "video/mp4", "width": 1920, "height": 1080, "fps": 30.0, "link": "https://pexels.com/1080p.mp4"}
                ]
            }
        ]
    }

    class MockHttpxResponse:
        status_code = 200
        def json(self):
            return mock_response

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, *args, **kwargs):
            return MockHttpxResponse()

    monkeypatch.setattr("app.providers.pexels_provider.httpx.AsyncClient", MockAsyncClient)
    monkeypatch.setattr(settings, "pexels_api_key", "test_key_pexels_valid")

    provider = PexelsProvider()
    assert provider.is_available is True

    clips = await provider.search_footage("coffee plantation", min_duration=3.0, limit=2)
    assert len(clips) == 1
    clip = clips[0]
    assert clip.clip_id == "pexels_998811"
    assert clip.download_url == "https://pexels.com/1080p.mp4"
    assert clip.height == 1080
    assert clip.is_commercial_cleared is True
    assert "Pexels" in clip.licence

@pytest.mark.asyncio
async def test_pixabay_parses_videos_and_large_stream(monkeypatch):
    """
    Verifies that PixabayProvider parses the API response and extracts large stream URL and tags.
    """
    mock_response = {
        "hits": [
            {
                "id": 776655,
                "duration": 7.0,
                "pageURL": "https://pixabay.com/videos/nature-776655/",
                "user": "NatureCreator",
                "tags": "nature, green, forest, trees",
                "videos": {
                    "large": {"url": "https://pixabay.com/nature_large.mp4", "width": 1920, "height": 1080},
                    "medium": {"url": "https://pixabay.com/nature_medium.mp4", "width": 1280, "height": 720}
                }
            }
        ]
    }

    class MockHttpxResponse:
        status_code = 200
        def json(self):
            return mock_response

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, *args, **kwargs):
            return MockHttpxResponse()

    monkeypatch.setattr("app.providers.pixabay_provider.httpx.AsyncClient", MockAsyncClient)
    monkeypatch.setattr(settings, "pixabay_api_key", "test_key_pixabay_valid")

    provider = PixabayProvider()
    assert provider.is_available is True

    clips = await provider.search_footage("forest nature", min_duration=3.0, limit=2)
    assert len(clips) == 1
    clip = clips[0]
    assert clip.clip_id == "pixabay_776655"
    assert clip.download_url == "https://pixabay.com/nature_large.mp4"
    assert "forest" in clip.tags
    assert clip.is_commercial_cleared is True

@pytest.mark.asyncio
async def test_fallback_to_pixabay_when_pexels_fails(monkeypatch):
    """
    When Pexels returns 429/empty, Pixabay results are pooled and returned.
    """
    pixabay_clip = FootageClip(
        clip_id="pixabay_fallback_1",
        provider="Pixabay",
        source_url="https://pixabay.com/video/1",
        download_url="https://pixabay.com/video1.mp4",
        width=1920,
        height=1080,
        duration=5.0,
        fps=30.0,
        licence="Pixabay License",
        attribution="Pixabay Artist",
        is_commercial_cleared=True,
        tags=["coffee", "brewing"]
    )

    async def mock_pexels_search(*args, **kwargs):
        return []

    async def mock_pixabay_search(*args, **kwargs):
        return [pixabay_clip]

    monkeypatch.setattr(settings, "pexels_api_key", "mock_pexels_key")
    monkeypatch.setattr(settings, "pixabay_api_key", "mock_pixabay_key")
    monkeypatch.setattr(footage_service.pexels_provider, "search_footage", mock_pexels_search)
    monkeypatch.setattr(footage_service.pixabay_provider, "search_footage", mock_pixabay_search)

    scene = SceneDetail(
        scene_number=1,
        narration_text="Steaming rich coffee in the morning.",
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
        visual_description="cinematic shot: coffee brewing steam",
        search_query="coffee brewing"
    )

    seen = set()
    selected = await footage_service.find_best_footage_for_scene(scene, seen)
    assert selected.provider == "Pixabay"
    assert selected.clip_id == "pixabay_fallback_1"

@pytest.mark.asyncio
async def test_fallback_to_mock_when_both_fail_with_explicit_warning(monkeypatch):
    """
    When both external providers fail or are unconfigured, MockProvider is used as
    last-resort fallback with an explicit warning recorded.
    """
    async def mock_empty_search(*args, **kwargs):
        return []

    monkeypatch.setattr(settings, "pexels_api_key", "mock_pexels_key")
    monkeypatch.setattr(settings, "pixabay_api_key", "mock_pixabay_key")
    monkeypatch.setattr(footage_service.pexels_provider, "search_footage", mock_empty_search)
    monkeypatch.setattr(footage_service.pixabay_provider, "search_footage", mock_empty_search)

    scene = SceneDetail(
        scene_number=1,
        narration_text="Steaming rich coffee in the morning.",
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
        visual_description="cinematic shot: coffee brewing steam",
        search_query="coffee brewing"
    )

    seen = set()
    selected = await footage_service.find_best_footage_for_scene(scene, seen)
    assert selected.provider == "MockProvider"
    assert any("mock fallback used" in w for w in scene.warnings)

def test_avoid_terms_filter_rejects_matching_candidate_clip():
    """
    Strict avoid terms: if clip tags contain avoid word, it is rejected.
    """
    clip = FootageClip(
        clip_id="test_clip_1",
        provider="Pexels",
        source_url="https://pexels.com/1",
        download_url="https://pexels.com/1.mp4",
        width=1920,
        height=1080,
        duration=5.0,
        fps=30.0,
        licence="Pexels License",
        attribution="Creator",
        is_commercial_cleared=True,
        tags=["urban", "city", "traffic", "rush"]
    )

    # Avoid "traffic"
    is_safe, reason = safety_service.evaluate_candidate_clip(clip, avoid_list=["traffic", "car"])
    assert is_safe is False
    assert "traffic" in reason

    # No avoid match
    is_safe_clean, _ = safety_service.evaluate_candidate_clip(clip, avoid_list=["nature", "animals"])
    assert is_safe_clean is True

def test_homonym_disambiguation_bank_cloud_mouse_python():
    """
    Validates contextual disambiguation for double-meaning terms.
    """
    # 1. Bank
    bank_money = query_intelligence.disambiguate_query("The investor deposited cash into the savings bank account.")
    assert any(term in bank_money.lower() for term in ("financial", "bank", "banking"))
    
    bank_river = query_intelligence.disambiguate_query("Wildflowers grew along the green river bank.")
    assert "river" in bank_river.lower()

    # 2. Cloud
    cloud_tech = query_intelligence.disambiguate_query("The company migrated its database to the secure AWS cloud server.")
    assert any(term in cloud_tech.lower() for term in ("server", "technology", "data"))

    cloud_sky = query_intelligence.disambiguate_query("Sunlight broke through the white fluffy cloud formations.")
    assert "cloud" in cloud_sky.lower() or "sky" in cloud_sky.lower()

    # 3. Python
    py_code = query_intelligence.disambiguate_query("The software engineer wrote a python programming script for machine learning.")
    assert any(term in py_code.lower() for term in ("developer", "coding", "software", "code"))

    py_snake = query_intelligence.disambiguate_query("A green python slithered through the rainforest canopy.")
    assert any(term in py_snake.lower() for term in ("snake", "wildlife", "python"))

def test_abstract_metaphors_conversion():
    """
    Validates conversion of abstract philosophical thoughts and economic metaphors
    into physical concrete visual queries.
    """
    # Inflation
    inflation_query = query_intelligence.disambiguate_query("Families struggle with soaring inflation and rising prices.")
    assert any(term in inflation_query.lower() for term in ("supermarket", "grocery", "prices", "wallet"))

    # Burning midnight oil
    midnight_query = query_intelligence.disambiguate_query("The founder was burning the midnight oil to finish the release.")
    assert any(term in midnight_query.lower() for term in ("desk", "lamp", "office", "worker"))

def test_human_rating_endpoint():
    """
    Tests POST /api/v1/jobs/{job_id}/rate endpoint and confirms storage persistence.
    """
    job_id = "test_rate_job_123"
    payload = {
        "ratings": {"1": 5, "2": 4},
        "notes": "Excellent alignment on scene 1; scene 2 was acceptable.",
        "overall_score": 4.5
    }

    res = client.post(f"/api/v1/jobs/{job_id}/rate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == job_id
    assert data["overall_score"] == 4.5

    rating_file = settings.storage_dir / "ratings" / f"{job_id}.json"
    assert rating_file.exists()
    saved = json.loads(rating_file.read_text(encoding="utf-8"))
    assert saved["ratings"]["1"] == 5
    assert saved["notes"] == "Excellent alignment on scene 1; scene 2 was acceptable."
