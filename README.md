# FrameFlow AI – Intelligent B-roll Studio
### Script and Voiceover to B-roll Video Engine (IncuBrix PS3 Technical Assessment)

FrameFlow AI is an end-to-end, production-grade AI video production engine designed to transform scripts and audio voiceovers into verified, commercially cleared B-roll videos across **16:9 Landscape**, **9:16 Portrait**, and **1:1 Square** formats with burned-in subtitles and synchronized narration.

---

## 1. Key Capabilities & Highlights

- **Meaning-Based Scene Segmentation:** Employs clause and discourse marker parsing (never arbitrary equal chunks) to divide narration into coherent semantic scenes.
- **Multilingual Voiceover Support:** Synthesizes and aligns narration in **English**, **Hindi (हिंदी)**, and **Tamil (தமிழ்)** with pitch and rate controls.
- **Commercial Licensing & Zero Web Scraping:** Pluggable adapter architecture (Pexels, Pixabay, MockProvider) enforcing 100% commercial clearance (CC0 / Pexels License / Pixabay License) and recording full attribution in `manifest.json`.
- **Zero Duplicate Clip Prevention:** Global project clip registry ensures no clip is reused across scenes within the same video.
- **Incremental Clip-Level Rerendering:** When a single scene is modified, only that scene's clip is re-rendered and concatenated, updating the video in seconds without re-rendering the entire timeline.
- **Native FFmpeg Compositor:** Outputs 1080p-class, 30 FPS, H.264 video with AAC audio, responsive subtitle burning, and standalone `captions.srt`.
- **Pure Light-Theme SaaS UI:** Elegant, responsive React 18 interface with ivory background (`#FBFBFA`), soft lavender (`#7C6EE6`), mint accents, and dark navy typography.
- **Zero Paid Dependencies Required:** Runs fully offline out of the box using high-speed procedural mock footage and local audio synthesis.

---

## 2. Architecture Overview

```
c:\Users\Lenovo\Desktop\incubrix\
├── backend/
│   ├── app/
│   │   ├── api/          # Routers (/broll/jobs, /jobs/{id}, /health, /analytics, /tts)
│   │   ├── core/         # Logging (JSON), Idempotency, HMAC-SHA256, Exceptions
│   │   ├── models/       # Pydantic v2 schemas
│   │   ├── providers/    # Pexels, Pixabay, and CC0 Mock Footage Adapters
│   │   └── services/     # AudioService, SceneEngine, FootageService, VideoEngine, CaptionService
│   ├── tests/            # 18 Automated Scenario Suites + Test Pack
│   ├── test_pack/        # 10 Multi-lingual and Multi-domain Script Samples
│   └── requirements.txt
├── frontend/             # React 18 + Vite (Pure Light Theme)
│   ├── src/components/   # Dashboard, Studio, Workspace, Player, Scene Editor, History, Analytics
│   └── dist/             # Production static SPA bundle
├── cli/
│   └── batch_runner.py   # CLI batch runner for automated multi-script processing
├── Dockerfile            # Multi-stage container build
├── docker-compose.yml    # Orchestrates FrameFlow and MinIO
├── openapi.yaml          # OpenAPI 3.1 specification
├── README.md
├── REPORT.md
├── SOURCES.md
└── AI_USE.md
```

---

## 3. Quickstart & Installation

### Option A: Local Development (Windows / Linux / macOS)

1. **Prerequisites:**
   - Python 3.11
   - Node.js 18+ & npm
   - FFmpeg (automatically detected via `imageio-ffmpeg` or system PATH)

2. **Backend Setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup:**
   ```bash
   cd ../frontend
   npm install
   npm run build
   ```

4. **Launch Application:**
   ```bash
   cd ..
   python backend/app/main.py
   ```
   Open your browser at **http://localhost:8000** to access the complete application!

---

### Option B: Docker Compose

```bash
docker-compose up --build
```
Access the application at **http://localhost:8000**.

---

## 4. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/broll/jobs` | Submits narration script or uploaded audio. Returns `202 Accepted` with `job_id`. |
| `GET` | `/api/v1/jobs/{job_id}` | Real-time status (`queued`, `running`, `succeeded`, `failed`), progress `0-100%`, and stage. |
| `GET` | `/api/v1/jobs/{job_id}/result` | Full deliverables (`video_16_9`, `video_9_16`, `video_1_1`, `captions_srt`, `timeline_json`, `manifest_json`). |
| `POST` | `/api/v1/jobs/{job_id}/scenes/{scene_num}/replace` | **Incremental Rerender:** Replaces footage of a single scene and updates all aspect ratios. |
| `GET` | `/health` & `/ready` | Deep health check (FFmpeg binary status, storage writeability, version). |
| `GET` | `/api/v1/analytics` | Provider statuses, resource metrics, and licensing policy. |
| `POST` | `/api/v1/tts/synthesize` | Standalone multi-lingual speech preview (EN, HI, TA). |

---

## 5. Output Deliverables

Every successful generation creates 6 deliverables in `storage/jobs/{job_id}/`:
1. `video_16_9.mp4`: 1920x1080 Landscape video.
2. `video_9_16.mp4`: 1080x1920 Vertical Portrait video (Shorts / Reels / TikTok).
3. `video_1_1.mp4`: 1080x1080 Square video (Instagram / LinkedIn).
4. `captions.srt`: SubRip subtitle file with millisecond timestamps.
5. `timeline.json`: Scene breakdown with start/end timestamps, clip IDs, relevance scores, and selection rationale.
6. `manifest.json`: Complete audit trail containing models, version, processing duration, and copyright attribution.

---

## 6. Running Automated Tests

Run the test suite covering all 18 mandatory assessment scenarios and the 10-script test pack:
```bash
python -m pytest backend/tests -v
```

All 19 test suites pass without requiring external API keys.

---

## 7. Batch CLI Runner

To process a batch of scripts non-interactively:
```bash
python cli/batch_runner.py --input backend/test_pack/sample_scripts.json --output storage/batch_runs
```
