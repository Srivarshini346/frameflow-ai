# FrameFlow AI – Hard Cases & Edge Scenarios

This document records how FrameFlow AI handles complex semantic, audio, and visual edge cases that typically break simple keyword-based or naive video generation pipelines.

---

## 1. Homonym Disambiguation

Words with multiple meanings are resolved using grammatical and semantic context rather than naive dictionary lookup:

| Term | Context 1 (Technology / Computing) | Generated Visual & Query | Context 2 (Nature / General) | Generated Visual & Query |
| :--- | :--- | :--- | :--- | :--- |
| **"mouse"** | *"The developer clicked the computer mouse on the desk."* | Ergonomic computer mouse on office desk (`computer mouse desk`) | *"A mouse scurried through the field."* | Small wild field mouse in outdoor habitat (`field mouse nature`) |
| **"cloud"** | *"Deploy the software to the cloud server."* | Server room with glowing blue LED racks (`server room technology`) | *"Fluffy clouds drifted across the sunny sky."* | Cumulus clouds in blue sky (`clouds sky time-lapse`) |
| **"bank"** | *"The central bank lowered interest rates."* | Corporate financial bank lobby (`financial corporate banking`) | *"We walked along the river bank at dawn."* | Lush green river bank with flowing water (`river bank nature`) |
| **"python"** | *"Writing python code for neural networks."* | Software engineer typing code on laptop (`software developer coding`) | *"A green python curled on the rainforest branch."* | Tree python in tropical canopy (`python snake wildlife`) |
| **"value"** | *"Shareholder value increased this quarter."* | Corporate financial growth chart review (`business growth corporate`) | *"We value mutual trust and respect."* | Partners closing agreement with handshake (`business partnership handshake`) |

*Implemented in:* [`backend/app/services/query_intelligence.py`](file:///c:/Users/Lenovo/Desktop/incubrix/backend/app/services/query_intelligence.py)

---

## 2. Abstract Metaphors to Physical Visuals

Abstract philosophical statements cannot be directly filmed. FrameFlow AI maps intangible concepts to concrete, evocative physical metaphors:

- **"Curiosity sparks creative discovery across human history"**  
  $\rightarrow$ *Physical Visual:* Young researcher observing illuminated scientific experiment in modern laboratory (`scientific discovery lab`).
- **"Trust is earned slowly and built like a fortress"**  
  $\rightarrow$ *Physical Visual:* Artisan stonemason carefully aligning foundational stone blocks (`foundation building craft`).
- **"Time is our most fleeting asset"**  
  $\rightarrow$ *Physical Visual:* Macro close-up of intricate mechanical watch tourbillon gears rotating precisely (`clock gears time`).
- **"True freedom is a quiet state of mind"**  
  $\rightarrow$ *Physical Visual:* Hiker standing on alpine mountain summit overlooking sunrise horizon (`mountain summit sunrise`).

---

## 3. Numbers, Percentages and Statistical Reports

Statements packed with numerical data (e.g. *"Quarterly revenue expanded by 42.5% this fiscal year across 15 international divisions"*) often cause generative engines to invent garbled text or awkward infographics.

**FrameFlow AI Solution:**
1. Strips isolated digits and arithmetic tokens from stock footage search queries to avoid matching low-quality literal digit overlays.
2. Formulates neutral, high-production business visual queries: `business financial market growth`.
3. Relies on the **burned-in caption engine** to display the exact numerical figures with sub-second accuracy, ensuring 100% factual fidelity.

---

## 4. Safety Guardrails & Entity Protection

### 4.1 Real Named People
- Input: *"Elon Musk announces a breakthrough in electric battery engineering."*
- Guardrail: Replaces named individual with generic professional stand-in: `"technology entrepreneur in modern engineering office"`.
- Warning Logged: `Safety Guard: Detected real person 'elon musk'. Substituted generic visual representation.`

### 4.2 Commercial Brands
- Input: *"Reviewing the new Apple iPhone display features."*
- Guardrail: Replaces trademarked brand with generic hardware representation: `"sleek modern mobile smartphone with clean glass screen"`.

### 4.3 Sensitive & Sad News
- When tragic or somber topics are detected (*"disaster"*, *"funeral"*, *"tragedy"*, *"earthquake"*):
- Blocklist enforced: Eliminates celebratory, upbeat, or graphic visuals (`party`, `confetti`, `fireworks`, `champagne`, `blood`, `gore`).
- Enforces dignified, respectful, neutral architectural or documentary visuals.

### 4.4 User `avoid` Directives
- Strictly filters out clips whose tags or visual descriptions contain user-specified avoid tokens (e.g. `avoid: ["blood", "weapons"]`).

*Implemented in:* [`backend/app/services/safety_service.py`](file:///c:/Users/Lenovo/Desktop/incubrix/backend/app/services/safety_service.py)

---

## 5. Corrupt, Silent & Non-Speech Audio Edge Cases

| Test Case | System Behavior | HTTP Status & Error Code |
| :--- | :--- | :--- |
| **Wrong Audio Format** (`.txt`, `.pdf`, `.flac`) | Strict suffix validation (`.mp3`, `.wav`, `.m4a` only). | `400 BAD REQUEST`<br>`WRONG_AUDIO_FORMAT` |
| **Empty File** ($< 100$ bytes) | File size sanity check. | `400 BAD REQUEST`<br>`EMPTY_AUDIO` |
| **Silent Audio** (RMS $< -45$ dB) | FFmpeg `volumedetect` analysis detects complete absence of audible signal. | `422 UNPROCESSABLE CONTENT`<br>`SILENT_AUDIO` |
| **Music-Only Audio** (No vocal energy) | VAD / spectral cadence detector flags lack of speech formants. | `422 UNPROCESSABLE CONTENT`<br>`MUSIC_ONLY_AUDIO` |
| **Audio Exceeds Limit** ($> 600$s) | Rejects files exceeding 10 minutes. | `400 BAD REQUEST`<br>`AUDIO_TOO_LONG` |
| **Empty Script** (`"   "`) | Rejects whitespace-only script when no audio or scenes are provided. | `400 BAD REQUEST`<br>`EMPTY_SCRIPT` |
| **Idempotency Key Reuse with Different Body** | Persistent SQLite store detects payload SHA-256 mismatch. | `409 CONFLICT`<br>`IDEMPOTENCY_KEY_REUSED` |
