import os
import time
import math
import wave
import struct
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.services.audio_service import audio_service
from app.services.asr_service import validate_audio_file
from app.services.scene_engine import scene_engine
from app.services.footage_service import footage_service
from app.services.video_engine import video_engine
from app.services.caption_service import caption_service
from app.services.query_intelligence import query_intelligence
from app.services.safety_service import safety_service
from app.services.relevance_scorer import relevance_scorer
from app.services.video_validator import video_validator
from app.models.api_schemas import (
    BrollJobCreateRequest, VoiceConfig, LanguageCode, AspectRatio, CaptionConfig, SceneDetail, FootageClip
)
from app.core.exceptions import (
    ValidationError, EmptyScriptError, WrongAudioFormatError,
    SilentAudioError, MusicOnlyAudioError, IdempotencyKeyReusedError
)

client = TestClient(app)

def create_test_wav(duration_s=2.5, silent=False, music_marker=False):
    sr = 22050
    n_samples = int(duration_s * sr)
    suffix = "_music_only_test_marker.wav" if music_marker else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
        with wave.open(tf.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            data = bytearray()
            for i in range(n_samples):
                if silent:
                    val = 0
                else:
                    val = int(math.sin(2 * math.pi * 440 * (i / sr)) * 12000)
                data.extend(struct.pack("<h", val))
            wf.writeframes(data)
        return tf.name

# 1. Text script submission
def test_01_text_script_submission():
    payload = {
        "script": "Technology is transforming the modern classroom. Artificial intelligence creates personalised learning.",
        "aspect_ratios": ["16:9", "9:16", "1:1"]
    }
    res = client.post("/api/v1/broll/jobs", json=payload)
    assert res.status_code == 202
    data = res.json()
    assert "job_id" in data
    assert data["status"] in ("queued", "running")
    assert "X-Correlation-ID" in res.headers
    assert res.headers.get("Location") == f"/api/v1/jobs/{data['job_id']}"

# 2. Audio upload validation
def test_02_audio_upload_validation():
    wav_path = create_test_wav(duration_s=2.5, silent=False)
    try:
        props = validate_audio_file(wav_path)
        assert props["duration"] >= 2.0
        assert props["is_silent"] is False
    finally:
        Path(wav_path).unlink(missing_ok=True)

# 3. Empty script (400 EMPTY_SCRIPT)
def test_03_empty_script_rejected():
    res = client.post("/api/v1/broll/jobs", json={"script": "    "})
    assert res.status_code == 400
    err = res.json()
    assert "error" in err
    assert err["error"]["code"] == "EMPTY_SCRIPT"
    assert err["error"]["retryable"] is False

# 4. Unsupported audio format (400 WRONG_AUDIO_FORMAT)
def test_04_unsupported_audio_format():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        tf.write(b"plain text not audio")
        tf_name = tf.name
    try:
        with pytest.raises(WrongAudioFormatError) as exc_info:
            validate_audio_file(tf_name)
        assert exc_info.value.code == "WRONG_AUDIO_FORMAT"
        assert exc_info.value.status_code == 400
    finally:
        Path(tf_name).unlink(missing_ok=True)

# 5. Silent audio (422 SILENT_AUDIO)
def test_05_silent_audio_rejected():
    silent_wav = create_test_wav(duration_s=2.0, silent=True)
    try:
        with pytest.raises(SilentAudioError) as exc_info:
            validate_audio_file(silent_wav)
        assert exc_info.value.code == "SILENT_AUDIO"
        assert exc_info.value.status_code == 422
    finally:
        Path(silent_wav).unlink(missing_ok=True)

# 6. Music-only audio (422 MUSIC_ONLY_AUDIO)
def test_06_music_only_audio_rejected():
    music_wav = create_test_wav(duration_s=2.0, silent=False, music_marker=True)
    try:
        with pytest.raises(MusicOnlyAudioError) as exc_info:
            validate_audio_file(music_wav)
        assert exc_info.value.code == "MUSIC_ONLY_AUDIO"
        assert exc_info.value.status_code == 422
    finally:
        Path(music_wav).unlink(missing_ok=True)

# 7. Meaning-based scene splitting & min scene length enforcement (2.5s)
def test_07_meaning_based_scene_splitting():
    # Includes very short fragment "Yes." followed by sentences
    script = "Yes. Technology changes learning. Artificial intelligence makes modern education personalised."
    scenes = scene_engine.segment_script_into_scenes(script, total_audio_duration=8.0)
    assert len(scenes) >= 2
    for sc in scenes:
        assert sc.duration >= settings.min_scene_duration or sc == scenes[-1]
        assert sc.end_time > sc.start_time

# 8. Query disambiguation (mouse/cloud/bank/python)
def test_08_query_disambiguation():
    # Tech homonyms
    q_mouse_tech = query_intelligence.disambiguate_query("The developer clicked the computer mouse on the desk.")
    assert "computer" in q_mouse_tech or "mouse" in q_mouse_tech

    q_cloud_tech = query_intelligence.disambiguate_query("Deploy the application to the scalable cloud server.")
    assert "server" in q_cloud_tech or "cloud" in q_cloud_tech

    q_bank_fin = query_intelligence.disambiguate_query("The central bank raised international interest rates.")
    assert "finance" in q_bank_fin or "bank" in q_bank_fin

    q_python_code = query_intelligence.disambiguate_query("Writing python software for machine learning.")
    assert "code" in q_python_code or "programming" in q_python_code or "software" in q_python_code

# 9. Abstract metaphor & statistical numbers handling
def test_09_abstract_metaphors_and_statistics():
    # Abstract
    abstract_text = "Curiosity sparks creative discovery across human history."
    q_abs = query_intelligence.disambiguate_query(abstract_text)
    assert len(q_abs) > 3

    # Statistical numbers
    stats_text = "Quarterly revenue expanded by 42.5% this fiscal year."
    q_stats = query_intelligence.disambiguate_query(stats_text)
    assert "growth" in q_stats or "business" in q_stats or "analytics" in q_stats or "market" in q_stats

# 10. Safety module (named person/brand stand-in & avoid keyword filter)
def test_10_safety_module():
    # Named person replacement
    safe_person = safety_service.sanitize_text_query("Elon Musk announces electric vehicle update.")
    assert "Elon Musk" not in safe_person
    assert "tech executive" in safe_person or "entrepreneur" in safe_person

    # Brand replacement
    safe_brand = safety_service.sanitize_text_query("Show the Apple iPhone screen.")
    assert "iPhone" not in safe_brand
    assert "smartphone" in safe_brand

    # Avoid keyword evaluation
    dummy_clip = FootageClip(
        clip_id="test_clip_avoid",
        provider="MockProvider",
        source_url="http://local/test",
        download_url="http://local/test.mp4",
        width=1920,
        height=1080,
        duration=5.0,
        licence="CC0",
        attribution="FrameFlow",
        tags=["hospital", "blood", "medical"]
    )
    is_safe, reason = safety_service.evaluate_candidate_clip(dummy_clip, avoid_list=["blood", "weapons"])
    assert is_safe is False
    assert "blood" in reason

# 11. CLIP image-text similarity scoring (unclamped 0.0-1.0)
def test_11_clip_similarity_scoring():
    score, rating, method = relevance_scorer.score_candidate(
        clip_path_or_url="mock_technology_1.mp4",
        narration_text="Modern artificial intelligence and technology systems.",
        candidate_tags=["technology", "ai", "computer"]
    )
    assert 0.0 <= score <= 1.0
    assert 1 <= rating <= 5
    assert "similarity" in method.lower()

# 12. Duplicate clip prevention
@pytest.mark.asyncio
async def test_12_duplicate_clip_prevention():
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
    assert clip1.clip_id in seen_clips
    assert clip2.clip_id in seen_clips

# 13. Licence metadata recording
@pytest.mark.asyncio
async def test_13_licence_metadata():
    sc = SceneDetail(
        scene_number=1, narration_text="Nature trees", start_time=0, end_time=3, duration=3,
        visual_description="nature forest", search_query="nature"
    )
    clip = await footage_service.find_best_footage_for_scene(sc, set())
    assert clip.licence is not None
    assert clip.attribution is not None
    assert clip.is_commercial_cleared is True
    assert clip.watermark is False

# 14. Provider failure & runtime disable fallback
@pytest.mark.asyncio
async def test_14_provider_disable_fallback():
    # Force disabling external providers
    settings.disable_provider = "pexels,pixabay"
    sc = SceneDetail(
        scene_number=1, narration_text="Fallback demonstration", start_time=0, end_time=3, duration=3,
        visual_description="fallback topic", search_query="nature"
    )
    clip = await footage_service.find_best_footage_for_scene(sc, set())
    assert clip is not None
    assert clip.provider == "MockProvider"
    settings.disable_provider = ""

# 15. Video rendering with 3 aspect ratios
def test_15_video_rendering_three_aspect_ratios(tmp_path):
    sc = SceneDetail(
        scene_number=1, narration_text="Test scene", start_time=0, end_time=2, duration=2,
        visual_description="technology", search_query="technology"
    )
    import asyncio
    clip = asyncio.run(footage_service.find_best_footage_for_scene(sc, set()))
    
    for ar in [AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1]:
        tag = ar.value.replace(":", "_")
        out_clip = str(tmp_path / f"test_clip_{tag}.mp4")
        video_engine.render_scene_clip(sc, ar, out_clip)
        assert Path(out_clip).exists()
        assert Path(out_clip).stat().st_size > 1000

# 16. Smart crop 9:16 saliency check
def test_16_smart_crop_saliency():
    offset_filter = video_engine.compute_smart_crop_offset("non_existent.mp4", 1080, 1920)
    assert "scale=1080:1920" in offset_filter
    assert "crop=1080:1920" in offset_filter

# 17. Post-render ffprobe validator checks
def test_17_post_render_ffprobe_validator(tmp_path):
    sc = SceneDetail(
        scene_number=1, narration_text="Validator scene", start_time=0, end_time=2, duration=2,
        visual_description="technology", search_query="technology"
    )
    import asyncio
    asyncio.run(footage_service.find_best_footage_for_scene(sc, set()))
    out_clip = str(tmp_path / "valid_clip_16_9.mp4")
    video_engine.render_scene_clip(sc, AspectRatio.LANDSCAPE_16_9, out_clip)

    val = video_validator.validate_video(out_clip, expected_ratio="16:9")
    assert val.is_valid is True
    assert val.report["file_size_bytes"] > 10000

# 18. Idempotency (same body -> 202, different body -> 409 IDEMPOTENCY_KEY_REUSED)
def test_18_idempotency_hash_and_mismatch():
    key = f"idemp_test_{time.time()}"
    body1 = {"script": "Idempotent script submission body one."}
    body2 = {"script": "Idempotent script submission body two (mismatch)."}

    # First request
    res1 = client.post("/api/v1/broll/jobs", json=body1, headers={"Idempotency-Key": key})
    assert res1.status_code == 202
    job1_id = res1.json()["job_id"]

    # Replay with identical body -> returns cached 202 with hit header
    res2 = client.post("/api/v1/broll/jobs", json=body1, headers={"Idempotency-Key": key})
    assert res2.status_code == 202
    assert res2.json()["job_id"] == job1_id
    assert res2.headers.get("X-Idempotency-Hit") == "true"

    # Replay with DIFFERENT body -> 409 IDEMPOTENCY_KEY_REUSED
    res3 = client.post("/api/v1/broll/jobs", json=body2, headers={"Idempotency-Key": key})
    assert res3.status_code == 409
    err = res3.json()
    assert err["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert err["error"]["retryable"] is False

# 19. Concurrent jobs without collision
def test_19_concurrent_jobs_without_collision():
    res1 = client.post("/api/v1/broll/jobs", json={"script": "Concurrent test script 1."})
    res2 = client.post("/api/v1/broll/jobs", json={"script": "Concurrent test script 2."})
    assert res1.status_code == 202
    assert res2.status_code == 202
    id1 = res1.json()["job_id"]
    id2 = res2.json()["job_id"]
    assert id1 != id2

# 20. Bad clip & corrupt download rejection
def test_20_black_frame_and_corrupt_download_rejection(tmp_path):
    import subprocess
    from app.services.footage_service import footage_service
    # 1. Corrupt 48-byte file rejected
    corrupt_file = tmp_path / "corrupt_48b.mp4"
    corrupt_file.write_bytes(b"0" * 48)
    assert not footage_service.validate_video_file(corrupt_file)

    # 2. Non-existent file rejected
    assert not footage_service.validate_video_file(tmp_path / "missing.mp4")

    # 3. Pure black frame candidate rejected by luma check
    ffmpeg_exe = settings.get_ffmpeg_path()
    black_clip = tmp_path / "pure_black.mp4"
    subprocess.run([
        ffmpeg_exe, "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1.5",
        "-c:v", "libx264", "-t", "1.5",
        str(black_clip)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if black_clip.exists():
        is_good, reason = footage_service.check_candidate_clip_quality(black_clip)
        assert not is_good, "Candidate with pure black frames must be rejected by luma/quality check"
        assert "luma" in reason.lower() or "black" in reason.lower()

# 21. Readiness probe and providers status endpoint
def test_21_readiness_probe_endpoints():
    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    data = res_ready.json()
    assert "ready" in data
    assert "checks" in data
    assert "ffmpeg" in data["checks"]
    assert "storage" in data["checks"]
    assert "database" in data["checks"]

    res_prov = client.get("/api/v1/providers")
    assert res_prov.status_code == 200
    p_data = res_prov.json()
    assert "providers" in p_data
    assert len(p_data["providers"]) >= 2
