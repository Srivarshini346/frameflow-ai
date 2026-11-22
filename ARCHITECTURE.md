# ARCHITECTURE.md – FrameFlow AI Technical Architecture

This document provides a comprehensive technical breakdown of the FrameFlow AI pipeline, detailing the concurrent footage acquisition engine, meaning-based discourse segmentation, relevance scoring mechanisms, and FFmpeg video compositing.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Client["Client Interface"]
        UI["React 18 Multi-Track Studio"]
        CLI["Batch CLI Runner / Benchmark Tools"]
    end

    subgraph Gateway["FastAPI Service Tier"]
        Router["API Gateway (/api/v1/broll/jobs)"]
        Idemp["Idempotency Engine (SHA256 Payload Hash)"]
        JobMgr["Async Background Job Manager"]
        DB[(SQLite Persistent Store)]
    end

    subgraph SpeechAI["Speech & Discourse Intelligence"]
        ASR["ASR Adapter (faster-whisper / Mock)"]
        TTS["TTS Adapter (gTTS / Edge-TTS / Mock)"]
        SceneEng["Scene Engine (Grammatical Clause Boundaries)"]
        QueryIntel["Query Intelligence & Homonyms"]
        Safety["Entity Protection & Avoid Filter"]
    end

    subgraph FootagePipeline["Concurrent Footage Orchestration Engine"]
        Pexels["Pexels Video API (1080p, Orientation)"]
        Pixabay["Pixabay Video API (Large MP4)"]
        Dedup["Zero-Duplicate Filter (seen_clip_ids)"]
        Scorer["Relevance Scorer (CLIP ViT-B/32 / Keyword Cosine)"]
        Downloader["Download Stream & FFprobe Container Validator"]
        MockFallback["CC0 Procedural Synthetic Fallback"]
    end

    subgraph Compositing["Compositing & Deliverables"]
        SmartCrop["OpenCV Haar Saliency Smart Crop (9:16)"]
        Normalizer["Color & Brightness Normalization (eq filter)"]
        FFmpeg["FFmpeg Native Compositor (30 FPS, H.264/AAC)"]
        Subtitles["Responsive Subtitle Burner (libass / drawtext)"]
        Validator["Post-Render FFprobe Validator"]
        Storage["Storage Service (Local Disk / MinIO S3)"]
    end

    Client -->|HTTP / OpenAPI 3.1| Router
    Router --> Idemp --> JobMgr
    JobMgr <--> DB
    JobMgr --> ASR & TTS
    JobMgr --> SceneEng --> QueryIntel --> Safety
    QueryIntel --> FootagePipeline
    Pexels & Pixabay --> Dedup --> Scorer
    Scorer -->|Score >= 0.40| Downloader
    Scorer -.->|Score < 0.40 or Timeout| MockFallback
    Downloader --> Compositing
    Compositing --> Storage
```

---

## 2. Footage Pipeline & Fallback Chain

The footage orchestration engine enforces strict commercial compliance, concurrency, query variations, and download integrity:

```mermaid
sequenceDiagram
    autonumber
    participant Scene as Scene Engine
    participant QI as Query Intelligence
    participant Safety as Safety Guard
    participant Foot as Footage Service
    participant Pex as Pexels Provider
    participant Pix as Pixabay Provider
    participant Score as Relevance Scorer
    participant Down as Download & FFprobe
    participant Mock as Mock Provider Fallback

    Scene->>QI: Narration text + context
    QI->>QI: Disambiguate homonyms (bank, cloud, mouse, python)
    QI->>QI: Translate metaphors (soaring inflation -> supermarket prices)
    QI-->>Safety: Primary query + 2 fallback variations
    Safety->>Safety: Replace named persons/brands with generic visuals
    Safety->>Safety: Strip user avoid terms
    Safety-->>Foot: Clean queries [Q1, Q2, Q3]

    loop For each query in [Q1, Q2, Q3]
        Foot->>Pex: Search Q (orientation, min_duration) [Async]
        Foot->>Pix: Search Q (orientation, min_duration) [Async]
        Note over Foot,Pix: asyncio.gather concurrent fetch with 8s timeout
        Pex-->>Foot: Return candidate clips
        Pix-->>Foot: Return candidate clips
        Foot->>Foot: Pool & deduplicate against seen_clip_ids
        Foot->>Safety: Validate candidate tags against avoid list
        Foot->>Score: Score candidate frames/tags (CLIP ViT-B/32)
        Score-->>Foot: Unclamped Score (0.0-1.0) & Star Rating (1-5★)
        opt If Best Score >= RELEVANCE_MIN (0.40)
            Foot->>Down: Stream download to disk
            Down->>Down: Validate with FFprobe (size >= 1KB, duration > 0, video stream)
            alt Download Valid
                Down-->>Foot: Confirmed valid local MP4
                Note over Foot: Select clip, register in seen_clip_ids, exit loop
            else Corrupt / Failed Download
                Down-->>Foot: File invalid -> unlink corrupt file, try next candidate
            end
        end
    end

    opt All real providers empty, below threshold, or keys unconfigured
        Foot->>Mock: Request CC0 synthetic clip
        Mock-->>Foot: Return local 1080p procedural MP4
        Foot->>Foot: Append explicit warning to scene: "mock fallback used: <reason>"
    end
