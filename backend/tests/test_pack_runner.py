import json
from pathlib import Path
import pytest
from app.services.scene_engine import scene_engine
from app.models.api_schemas import LanguageCode, VisualPromptStyle

def test_10_script_test_pack():
    pack_path = Path(__file__).resolve().parent.parent / "test_pack" / "sample_scripts.json"
    assert pack_path.exists(), "Sample test pack JSON file must exist"
    
    with open(pack_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    assert len(samples) >= 10, f"Test pack must contain at least 10 scripts, found {len(samples)}"

    for item in samples:
        script = item["script"]
        lang = LanguageCode(item["language"])
        scenes = scene_engine.segment_script_into_scenes(
            script_text=script,
            total_audio_duration=8.0,
            style=VisualPromptStyle.CINEMATIC,
            language=lang
        )
        assert len(scenes) >= item["min_scenes"], (
            f"Failed scene count for '{item['title']}': expected >={item['min_scenes']}, got {len(scenes)}"
        )
        for sc in scenes:
            assert sc.narration_text, "Scene narration text cannot be empty"
            assert sc.visual_description, "Scene visual description must be populated"
            assert sc.search_query, "Scene search query must be formulated"
            assert sc.duration > 0, "Scene duration must be positive"
            assert sc.end_time > sc.start_time, "Timestamps must be strictly chronological"
