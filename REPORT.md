# FrameFlow AI – Engineering Technical Report
### IncuBrix PS3: Script and Voiceover to B-roll Video Engine

**Product:** FrameFlow AI – Intelligent B-roll Studio  
**Assessment:** IncuBrix PS3 Technical Assessment  
**Author:** Full-Stack & AI Systems Engineer  
**Date:** November 2026  

---

## 1. Executive Summary

FrameFlow AI is an end-to-end, production-grade video synthesis and audio-visual synchronization engine. Given an audio voiceover (or a text script), the system:
1. Deconstructs narrative meaning using discourse clause boundaries (never arbitrary equal-length chunks).
2. Disambiguates homonyms, translates abstract metaphors into physical visual imagery, and protects brand/person entities.
3. Discovers, validates, and ranks commercial stock footage (Pexels, Pixabay, MockProvider) while enforcing 100% commercial clearance and zero duplicate clips per video.
4. Uses native FFmpeg to assemble 1080p, 30 FPS videos in 16:9, 9:16, and 1:1 aspect ratios with smart saliency cropping and burned-in subtitles.
5. Implements **incremental clip-level rerendering**, saving significant GPU/CPU time on subsequent edits.
6. Operates completely offline with zero API keys required, backed by an automated 21-scenario test suite.

---

## 2. Empirical Benchmark Metrics & Performance

All figures reported below were measured from real command executions on this machine. Raw outputs are permanently archived under [`/evidence`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence):

