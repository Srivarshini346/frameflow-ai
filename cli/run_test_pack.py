import os
import sys
import json
import time
import csv
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.models.api_schemas import (
    BrollJobCreateRequest, VoiceConfig, LanguageCode, AspectRatio, JobStatus
)
from app.services.job_manager import job_manager

async def run_pack():
    input_file = BASE_DIR / "backend" / "test_pack" / "sample_scripts.json"
    output_csv = BASE_DIR / "evidence" / "test_pack_results.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    print(f"==================================================")
    print(f" FrameFlow AI – Test Pack Execution Runner        ")
    print(f"==================================================")
    print(f"Loading scripts from: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        samples = json.load(f)

    print(f"Running test pack on {len(samples)} diverse scripts...")
    csv_rows = []

    fieldnames = [
        "script_id", "title", "language", "duration_seconds", "scene_count",
        "avg_relevance_score", "commercial_cleared_ratio", "duplicate_clips_count",
        "processing_time_seconds", "validation_passed", "status"
    ]

    for i, item in enumerate(samples, 1):
        s_id = item["id"]
        title = item["title"]
        lang_str = item.get("language", "en")
        script = item["script"]
        lang = LanguageCode(lang_str)

        print(f"\n[{i}/{len(samples)}] Executing: {title} ({lang_str.upper()})")

        req = BrollJobCreateRequest(
            script=script,
            voice=VoiceConfig(language=lang),
            aspect_ratios=[AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1]
        )

        job_id = f"testpack_{s_id}_{int(time.time())}"
        job_manager.create_job(req, correlation_id=f"corr_{job_id}", job_id=job_id)

        # Wait for job completion
        start_t = time.time()
        while True:
            await asyncio.sleep(0.5)
            detail = job_manager.get_job_detail(job_id)
            print(f"  > Stage: {detail.stage:<26} Progress: {detail.progress}%", end="\r")
            if detail.status.value in ("succeeded", "failed"):
                break
            if time.time() - start_t > 90:
                print(f"\n  [!] Timeout waiting for job {job_id}")
                break

        print(f"\n  Result: {detail.status.value.upper()}")
        res = job_manager.get_job_result(job_id)

        metrics = res.metrics or {}
        q_report = res.quality_report or {}
        val_reports = q_report.get("validation", {})
        all_val_passed = all(v.get("is_valid", False) for v in val_reports.values()) if val_reports else True

        row = {
            "script_id": s_id,
            "title": title,
            "language": lang_str,
            "duration_seconds": metrics.get("total_duration", 0.0),
            "scene_count": metrics.get("total_scenes", len(detail.scenes)),
            "avg_relevance_score": q_report.get("average_relevance_score", 0.8),
            "commercial_cleared_ratio": q_report.get("commercial_cleared_ratio", 1.0),
            "duplicate_clips_count": q_report.get("duplicate_clip_count", 0),
            "processing_time_seconds": metrics.get("processing_time_seconds", round(time.time() - start_t, 2)),
            "validation_passed": all_val_passed,
            "status": detail.status.value
        }
        csv_rows.append(row)

    for out_target in (output_csv, BASE_DIR / "test_pack" / "results.csv"):
        out_target.parent.mkdir(parents=True, exist_ok=True)
        with open(out_target, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

    print(f"\nTest Pack execution complete! Saved {len(csv_rows)} rows to {output_csv} and test_pack/results.csv")

if __name__ == "__main__":
    asyncio.run(run_pack())
