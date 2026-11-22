import os
import sys
import json
import time
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.models.api_schemas import (
    BrollJobCreateRequest, VoiceConfig, LanguageCode, AspectRatio
)
from app.services.job_manager import job_manager

async def benchmark_rerender():
    print("==================================================")
    print(" FrameFlow AI – Incremental Re-render Benchmark   ")
    print("==================================================")

    script = (
        "Technology is transforming modern education through digital learning environments. "
        "Artificial intelligence adapts coursework dynamically to each student's needs. "
        "Collaborative interactive classrooms empower global learners to excel."
    )

    req = BrollJobCreateRequest(
        script=script,
        voice=VoiceConfig(language=LanguageCode.EN),
        aspect_ratios=[AspectRatio.LANDSCAPE_16_9, AspectRatio.PORTRAIT_9_16, AspectRatio.SQUARE_1_1]
    )

    job_id = f"bench_{int(time.time())}"
    print(f"Creating baseline job {job_id} (3 scenes across 3 aspect ratios)...")

    # 1. Measure Initial Full Render
    t0 = time.time()
    job_manager.create_job(req, correlation_id=f"corr_{job_id}", job_id=job_id)

    while True:
        await asyncio.sleep(0.3)
        detail = job_manager.get_job_detail(job_id)
        if detail.status.value in ("succeeded", "failed"):
            break

    full_render_time = round(time.time() - t0, 3)
    print(f"Full Render Completed in: {full_render_time:.2f}s (Status: {detail.status.value})")

    if detail.status.value != "succeeded":
        print("Initial job failed, aborting benchmark.")
        return

    # 2. Measure Incremental Re-render for Scene 2
    print("\nExecuting Incremental Clip Replacement for Scene 2...")
    t1 = time.time()
    await job_manager.replace_scene_footage(
        job_id=job_id,
        scene_number=2,
        custom_query="advanced robotics laboratory artificial intelligence"
    )
    rerender_time = round(time.time() - t1, 3)
    print(f"Incremental Re-render Completed in: {rerender_time:.2f}s")

    # 3. Calculate Benchmark Metrics
    time_saved = round(full_render_time - rerender_time, 3)
    speedup_pct = round(((full_render_time - rerender_time) / full_render_time) * 100, 1)
    speedup_ratio = round(full_render_time / max(0.001, rerender_time), 2)

    result = {
        "job_id": job_id,
        "total_scenes": len(detail.scenes),
        "aspect_ratios": [r.value for r in detail.request.get("aspect_ratios", [])] if hasattr(detail, "request") else ["16:9", "9:16", "1:1"],
        "full_render_time_seconds": full_render_time,
        "incremental_rerender_time_seconds": rerender_time,
        "time_saved_seconds": time_saved,
        "speedup_percentage": speedup_pct,
        "speedup_factor": f"{speedup_ratio}x",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "conclusion": f"Incremental clip replacement saved {time_saved:.2f}s ({speedup_pct}% faster than full render)."
    }

    out_file = BASE_DIR / "evidence" / "rerender_benchmark.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("\n--- Benchmark Results ---")
    print(f"Full Render Time:        {full_render_time:.2f}s")
    print(f"Incremental Re-render:   {rerender_time:.2f}s")
    print(f"Time Saved:              {time_saved:.2f}s")
    print(f"Speedup:                 {speedup_ratio}x ({speedup_pct}%)")
    print(f"Saved benchmark to:      {out_file}")

if __name__ == "__main__":
    asyncio.run(benchmark_rerender())
