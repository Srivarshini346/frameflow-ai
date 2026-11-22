import pytest
import time
import base64
import wave
import struct
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.audio_service import audio_service
from app.services.scene_engine import scene_engine
from app.services.footage_service import footage_service
from app.services.video_engine import video_engine
from app.services.caption_service import caption_service
from app.models.api_schemas import (
    BrollJobCreateRequest, VoiceConfig, LanguageCode, AspectRatio, CaptionConfig, SceneDetail
)
from app.core.exceptions import ValidationError, AudioProcessingError

client = TestClient(app)

# Helper to create a small valid WAV file in memory
def create_test_wav(duration_s=2.0, silent=False):
    sr = 22050
    n_samples = int(duration_s * sr)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        with wave.open(tf.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            data = bytearray()
            for i in range(n_samples):
                if silent:
                    val = 0
                else:
                    # 440 Hz audible sine wave
                    import math
                    val = int(math.sin(2 * math.pi * 440 * (i / sr)) * 10000)
                data.extend(struct.pack("<h", val))
            wf.writeframes(data)
        return tf.name

# 1. Text script submission
def test_01_text_script_submission():
    payload = {
        "script_text": "Artificial intelligence creates personalised learning for students in modern classrooms.",
        "aspect_ratios": ["16:9", "9:16", "1:1"]
    }
    res = client.post("/api/v1/broll/jobs", json=payload)
    assert res.status_code == 202
    data = res.json()
    assert "job_id" in data
    assert data["status"] in ("queued", "running")
    assert "X-Correlation-ID" in res.headers

# 2. Audio upload validation
def test_02_audio_upload_validation():
    wav_path = create_test_wav(duration_s=2.0, silent=False)
    props = audio_service.validate_audio_file(wav_path)
    assert props["duration"] >= 1.9
    assert props["is_silent"] is False
    Path(wav_path).unlink(missing_ok=True)

# 3. Empty script validation
def test_03_empty_script_rejected():
    res = client.post("/api/v1/broll/jobs", json={"script_text": "   "})
    assert res.status_code in (400, 422)
    err = res.json()
    assert "error" in err

# 4. Unsupported audio format
def test_04_unsupported_audio_format():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        tf.write(b"not an audio file")
        tf_name = tf.name
    with pytest.raises(ValidationError):
        audio_service.validate_audio_file(tf_name)
    Path(tf_name).unlink(missing_ok=True)

# 5. Silent audio detection
def test_05_silent_audio_rejected():
    silent_wav = create_test_wav(duration_s=2.0, silent=True)
    with pytest.raises(AudioProcessingError):
        audio_service.validate_audio_file(silent_wav)
    Path(silent_wav).unlink(missing_ok=True)

# 6. Scene generation (meaning-based segmentation)
def test_06_meaning_based_scene_generation():
    script = "Technology changes student learning. Artificial intelligence makes education personalised."
    scenes = scene_engine.segment_script_into_scenes(script, total_audio_duration=6.0)
    assert len(scenes) == 2
    assert "technology" in scenes[0].visual_description.lower() or "digital" in scenes[0].visual_description.lower() or "student" in scenes[0].visual_description.lower()
    assert "neural" in scenes[1].visual_description.lower() or "seminar" in scenes[1].visual_description.lower() or "education" in scenes[1].search_query.lower()

# 7. Scene timing based on narration
def test_07_scene_timing():
    script = "Short sentence. A much longer second sentence that naturally requires significantly more narration duration."
    scenes = scene_engine.segment_script_into_scenes(script, total_audio_duration=10.0)
    assert len(scenes) == 2
    assert scenes[0].duration < scenes[1].duration
    assert scenes[-1].end_time == 10.0

# 8. Footage relevance scoring
@pytest.mark.asyncio
async def test_08_footage_relevance():
    scene = SceneDetail(
        scene_number=1,
        narration_text="Modern technology and computers.",
        start_time=0.0,
        end_time=4.0,
        duration=4.0,
        visual_description="modern digital computer screen",
        search_query="technology"
    )
    clip = await footage_service.find_best_footage_for_scene(scene, set())
    assert scene.relevance_score >= 0.70
    assert scene.vlm_score is not None and scene.vlm_score >= 0.70

# 9. Duplicate clip prevention
@pytest.mark.asyncio
async def test_09_duplicate_clip_prevention():
    seen_clips = set()
    sc1 = SceneDetail(
        scene_number=1, narration_text="Tech one", start_time=0, end_time=3, duration=3,
        visual_description="technology", search_query="technology"
    )
    sc2 = SceneDetail(
        scene_number=2, narration_text="Tech two", start_time=3, end_time=6, duration=3,
        visual_description="technology", search_query="technology"
    )
    clip1 = await footage_service.find_best_footage_for_scene(sc1, seen_clips)
    clip2 = await footage_service.find_best_footage_for_scene(sc2, seen_clips)
    assert clip1.clip_id != clip2.clip_id

# 10. Licence metadata recording
@pytest.mark.asyncio
async def test_10_licence_metadata():
    sc = SceneDetail(
        scene_number=1, narration_text="Nature trees", start_time=0, end_time=3, duration=3,
        visual_description="nature forest", search_query="nature"
    )
    clip = await footage_service.find_best_footage_for_scene(sc, set())
    assert clip.licence is not None
    assert clip.attribution is not None
    assert clip.is_commercial_cleared is True

# 11. Provider failure and fallback
@pytest.mark.asyncio
async def test_11_provider_fallback():
    sc = SceneDetail(
        scene_number=1, narration_text="Random obscure topic", start_time=0, end_time=3, duration=3,
        visual_description="rare unknown topic", search_query="xyzabc123nonexistent"
    )
    clip = await footage_service.find_best_footage_for_scene(sc, set())
    assert clip is not None
    assert clip.provider == "MockProvider"

# 12. Video rendering
def test_12_video_rendering(tmp_path):
    sc = SceneDetail(
        scene_number=1, narration_text="Test scene", start_time=0, end_time=2, duration=2,
        visual_description="nature", search_query="nature"
    )
    # Ensure mock clip exists
    import asyncio
    clip = asyncio.run(footage_service.find_best_footage_for_scene(sc, set()))
    out_clip = str(tmp_path / "test_clip.mp4")
    res = video_engine.render_scene_clip(sc, AspectRatio.LANDSCAPE_16_9, out_clip)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 1000

# 13. Caption generation
def test_13_caption_generation(tmp_path):
    scenes = [
        SceneDetail(scene_number=1, narration_text="First phrase.", start_time=0.0, end_time=2.5, duration=2.5, visual_description="v1", search_query="q1"),
        SceneDetail(scene_number=2, narration_text="Second phrase.", start_time=2.5, end_time=5.0, duration=2.5, visual_description="v2", search_query="q2")
    ]
    srt_out = str(tmp_path / "captions.srt")
    caption_service.generate_srt(scenes, srt_out)
    assert Path(srt_out).exists()
    content = Path(srt_out).read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,500" in content
    assert "First phrase." in content

# 14. All three aspect ratios support
def test_14_aspect_ratios_supported():
    assert AspectRatio.LANDSCAPE_16_9.value == "16:9"
    assert AspectRatio.PORTRAIT_9_16.value == "9:16"
    assert AspectRatio.SQUARE_1_1.value == "1:1"
    assert video_engine.RESOLUTIONS[AspectRatio.LANDSCAPE_16_9] == (1920, 1080)
    assert video_engine.RESOLUTIONS[AspectRatio.PORTRAIT_9_16] == (1080, 1920)
    assert video_engine.RESOLUTIONS[AspectRatio.SQUARE_1_1] == (1080, 1080)

# 15. Background job progress
def test_15_background_job_progress():
    payload = {"script_text": "Progress tracking demonstration script."}
    res = client.post("/api/v1/broll/jobs", json=payload)
    job_id = res.json()["job_id"]
    time.sleep(1)
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    st_data = status_res.json()
    assert 0 <= st_data["progress"] <= 100
    assert st_data["stage"] is not None

# 16. Idempotency support
def test_16_idempotency():
    key = f"test_idemp_{time.time()}"
    payload = {"script_text": "Idempotent script submission test."}
    res1 = client.post("/api/v1/broll/jobs", json=payload, headers={"Idempotency-Key": key})
    assert res1.status_code == 202
    job1_id = res1.json()["job_id"]

    res2 = client.post("/api/v1/broll/jobs", json=payload, headers={"Idempotency-Key": key})
    assert res2.status_code == 202
    assert res2.json()["job_id"] == job1_id
    assert res2.headers.get("X-Idempotency-Hit") == "true"

# 17. Concurrent job submissions
def test_17_concurrent_jobs():
    res1 = client.post("/api/v1/broll/jobs", json={"script_text": "Concurrent job 1."})
    res2 = client.post("/api/v1/broll/jobs", json={"script_text": "Concurrent job 2."})
    assert res1.status_code == 202
    assert res2.status_code == 202
    assert res1.json()["job_id"] != res2.json()["job_id"]

# 18. API error handling structured JSON format
def test_18_api_error_structure():
    res = client.get("/api/v1/jobs/non_existent_job_9999")
    assert res.status_code == 404
    err_body = res.json()
    assert "error" in err_body
    assert err_body["error"]["code"] == "JOB_NOT_FOUND"
    assert "correlation_id" in err_body["error"]
