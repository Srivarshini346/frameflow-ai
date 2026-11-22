import re
from typing import List, Dict, Any, Optional, Tuple
from app.models.api_schemas import SceneDetail, VisualPromptStyle, LanguageCode
from app.core.logger import logger

class SceneEngine:
    """
    Intelligent Meaning-Based Scene Segmentation and Visual Query Formulation Engine.
    
    Principles:
    1. NEVER divides script into arbitrary equal-length chunks.
    2. Uses discourse markers, clause boundaries, and sentence delimiters.
    3. Transforms abstract concepts, numbers, and metaphors into physical visual actions.
    4. Enforces negative avoidance keywords.
    5. Calculates realistic start/end timestamps based on audio length and phrase weighting.
    """

    ABSTRACT_VISUAL_MAP = {
        "technology": "modern digital interface with glowing data streams and engineer working",
        "artificial intelligence": "futuristic neural network visualization and human collaborator",
        "ai": "futuristic holographic display and AI software interaction",
        "learning": "focused student interacting with interactive digital education tablet in modern space",
        "education": "vibrant university seminar with engaging presentation and students",
        "healthcare": "advanced medical clinic with clinician viewing dynamic diagnostic monitors",
        "future": "sleek smart city skyline at golden hour with autonomous clean transit",
        "growth": "upward financial charts and confident diverse team celebrating milestone",
        "finance": "dynamic stock market floor and modern fintech analytics dashboard",
        "climate": "lush green renewable energy wind turbines over sunlit rolling hills",
        "nature": "serene mountain lake with mist rising under clear morning light",
        "innovation": "high-tech research laboratory with scientists testing modern prototype",
        "speed": "fast motion blurred timelapse of modern city traffic lights at night",
        "data": "server room with blinking blue LED lights and flowing optical fibre data",
        "security": "cybersecurity lock interface and encrypted shield protocol visual",
        "collaboration": "diverse team gathered around creative studio table brainstorming",
    }

    # Sentence and clause boundary patterns for English, Hindi (पूर्णविराम ।), and Tamil
    BOUNDARY_REGEX = re.compile(
        r'(?<=[.?!;।\n])\s+'                       # Standard punctuation + Hindi purna viram
        r'|(?<=[,])\s+(?=(?:and|but|however|therefore|while|whereas|moreover|because|meanwhile)\b)', # Clause conjunctions
        flags=re.IGNORECASE
    )

    def segment_script_into_scenes(
        self,
        script_text: str,
        total_audio_duration: float,
        style: VisualPromptStyle = VisualPromptStyle.CINEMATIC,
        style_instructions: Optional[str] = None,
        avoid_instructions: Optional[List[str]] = None,
        language: LanguageCode = LanguageCode.EN
    ) -> List[SceneDetail]:
        """
        Splits script text into semantic scenes, formulating visual descriptions and
        calculating duration proportional to syllable/word length across total audio time.
        """
        clean_text = script_text.strip()
        if not clean_text:
            return []

        # Split on semantic phrase boundaries
        raw_chunks = self.BOUNDARY_REGEX.split(clean_text)
        phrases: List[str] = []
        for chunk in raw_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            # If a chunk is very long (>25 words), split on comma or semicolon
            if len(chunk.split()) > 25:
                sub_chunks = re.split(r'[,;]\s+', chunk)
                for sc in sub_chunks:
                    sc = sc.strip()
                    if sc:
                        phrases.append(sc)
            else:
                phrases.append(chunk)

        if not phrases:
            phrases = [clean_text]

        # Calculate phrase weights (based on word count + character count)
        weights = [max(1.0, len(p.split()) + len(p) * 0.1) for p in phrases]
        total_weight = sum(weights)

        # Distribute total audio duration across phrases
        scenes: List[SceneDetail] = []
        current_time = 0.0
        avoid_set = {a.lower().strip() for a in (avoid_instructions or [])}

        for i, phrase in enumerate(phrases):
            fraction = weights[i] / total_weight
            duration = max(1.5, round(total_audio_duration * fraction, 2))
            
            # Ensure the last scene aligns exactly with total duration
            if i == len(phrases) - 1:
                duration = max(1.0, round(total_audio_duration - current_time, 2))
                end_time = round(total_audio_duration, 2)
            else:
                end_time = round(current_time + duration, 2)

            # Generate meaning-based visual description and query
            visual_desc, query = self._generate_visual_intent(
                phrase=phrase,
                style=style,
                style_instructions=style_instructions,
                avoid_set=avoid_set,
                language=language
            )

            scene = SceneDetail(
                scene_number=i + 1,
                narration_text=phrase,
                start_time=round(current_time, 2),
                end_time=end_time,
                duration=round(end_time - current_time, 2),
                visual_description=visual_desc,
                search_query=query,
                ai_generated=True,
                relevance_score=0.0,
                selection_reason=f"Meaning matched to semantic phrase: '{phrase[:40]}...'"
            )
            scenes.append(scene)
            current_time = end_time

        logger.info(f"Segmented script into {len(scenes)} intelligent scenes over {total_audio_duration}s")
        return scenes

    def _generate_visual_intent(
        self,
        phrase: str,
        style: VisualPromptStyle,
        style_instructions: Optional[str],
        avoid_set: set,
        language: LanguageCode
    ) -> Tuple[str, str]:
        """
        Transforms narrative meaning into concrete physical scenes.
        Translates metaphors, numbers, and abstract buzzwords into filmed actions.
        """
        lower_phrase = phrase.lower()
        matched_visuals = []
        query_terms = []

        # Check semantic map
        for key, visual in self.ABSTRACT_VISUAL_MAP.items():
            if key in lower_phrase:
                matched_visuals.append(visual)
                query_terms.append(key)

        # Handle numbers or metrics
        if re.search(r'\b\d+(?:\.\d+)?%?\b', phrase):
            matched_visuals.append("infographic digital chart overlay with increasing metrics")
            query_terms.append("analytics growth")

        # Fallback if no specific abstract map matched
        if not matched_visuals:
            # Extract key nouns and verbs
            words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in lower_phrase.split()]
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "to", "in", "of", "for", "with", "on", "at", "by", "from", "up", "about", "into", "over", "after"}
            meaningful = [w for w in words if w and w not in stopwords and len(w) > 3]
            
            # Filter out avoid keywords
            meaningful = [w for w in meaningful if w not in avoid_set]
            
            selected_words = meaningful[:4] if meaningful else ["cinematic", "scenic", "atmosphere"]
            query_terms = selected_words
            matched_visuals.append(f"dynamic scene depicting {' '.join(selected_words)}")

        # Construct visual description with style
        style_tag = f"{style.value} shot"
        if style_instructions:
            style_tag += f", {style_instructions}"

        visual_desc = f"{style_tag}: {'; '.join(matched_visuals)}"

        # Enforce negative avoidance
        for avoid in avoid_set:
            if avoid in visual_desc.lower():
                visual_desc = visual_desc.replace(avoid, "alternative atmosphere")

        # Formulate concise footage search query (2-3 words for high recall in video providers)
        clean_query_terms = [q for q in query_terms if q not in avoid_set]
        search_query = " ".join(clean_query_terms[:3]) if clean_query_terms else "cinematic concept"

        return visual_desc, search_query

scene_engine = SceneEngine()
