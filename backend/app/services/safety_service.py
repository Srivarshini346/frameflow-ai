import re
from typing import List, Tuple, Dict, Any
from app.models.api_schemas import FootageClip
from app.core.logger import logger

class SafetyService:
    """
    Safety Module:
    1. Detects named real people & commercial brands in narration -> replaces with generic stand-in visuals; logs warning.
    2. Detects sensitive / sad news -> ensures respectful, neutral visuals; blocks celebratory/graphic terms.
    3. Strictly enforces user 'avoid' directives on queries, tags, and candidate clips.
    4. Prohibits realistic AI-generated faces.
    """

    KNOWN_ENTITIES = {
        # Real people
        "elon musk": "technology entrepreneur working in modern engineering office",
        "steve jobs": "visionary product designer in modern tech studio",
        "donald trump": "government building and diplomatic conference hall",
        "narendra modi": "international diplomatic summit with flags",
        "sundar pichai": "corporate executive in bright modern headquarters",
        "mark zuckerberg": "software team collaborating on digital interface",
        "bill gates": "philanthropic researcher reviewing global health charts",
        "tim cook": "corporate technology leadership presentation",
        
        # Commercial brands
        "apple": "sleek modern mobile smartphone with clean glass screen",
        "iphone": "modern smartphone with glass display",
        "google": "high speed internet digital data search visual",
        "microsoft": "enterprise cloud computing desktop workflow",
        "tesla": "modern electric vehicle driving on scenic highway",
        "amazon": "automated modern logistics fulfillment center",
        "nike": "athletic runner training on outdoor scenic track",
        "coca cola": "refreshing cold sparkling beverage glass on table"
    }

    SENSITIVE_NEWS_TERMS = {
        "death", "died", "funeral", "tragedy", "disaster", "earthquake", "flood",
        "crash", "casualty", "mourning", "victim", "crisis", "fatal", "grief"
    }

    BLOCKLIST_GRAPHIC_CELEBRATORY = {
        "party", "club", "confetti", "fireworks", "champagne", "graphic", "blood", "gore"
    }

    def sanitize_text_query(self, text: str) -> str:
        """
        Sanitizes text query replacing named entities and brands with generic stand-in visuals.
        """
        q, v, _, _ = self.sanitize_scene_intent(text, text, text, [])
        return f"{q} {v}"

    def sanitize_scene_intent(
        self,
        phrase: str,
        visual_intent: str,
        query: str,
        avoid_list: List[str]
    ) -> Tuple[str, str, str, List[str]]:
        """
        Sanitizes search query and visual intent:
        Returns: (sanitized_query, sanitized_visual_intent, filtered_avoid, warnings)
        """
        warnings: List[str] = []
        lower_phrase = phrase.lower()
        lower_query = query.lower()

        clean_query = query
        clean_visual = visual_intent

        # 1. Detect named real people and brands
        for entity, standin in self.KNOWN_ENTITIES.items():
            pattern = r'\b' + re.escape(entity) + r'\b'
            if re.search(pattern, lower_phrase) or re.search(pattern, lower_query):
                clean_query = re.sub(pattern, standin.split()[0], clean_query, flags=re.IGNORECASE)
                clean_visual = re.sub(pattern, standin, clean_visual, flags=re.IGNORECASE)
                warning_msg = (
                    f"Safety Guard: Detected real person / brand entity '{entity}'. "
                    f"Substituted with generic commercial stand-in footage; realistic likeness suppressed."
                )
                warnings.append(warning_msg)
                logger.info(warning_msg)

        # 2. Detect sensitive / sad news
        is_sensitive = any(re.search(r'\b' + re.escape(term) + r'\b', lower_phrase) for term in self.SENSITIVE_NEWS_TERMS)
        if is_sensitive:
            clean_query = "peaceful solemn nature landscape reflection"
            clean_visual = "respectful, neutral footage: serene landscape with calm waters and gentle morning mist"
            warning_msg = "Safety Guard: Sensitive topic detected. Enforced respectful, neutral footage; blocked celebratory/graphic content."
            warnings.append(warning_msg)
            logger.info(warning_msg)

        # 3. Enforce avoid keywords on query & visual intent
        clean_avoid = [a.strip().lower() for a in avoid_list if a.strip()]
        for avoid_term in clean_avoid:
            if avoid_term in clean_query.lower():
                clean_query = re.sub(r'\b' + re.escape(avoid_term) + r'\b', 'cinematic atmosphere', clean_query, flags=re.IGNORECASE).strip()
            if avoid_term in clean_visual.lower():
                clean_visual = re.sub(r'\b' + re.escape(avoid_term) + r'\b', 'alternative aesthetic', clean_visual, flags=re.IGNORECASE)

        return clean_query.strip(), clean_visual, clean_avoid, warnings

    def evaluate_candidate_clip(
        self,
        clip: FootageClip,
        avoid_list: List[str],
        is_sensitive: bool = False
    ) -> Tuple[bool, str]:
        """
        Validates clip before selection:
        - Rejects any clip matching avoid keywords
        - Rejects celebratory/graphic clips if sensitive news
        - Rejects realistic AI faces
        """
        text_corpus = (" ".join(clip.tags) + " " + clip.attribution + " " + clip.clip_id).lower()

        # Check avoid terms
        for term in avoid_list:
            if term and term.lower() in text_corpus:
                return False, f"Clip matches avoid directive: '{term}'"

        # Check graphic / celebratory terms for sensitive news
        if is_sensitive:
            for term in self.BLOCKLIST_GRAPHIC_CELEBRATORY:
                if term in text_corpus:
                    return False, f"Clip contains inappropriate tone for sensitive news: '{term}'"

        # Realistic face AI guard
        if clip.is_ai_generated and any(w in text_corpus for w in ("portrait", "face", "human-likeness", "celebrity")):
            return False, "Safety Guard: AI-generated realistic human face prohibited."

        return True, ""

safety_service = SafetyService()
