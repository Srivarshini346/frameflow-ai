import os
import sys
import json
import time
import argparse
from pathlib import Path

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

import asyncio
from app.models.api_schemas import BrollJobCreateRequest, VoiceConfig, LanguageCode, AspectRatio
from app.services.job_manager import job_manager

async def run_batch(input_file: str, output_dir: str):
    print(f"==================================================")
    print(f" FrameFlow AI – Batch CLI Video Processing Runner ")
    print(f"==================================================")
    print(f"Loading input scripts from: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        scripts_data = json.load(f)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(scripts_data)} scripts to process.")
    results_summary = []

    for i, item in enumerate(scripts_data, 1):
        script_id = item.get("id", f"item_{i}")
        title = item.get("title", f"Project {i}")
        script_text = item["script"]
        lang_str = item.get("language", "en")
        lang = LanguageCode(lang_str)

        print(f"\n[{i}/{len(scripts_data)}] Starting: {title} ({lang_str.upper()})")

        req = BrollJobCreateRequest(
            script_text=script_text,
            voice_config=VoiceConfig(language=lang),
            aspect_ratios=[AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1]
        )

        job_id = f"batch_{script_id}_{int(time.time())}"
        job_detail = job_manager.create_job(req, correlation_id=f"corr_{job_id}", job_id=job_id)

        # Poll until complete
        start_wait = time.time()
        while True:
            await asyncio.sleep(1)
            status = job_manager.get_job_detail(job_id)
            print(f"  > Stage: {status.stage:<26} Progress: {status.progress}%", end="\r")
            if status.status.value in ("succeeded", "failed"):
                break
            if time.time() - start_wait > 90:
                print(f"\n  [!] Timeout waiting for job {job_id}")
                break

        print(f"\n  Result: {status.status.value.upper()}")
        res = job_manager.get_job_result(job_id)
        results_summary.append({
            "id": script_id,
            "title": title,
            "job_id": job_id,
            "status": status.status.value,
            "metrics": res.metrics,
            "video_urls": res.video_urls
        })

    summary_file = out_path / "batch_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\nBatch processing finished! Summary saved to {summary_file}")

def main():
    parser = argparse.ArgumentParser(description="FrameFlow AI Batch CLI Runner")
    parser.add_argument(
        "--input", "-i",
        default=str(BASE_DIR / "backend" / "test_pack" / "sample_scripts.json"),
        help="Path to JSON file containing array of scripts"
    )
    parser.add_argument(
        "--output", "-o",
        default=str(BASE_DIR / "storage" / "batch_runs"),
        help="Directory to export batch results"
    )
    args = parser.parse_args()
    asyncio.run(run_batch(args.input, args.output))

if __name__ == "__main__":
    main()
