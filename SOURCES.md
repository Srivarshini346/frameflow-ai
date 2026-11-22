# SOURCES.md – External Libraries, Models & Media Attributions

All libraries, media assets, and models used in FrameFlow AI are 100% commercially usable (MIT, BSD, Apache 2.0, CC0, Pexels, or Pixabay licences). No AGPL, CC-BY-NC, or research-only dependencies are utilized.

---

## 1. Backend Libraries & Frameworks

| Package | Licence | Purpose | Commercial Usage |
| :--- | :--- | :--- | :--- |
| **FastAPI** | MIT | Asynchronous REST API framework and routing | Cleared |
| **Uvicorn** | BSD-3-Clause | ASGI production HTTP server | Cleared |
| **Pydantic v2** | MIT | Request and response schema validation | Cleared |
| **faster-whisper** | MIT | CTranslate2-accelerated Whisper ASR for speech transcription | Cleared |
| **edge-tts** | MIT | Microsoft Neural Voice Text-to-Speech synthesis | Cleared |
| **gTTS** | MIT | Google Translate TTS client for multilingual speech | Cleared |
| **imageio-ffmpeg** | BSD-2-Clause | Cross-platform embedded FFmpeg binary locator | Cleared |
| **FFmpeg** | LGPL 2.1+ / GPL | Video compositing (H.264/AAC), 3 aspect ratios, subtitle burning | Cleared |
| **OpenCV (`cv2`)** | Apache 2.0 | Haar cascade face and subject detection for 9:16 smart crop | Cleared |
| **boto3 / botocore** | Apache 2.0 | AWS S3 / MinIO object storage SDK | Cleared |
| **httpx** | BSD-3-Clause | Asynchronous HTTP client for provider and webhook calls | Cleared |
| **pytest & pytest-asyncio** | MIT / Apache 2.0 | Automated unit and integration test runner | Cleared |
| **NumPy & SciPy** | BSD-3-Clause | Waveform PCM processing, Pearson and Spearman correlation | Cleared |
| **scikit-learn** | BSD-3-Clause | Semantic TF-IDF and vector cosine similarity scoring | Cleared |
| **PyYAML** | MIT | OpenAPI 3.1 YAML parsing and generation | Cleared |
| **aiosqlite** | MIT | Asynchronous SQLite interface for job metadata persistence | Cleared |
| **python-dotenv** | BSD-3-Clause | Environment variable parsing | Cleared |

---

## 2. Frontend Libraries & Frameworks

| Package | Licence | Purpose | Commercial Usage |
| :--- | :--- | :--- | :--- |
| **React 18** | MIT | User interface rendering engine | Cleared |
| **React DOM** | MIT | Browser DOM integration | Cleared |
| **Vite** | MIT | Frontend build tooling and fast dev server | Cleared |
| **Lucide React** | ISC | SaaS user interface icons | Cleared |

---

## 3. Media & Footage Licences

| Provider | Applicable Licence | Commercial Clearance | Attribution Required |
| :--- | :--- | :--- | :--- |
| **MockProvider Synthetic Archive** | Creative Commons Zero (CC0 1.0 Universal) | **Yes (100% Cleared)** | Optional; recorded in `manifest.json` |
| **Pexels Video API** | Pexels License | **Yes (100% Cleared)** | Optional; recorded in `manifest.json` |
| **Pixabay Video API** | Pixabay Content License | **Yes (100% Cleared)** | Optional; recorded in `manifest.json` |

*Zero copyrighted media, zero non-commercial clips, and zero unauthorized web scraping are used in FrameFlow AI.*
