import os
import sys
import json
import time
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.config import settings
from app.models.api_schemas import (
    BrollJobCreateRequest, AspectRatio, VisualPromptStyle, CaptionConfig
)
from app.services.job_manager import job_manager
from app.services.video_validator import video_validator

COFFEE_SCRIPT = (
    "Coffee from bean to cup begins in mist-covered mountain highlands. "
    "Farmers hand-pick only the ripest red cherries with precision. "
    "Inside the roasting drum, intense heat creates the golden brown crackle. "
    "Grinding freshly roasted beans releases an unmistakable rich aroma. "
    "High pressure extraction pulls dark espresso into a glass cup. "
    "Morning steam rises as the rich crema settles to perfection."
)

async def main():
    print("=" * 70)
    print("FrameFlow AI - Live Real Stock Footage Verification Suite")
    print("=" * 70)

    # 1. Check API keys
    has_pexels = bool(settings.pexels_api_key and settings.pexels_api_key.strip())
    has_pixabay = bool(settings.pixabay_api_key and settings.pixabay_api_key.strip())

    if not (has_pexels or has_pixabay):
        print("\nREAL_RUN SKIPPED: neither PEXELS_API_KEY nor PIXABAY_API_KEY is set.")
        print("To run live verification with real stock footage:")
        print("  1. Create a free API key at https://www.pexels.com/api/ or https://pixabay.com/api/docs/")
        print("  2. Add PEXELS_API_KEY=... or PIXABAY_API_KEY=... to your .env file")
        print("  3. Run: python scripts/real_run.py\n")
        sys.exit(0)

    active_provider = "Pexels" if has_pexels else "Pixabay"
    print(f"\n[OK] Active Stock Media Key Detected: {active_provider}")
    print(f"Submitting 6-line Coffee Script for multi-format video generation...")

    # 2. Build Job Request
    job_id = f"real_run_{int(time.time())}"
    request_data = BrollJobCreateRequest(
        script=COFFEE_SCRIPT,
        aspect_ratios=[AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1],
        style=VisualPromptStyle.CINEMATIC,
        avoid=["cartoon", "animation", "drawing"],
        captions=CaptionConfig(burn_in=True, srt=True)
    )

    t0 = time.time()
    job_detail = job_manager.create_job(request_data, correlation_id="real_run_corr", job_id=job_id)

    # 3. Poll until completed
    print(f"Job created: {job_id}. Processing in background...")
    while True:
        await asyncio.sleep(2.0)
        status = job_manager.get_job_detail(job_id)
        print(f"   Stage: {status.stage:<25} Progress: {status.progress}%")
        if status.status in ("succeeded", "failed"):
            break

    if status.status == "failed":
        print(f"\n[FAIL] Real run failed: {status.error}")
        sys.exit(1)

    result = job_manager.get_job_result(job_id)
    total_time = round(time.time() - t0, 2)

    # 4. Verify outputs with FFprobe
    evidence_dir = ROOT_DIR / "evidence" / "real_run"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report_file = evidence_dir / "report.json"

    validation_summary = {}
    for ar in ["16:9", "9:16", "1:1"]:
        video_url = result.video_urls.get(ar)
        local_video_path = ROOT_DIR / "storage" / "jobs" / job_id / f"video_{ar.replace(':', '_')}.mp4"
        val = video_validator.validate_video(str(local_video_path), expected_ar=ar)
        validation_summary[ar] = {
            "valid": val.is_valid,
            "duration": val.duration,
            "dimensions": f"{val.width}x{val.height}",
            "fps": val.fps,
            "has_video": val.has_video_stream,
            "has_audio": val.has_audio_stream,
            "aspect_ratio_match": val.aspect_ratio_matches
        }

    # 5. Scene Breakdown Table
    scenes = job_manager._jobs[job_id].get("scenes", [])
    scene_summary = []
    print("\n" + "=" * 90)
    print(f"{'Scene':<6} | {'Provider':<10} | {'Clip ID':<18} | {'Score':<6} | {'Rating':<6} | {'Search Query':<22}")
    print("-" * 90)

    for sc in scenes:
        ft = sc.get("selected_footage", {})
        sc_num = sc.get("scene_number", 0)
        prov = ft.get("source") or ft.get("provider", "Mock")
        cid = ft.get("clip_id", "N/A")
        score = sc.get("relevance_score", 0.0)
        rating = sc.get("clip_rating", 0)
        q = sc.get("search_query", "")[:22]

        print(f"{sc_num:<6} | {prov:<10} | {cid:<18} | {score:<6.2f} | {rating}/5    | {q:<22}")
        scene_summary.append({
            "scene": sc_num,
            "provider": prov,
            "clip_id": cid,
            "licence": ft.get("licence", ""),
            "attribution": ft.get("attribution", ""),
            "relevance_score": score,
            "clip_rating": rating,
            "search_query": sc.get("search_query")
        })
    print("=" * 90)

    # 6. Save Evidence Report
    report_data = {
        "job_id": job_id,
        "active_provider": active_provider,
        "processing_time_seconds": total_time,
        "total_scenes": len(scenes),
        "video_validations": validation_summary,
        "scenes": scene_summary,
        "result_urls": result.video_urls
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n[SUCCESS] Live real run finished in {total_time}s.")
    print(f"Evidence report saved to: {report_file}")
    return 0

if __name__ == "__main__":
    asyncio.run(main())