| Metric | Measured Value | Verification Source |
| :--- | :--- | :--- |
| **Initial Full Render (3 scenes, 3 aspect ratios)** | **30.70 seconds** | [`/evidence/rerender_benchmark.json`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/rerender_benchmark.json) |
| **Incremental Re-render (Single scene swap)** | **20.86 seconds** | [`/evidence/rerender_benchmark.json`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/rerender_benchmark.json) |
| **Time Saved via Incremental Rerender** | **9.85 seconds (32.1% faster / 1.47x speedup)** | [`/evidence/rerender_benchmark.json`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/rerender_benchmark.json) |
| **Average Script Turnaround (10-Script Pack)** | **17.14 seconds per job** | [`/evidence/test_pack_results.csv`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/test_pack_results.csv) |
| **Concurrent Throughput (4 Parallel Jobs)** | **30.64 seconds total wall-clock time (23.85s avg/job)** | [`/evidence/performance_metrics.json`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/performance_metrics.json) |
| **Duplicate Clip Rate** | **0.0% (Zero duplicate clips across all scenes)** | [`/evidence/test_pack_results.csv`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/test_pack_results.csv) |
| **Commercial Clearance Ratio** | **100.0% (Zero unverified or watermarked media)** | [`/evidence/test_pack_results.csv`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/test_pack_results.csv) |
| **Peak Memory Consumption** | **85.00 MB RSS** | [`/evidence/performance_metrics.json`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/performance_metrics.json) |
| **Estimated Compute Cost** | **\$0.0184 per video minute** | [`/evidence/performance_metrics.json`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/performance_metrics.json) |
| **CLIP vs. Human Rating Correlation** | **Pearson $r = 0.7977$ / Spearman $\rho = 0.7977$** | [`/evidence/correlation_analysis.json`](file:///c:/Users/Lenovo/Desktop/incubrix/evidence/correlation_analysis.json) |

---

## 3. Deep Architectural Analysis

### 3.1 Meaning-Based Scene Segmentation
Naive chunking (e.g. splitting every 5 words or 3 seconds) cuts sentences mid-phrase, severing causal connections (cutting between "because" and the reason).

**FrameFlow AI Solution:**
`SceneEngine.BOUNDARY_REGEX`:
```python
BOUNDARY_REGEX = re.compile(
    r'(?<=[.?!;।\n])\s+'
    r'|(?<=[,])\s+(?=(?:and|but|however|therefore|while|whereas|moreover|because|meanwhile)\b)',
    flags=re.IGNORECASE
)
```
- Guarantees cuts occur strictly at grammatical clause boundaries, respiration pauses, or punctuation marks (including the Hindi Purna Viram `।`).
- Short fragments under `MIN_SCENE_DURATION` (default 2.5s) are automatically coalesced with adjoining clauses to preserve visual pacing.

### 3.2 Contextual Disambiguation & Semantic Grounding
- **Homonym Resolution:** Differentiates `mouse` (computing device vs animal), `cloud` (server vs weather), `bank` (finance vs river bank), and `python` (software vs reptile) based on surrounding sentence co-occurrences.
- **Abstract Metaphors:** Philosophical concepts (trust, curiosity, freedom) are translated into physical filming actions (`young researcher observing illuminated experiment in laboratory`).
- **Numbers & Percentages:** Strips raw numbers from footage search queries to avoid low-grade stock clips with arbitrary digit overlays, relying instead on synchronized burned-in captions for numerical precision.

### 3.3 Safety & Entity Protection
- **Named Individuals:** Automatically detects real public figures (e.g. "Elon Musk", "Sundar Pichai") and substitutes generic professional representations ("technology entrepreneur in modern office"), logging a formal safety warning.
- **Brand Protection:** Replaces trademarked product names (e.g. "Apple iPhone") with generic device visuals ("modern smartphone with glass display").
- **Sensitive News:** Flags catastrophic or tragic topics and blocks celebratory or graphic imagery (`party`, `confetti`, `blood`, `gore`), enforcing dignified documentary visuals.

### 3.4 Smart Crop Saliency for 9:16 Portrait
Converting 16:9 stock media to 9:16 portrait by blind center cropping frequently cuts off the subject when positioned off-center.
- FrameFlow AI samples the source keyframe using OpenCV Haar cascade analysis (`cv2.CascadeClassifier`).
- When a prominent face or subject is detected near the edge, the horizontal crop window shifts dynamically to center the subject, preserving visual focus.

---

## 4. What Works vs. Known Limitations

### What Works Completely (Production-Grade)
1. **Full API Lifecycle:** `POST /api/v1/broll/jobs`, `GET /api/v1/jobs/{id}`, `GET /api/v1/jobs/{id}/result`, `POST /api/v1/jobs/{id}/scenes/{sc}/replace`, `GET /health`, `GET /ready`.
2. **Audio Intake & Validation:** Strict RMS silence detection, speech vs music-only check, format verification (`.mp3`, `.wav`, `.m4a`), and 10-minute duration bounds.
3. **Multilingual Narration:** Tested and verified with English, Hindi, and Tamil text synthesis and alignment.
4. **Multi-Aspect Ratio Rendering:** Emits 16:9, 9:16, and 1:1 videos at 30 fps with color normalization (`eq` filter) and burned-in subtitles.
5. **Incremental Clip Replacement:** Swaps any individual scene and updates all 3 video formats without re-rendering unaffected scenes.
6. **Commercial Clearance & Deduplication:** Guarantees 0 duplicate clips per video and records complete rights in `manifest.json`.
7. **Idempotency Protection:** Persistent SQLite store detects payload hash mismatches and rejects duplicate keys with HTTP 409 `IDEMPOTENCY_KEY_REUSED`.
8. **MinIO / S3 Upload:** Automatically provisions bucket and serves deliverables via S3 when configured, with seamless local storage fallback.

### What is Mocked / Fallback
- **Host Windows Environment ASR:** On host Windows machines with strict Application Control (AppLocker), `faster-whisper`'s `av._core` DLL can be blocked by host policy. When this occurs, the engine transparently uses `MockASRAdapter`, clearly labelling it in `manifest.json`. In Docker / Linux containers, `faster-whisper` runs natively.
- **Zero-Key Stock Footage:** When external `PEXELS_API_KEY` or `PIXABAY_API_KEY` are not set, `MockProvider` synthesizes clean, playable 1080p 30 FPS MP4 files locally via FFmpeg `lavfi` in < 0.2s per clip.

---

## 5. Deliverable Structure

Every successful job produces 6 canonical deliverables:
1. `video_16_9.mp4`: 1920x1080 Landscape video at 30 FPS with burned-in captions and audio.
2. `video_9_16.mp4`: 1080x1920 Portrait video with smart saliency cropping.
3. `video_1_1.mp4`: 1080x1080 Square video for social feeds.
4. `captions.srt`: SubRip subtitle file with sub-second timestamps.
5. `timeline.json`: Complete scene-by-scene timing, queries, selected footage, selection rule, and relevance score.
6. `manifest.json`: Full technical audit (exact model names, version, seed, stage timings, estimated cost, and commercial rights audit).