```

---

## 3. Homonym Disambiguation Architecture

FrameFlow AI resolves double-meaning words based on contextual tokens in the narration phrase:

| Homonym | Tech Context Keywords | Tech Visual Output | Nature/Literal Context | Nature Visual Output |
| :--- | :--- | :--- | :--- | :--- |
| **`bank`** | money, finance, deposit, loan, account, cash, savings | `financial corporate banking` | river, stream, shore, water, flowers, grass | `river bank nature` |
| **`cloud`** | data, server, computing, storage, network, AWS, software | `server room technology` | sky, cumulus, weather, blue, time-lapse | `clouds sky time-lapse` |
| **`mouse`** | computer, click, screen, laptop, cursor, desk | `computer mouse desk` | rodent, wild, field, outdoor, grass | `field mouse nature` |
| **`python`** | code, programming, developer, software, script, algorithm | `software developer coding` | snake, rainforest, branch, reptile, wildlife | `python snake wildlife` |
| **`value`** | sales, revenue, growth, stock, market, finance, investor | `stock market chart growth` | partnership, handshake, agreement, trust | `business partnership handshake` |

---

## 4. Entity Safety & Real Person Guard

To maintain strict commercial clearance and brand safety:
1. **Real Public Figures:** Automatically replaced with generic professional stand-ins.
   - *Input:* `"Elon Musk announces new technology initiative."`
   - *Transformed Intent:* `"technology entrepreneur and tech executive stage presentation announces new technology initiative."`
   - *Timeline Record:* Safety warning logged: `"Safety Guard: Detected real person / brand entity 'elon musk'. Substituted with generic commercial stand-in footage; realistic likeness suppressed."`
2. **Commercial Brands:** Replaced with generic product visuals (`"Apple iPhone"` $\to$ `"modern smartphone with glass display"`).
3. **Sensitive Tragedies / Disasters:** Enforces solemn, respectful landscape reflection and suppresses celebratory or graphic terms.
4. **User `avoid` Directives:** Stripped from query generation and enforced as strict blocklist on candidate clip tags.

---

## 5. Honest Relevance Scoring Specification

1. **Primary Model:** CLIP (`open_clip` ViT-B/32) measuring cosine similarity between keyframe and narration text:
   $$\text{Similarity} = \frac{\mathbf{v}_{\text{image}} \cdot \mathbf{v}_{\text{text}}}{\|\mathbf{v}_{\text{image}}\| \|\mathbf{v}_{\text{text}}\|}$$
2. **Fallback Model:** Calibrated Jaccard token overlap between query synset and candidate clip tags.
3. **Unclamped Scaling:**
   - 0.80 - 1.00 $\to$ 5 Stars (Excellent semantic and visual alignment)
   - 0.65 - 0.79 $\to$ 4 Stars (Strong match)
   - 0.50 - 0.64 $\to$ 3 Stars (Acceptable contextual match)
   - 0.35 - 0.49 $\to$ 2 Stars (Marginal alignment)
   - $< 0.35$ $\to$ 1 Star (Weak match / rejected if candidate pool allows)
4. **Transparency Contract:** The exact method is honestly declared in `timeline.json`, `manifest.json`, and the UI (`"CLIP ViT-B/32"` or `"Keyword overlap similarity heuristic"`). Heuristic overlap is never falsely labeled as "VLM".

---

## 6. Deliverable Specifications

Every job produces 6 deliverables verified by FFprobe:
1. `video_16_9.mp4`: 1920x1080 Landscape, 30 FPS, H.264 / AAC 192kbps.
2. `video_9_16.mp4`: 1080x1920 Portrait, Smart Saliency Crop, 30 FPS.
3. `video_1_1.mp4`: 1080x1080 Square, 30 FPS.
4. `captions.srt`: SubRip subtitle file with millisecond timestamp synchronization.
5. `timeline.json`: Complete per-scene metadata, provider provenance, commercial licence, and relevance scores.
6. `manifest.json`: Cryptographic seed, model inventory, stage timings, estimated compute cost, and licensing audit.
