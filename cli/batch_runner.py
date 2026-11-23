import os
import sys
import json
import time
import csv
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

async def run_batch(input_file: str, output_dir: str, api_url: Optional[str] = None, download: bool = False):
    print("==================================================")
    print(" FrameFlow AI – Production Batch CLI Video Runner ")
    print("==================================================")
    print(f"Loading scripts from: {input_file}")
    if api_url:
        print(f"Targeting HTTP API:  {api_url}")
    else:
        print(f"Targeting Engine:    Local In-Process JobManager")
    print(f"Output Directory:    {output_dir}")

    # Load from file or folder
    inp_p = Path(input_file)
    scripts_data = []
    if inp_p.is_dir():
        for p in inp_p.glob("*.txt"):
            text = p.read_text(encoding="utf-8").strip()
            if text:
                scripts_data.append({"id": p.stem, "title": p.stem, "script": text, "language": "en"})
        for p in inp_p.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        scripts_data.extend(content)
                    elif isinstance(content, dict):
                        scripts_data.append(content)
            except Exception:
                pass
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            scripts_data = json.load(f)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(scripts_data)} scripts to process.")
    results_summary = []

    import httpx
    from app.models.api_schemas import BrollJobCreateRequest, VoiceConfig, LanguageCode, AspectRatio
    from app.services.job_manager import job_manager

    for i, item in enumerate(scripts_data, 1):
        script_id = item.get("id", f"item_{i}")
        title = item.get("title", f"Script {i}")
        script_text = item["script"]
        lang_str = item.get("language", "en")
        lang = LanguageCode(lang_str)

        print(f"\n[{i}/{len(scripts_data)}] Queuing: {title} ({lang_str.upper()})")

        payload = {
            "script": script_text,
            "voice": {"language": lang_str},
            "aspect_ratios": ["16:9", "9:16", "1:1"]
        }

        job_id = None
        t0 = time.time()

        if api_url:
            base_endpoint = api_url.rstrip("/")
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(f"{base_endpoint}/broll/jobs", json=payload)
                if res.status_code != 202:
                    print(f"  [!] Failed to queue job via API: HTTP {res.status_code} - {res.text}")
                    results_summary.append({
                        "id": script_id, "title": title, "status": "failed",
                        "job_id": "N/A", "duration_seconds": 0, "processing_time_s": 0,
                        "relevance_score": 0, "video_urls": ""
                    })
                    continue
                data = res.json()
                job_id = data.get("job_id")
        else:
            req = BrollJobCreateRequest(
                script=script_text,
                voice=VoiceConfig(language=lang),
                aspect_ratios=[AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1]
            )
            job_id = f"batch_{script_id}_{int(time.time())}"
            job_manager.create_job(req, correlation_id=f"corr_{job_id}", job_id=job_id)

        print(f"  > Job ID: {job_id}. Polling progress...")

        # Poll status
        final_status = "running"
        while True:
            await asyncio.sleep(0.5)
            if api_url:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    st_res = await client.get(f"{api_url.rstrip('/')}/jobs/{job_id}")
                    if st_res.status_code == 200:
                        st_data = st_res.json()
                        stage = st_data.get("stage", "working")
                        progress = st_data.get("progress", 0)
                        final_status = st_data.get("status", "running")
                        print(f"  > Stage: {stage:<26} Progress: {progress}%", end="\r")
                        if final_status in ("succeeded", "failed"):
                            break
            else:
                detail = job_manager.get_job_detail(job_id)
                final_status = detail.status.value
                print(f"  > Stage: {detail.stage:<26} Progress: {detail.progress}%", end="\r")
                if final_status in ("succeeded", "failed"):
                    break

            if time.time() - t0 > 90:
                print(f"\n  [!] Timeout reached for job {job_id}")
                final_status = "timeout"
                break

        print(f"\n  Result: {final_status.upper()}")

        # Fetch result
        result_data = {}
        if api_url:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r_res = await client.get(f"{api_url.rstrip('/')}/jobs/{job_id}/result")
                if r_res.status_code == 200:
                    result_data = r_res.json()
        else:
            res_obj = job_manager.get_job_result(job_id)
            result_data = res_obj.dict()

        metrics = result_data.get("metrics", {})
        q_rep = result_data.get("quality_report", {})
        video_urls = result_data.get("video_urls", {})

        # Optional download of artifacts to output directory
        if download and final_status == "succeeded":
            job_out_dir = out_path / job_id
            job_out_dir.mkdir(parents=True, exist_ok=True)
            async with httpx.AsyncClient(timeout=30.0) as client:
                for ar_name, v_url in video_urls.items():
                    if v_url.startswith("http"):
                        v_res = await client.get(v_url)
                        if v_res.status_code == 200:
                            v_file = job_out_dir / f"video_{ar_name.replace(':', '_')}.mp4"
                            with open(v_file, "wb") as f:
                                f.write(v_res.content)

        results_summary.append({
            "script_id": script_id,
            "title": title,
            "status": final_status,
            "job_id": job_id,
            "duration_seconds": metrics.get("total_duration", 0),
            "processing_time_s": metrics.get("processing_time_seconds", round(time.time() - t0, 2)),
            "relevance_score": q_rep.get("average_relevance_score", 0.0),
            "video_urls": "; ".join([f"{k}: {v}" for k, v in video_urls.items()])
        })

    # Save summary CSV
    for filename in ("summary.csv", "batch_summary.csv"):
        csv_file = out_path / filename
        fieldnames = [
            "script_id", "title", "status", "job_id", "duration_seconds",
            "processing_time_s", "relevance_score", "video_urls"
        ]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results_summary)

    # Save summary JSON
    json_file = out_path / "batch_summary.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\nBatch processing finished successfully!")
    print(f"Summary CSV saved to:  {csv_file}")
    print(f"Summary JSON saved to: {json_file}")

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
        help="Directory to export batch results and deliverables"
    )
    parser.add_argument(
        "--api-url", "-a",
        default=None,
        help="Optional API base URL (e.g. http://localhost:8000/api/v1). If omitted, processes in-process."
    )
    parser.add_argument(
        "--download", "-d",
        action="store_true",
        help="Download generated video deliverables to output directory"
    )
    args = parser.parse_args()
    asyncio.run(run_batch(args.input, args.output, args.api_url, args.download))

if __name__ == "__main__":
    main()
