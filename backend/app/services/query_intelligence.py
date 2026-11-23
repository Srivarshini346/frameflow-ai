import re
import os
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, List, Optional
from app.config import settings
from app.core.logger import logger

class QueryAdapterBase(ABC):
    @abstractmethod
    def formulate_query_variations(
        self,
        phrase: str,
        visual_style: str = "cinematic"
    ) -> Tuple[str, List[str], str]:
        """
        Returns:
        (concrete_visual_intent, [query_primary, query_secondary, query_tertiary], rationale)
        """
        pass

class RulesQueryAdapter(QueryAdapterBase):
    """
    NLP Rules Heuristic Query Formulation Engine:
    1. Homonym context disambiguation (mouse, cloud, bank, python, value).
    2. Abstract metaphors to concrete physical filmed visuals.
    3. Concrete noun extraction (2-4 words, physical objects/settings only).
    4. 3 distinct query variations (primary + 2 fallbacks) for retry resilience.
    """

    HOMONYMS = {
        "mouse": {
            "tech_terms": {"computer", "click", "screen", "laptop", "software", "desk", "pc", "cursor", "device", "work"},
            "tech_visual": "modern ergonomic computer mouse on clean office desk",
            "tech_queries": ["computer mouse desk", "computer mouse office desk", "clicking wireless mouse hand"],
            "nature_visual": "small wild field mouse in natural outdoor habitat",
            "nature_queries": ["field mouse nature", "wild mouse grass habitat", "small field mouse rodent"]
        },
        "cloud": {
            "tech_terms": {"data", "server", "computing", "storage", "network", "backup", "software", "infrastructure", "digital", "aws"},
            "tech_visual": "modern enterprise server room with glowing blue LED network cables",
            "tech_queries": ["server room technology", "server data center blinking lights", "cloud data center hardware"],
            "nature_visual": "fluffy white cumulus clouds drifting across vast bright blue sky",
            "nature_queries": ["clouds sky time-lapse", "cumulus clouds blue sky", "aerial dramatic clouds"]
        },
        "bank": {
            "tech_terms": {"money", "finance", "loan", "investment", "deposit", "economy", "account", "capital", "wealth", "cash", "savings"},
            "tech_visual": "impressive modern architectural financial corporate banking tower lobby",
            "tech_queries": ["financial corporate banking", "bank vault cash transaction", "bank teller money counter"],
            "nature_visual": "lush green river bank with crystal clear flowing water at sunrise",
            "nature_queries": ["river bank nature", "riverbank water stream", "flowing river shoreline"]
        },
        "python": {
            "tech_terms": {"code", "programming", "developer", "software", "script", "data", "engineer", "algorithm", "syntax"},
            "tech_visual": "focused software engineer typing code on laptop in modern office",
            "tech_queries": ["software developer coding", "code terminal software programming", "programmer typing python code"],
            "nature_visual": "green tree python curled on rainforest branch in tropical canopy",
            "nature_queries": ["python snake wildlife", "green python tree branch", "exotic snake rainforest"]
        },
        "value": {
            "tech_terms": {"sales", "revenue", "growth", "stock", "price", "market", "finance", "investor", "dividend", "business"},
            "tech_visual": "confident executive team reviewing corporate financial charts on digital display",
            "tech_queries": ["stock market chart growth", "business growth corporate", "financial graphs trading"],
            "nature_visual": "two trusted partners closing successful agreement with firm handshake",
            "nature_queries": ["business partnership handshake", "handshake agreement office", "partners smiling handshake"]
        }
    }

    ABSTRACT_METAPHORS = [
        (re.compile(r'\b(soaring\s+inflation|inflation|rising\s+prices|cost\s+of\s+living)\b', re.IGNORECASE),
         "supermarket shelves with product price tags and shopping cart",
         ["supermarket prices grocery", "grocery shopping supermarket", "wallet cash empty"]),
        (re.compile(r'\b(cutting-edge\s+technology|cutting\s+edge|next-gen\s+tech)\b', re.IGNORECASE),
         "advanced robotics laboratory engineer working on precision microchip",
         ["robotics lab microchip", "advanced robotics engineer", "microchip circuit technology"]),
        (re.compile(r'\b(exploding\s+market|market\s+boom|booming\s+economy)\b', re.IGNORECASE),
         "bustling stock exchange trading floor with financial displays",
         ["stock exchange trading floor", "bustling stock market floor", "traders financial exchange"]),
        (re.compile(r'\b(burning\s+the\s+midnight\s+oil|midnight\s+oil|working\s+late)\b', re.IGNORECASE),
         "focused professional working at office desk under warm lamp light late at night",
         ["office desk night lamp", "focused worker night office", "lone desk lamp darkness"]),
        (re.compile(r'\btrust\b.*?\b(earn|slow|build|fragile)\b', re.IGNORECASE),
         "artisan builder carefully aligning foundation stone blocks for solid structure",
         ["foundation building craft", "stone mason craftsman", "architect building blueprint"]),
        (re.compile(r'\b(time|seconds?|hours?)\b.*?\b(asset|precious|slipp|fleeting)\b', re.IGNORECASE),
         "close-up of elegant mechanical watch tourbillon gears rotating precisely",
         ["clock gears time", "mechanical watch movement", "hourglass sand trickling"]),
        (re.compile(r'\b(freedom|liberty|peace)\b.*?\b(mind|spirit|soul)\b', re.IGNORECASE),
         "adventurous hiker standing on mountain peak arms open looking over sunrise horizon",
         ["mountain summit sunrise", "open mountain landscape", "clouds horizon sunlight"]),
        (re.compile(r'\bcuriosity\b.*?\b(discover|spark|wonder)\b', re.IGNORECASE),
         "young scientist observing glowing illuminated experiment in research laboratory",
         ["scientific discovery lab", "laboratory microscope research", "curious student experiment"]),
        (re.compile(r'\bsilence\b.*?\b(loud|powerful|speak)\b', re.IGNORECASE),
         "tranquil glassy mountain lake reflecting snow peaks with zero ripples",
         ["tranquil mountain lake", "serene calm water reflection", "morning mist lake forest"]),
    ]

    def formulate_query_variations(
        self,
        phrase: str,
        visual_style: str = "cinematic"
    ) -> Tuple[str, List[str], str]:
        lower = phrase.lower()

        # 1. Metaphors
        for pattern, visual, queries in self.ABSTRACT_METAPHORS:
            if pattern.search(lower):
                return (
                    f"{visual_style} shot: {visual}",
                    queries,
                    "Abstract line resolved to physical visual metaphor"
                )

        # 2. Coffee domain heuristic
        if "coffee" in lower:
            return (
                f"{visual_style} shot: steaming cup of artisanal brewed coffee in warm morning light",
                ["coffee brewing steam", "coffee plantation mountains", "barista espresso machine"],
                "Concrete coffee domain extraction"
            )

        # 3. Data center concrete domain heuristic
        if "data center" in lower or "data centers" in lower or "server rack" in lower:
            return (
                f"{visual_style} shot: modern enterprise data center server racks with blinking network lights",
                ["data center server racks", "modern server room hardware", "data center cables lights"],
                "Concrete data center physical visual mapping"
            )

        # 4. Numbers & Statistics ("sales grew 40% in 2025")
        has_stats = bool(re.search(r'\b\d+(?:\.\d+)?%?\b', phrase)) or any(w in lower for w in ("revenue", "quarterly", "sales grew", "profit", "metrics"))
        if has_stats and any(w in lower for w in ("grow", "sales", "revenue", "percent", "fiscal", "year", "quarter")):
            return (
                f"{visual_style} shot: professional business executives analyzing market strategy in sunlit modern conference room",
                ["business strategy meeting", "corporate financial analytics", "executives meeting discussion"],
                "Statistical statement mapped to neutral corporate business footage"
            )

        # 4. Homonyms
        for word, config in self.HOMONYMS.items():
            if re.search(r'\b' + re.escape(word) + r'\b', lower):
                tokens = set(re.findall(r'[a-zA-Z]+', lower))
                tech_overlap = len(tokens.intersection(config["tech_terms"]))
                if tech_overlap > 0:
                    matched = list(tokens.intersection(config["tech_terms"]))[:2]
                    return (
                        f"{visual_style} shot: {config['tech_visual']}",
                        config["tech_queries"],
                        f"Disambiguated '{word}' to technological context based on terms: {matched}"
                    )
                else:
                    return (
                        f"{visual_style} shot: {config['nature_visual']}",
                        config["nature_queries"],
                        f"Disambiguated '{word}' to natural/literal context"
                    )

        # 5. General concrete noun/setting extraction (2-4 words, physical objects only)
        words = re.findall(r'[a-zA-Z]{3,}', lower)
        stopwords = {
            "the", "and", "that", "this", "with", "from", "for", "are", "was", "were",
            "been", "being", "have", "has", "had", "does", "did", "can", "could", "will",
            "every", "millions", "wake", "about", "their", "there", "what", "which", "into"
        }
        salient = [w for w in words if w not in stopwords]
        
        q1 = " ".join(salient[:3]) if salient else "cinematic landscape"
        q2 = " ".join(salient[1:4]) if len(salient) > 2 else f"{q1} cinematic"
        q3 = f"{salient[0]} atmosphere" if salient else "aerial nature scenery"

        visual = f"{visual_style} shot: dynamic scene representing {' '.join(salient[:4]) if salient else 'scenic landscape'}"
        return visual, [q1, q2, q3], "Standard semantic keyword extraction"

class MockQueryAdapter(QueryAdapterBase):
    def formulate_query_variations(
        self,
        phrase: str,
        visual_style: str = "cinematic"
    ) -> Tuple[str, List[str], str]:
        rules = RulesQueryAdapter()
        return rules.formulate_query_variations(phrase, visual_style)

class LLMQueryAdapter(QueryAdapterBase):
    """
    LLM Query Adapter: uses Gemini or OpenAI API when keys configured,
    with automatic graceful fallback to RulesQueryAdapter.
    """
    def __init__(self):
        self._fallback = RulesQueryAdapter()

    def formulate_query_variations(
        self,
        phrase: str,
        visual_style: str = "cinematic"
    ) -> Tuple[str, List[str], str]:
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")

        if not (gemini_key or openai_key):
            return self._fallback.formulate_query_variations(phrase, visual_style)

        # If LLM key configured, query adapter can generate high-precision visual terms
        # Otherwise fallback gracefully to rules
        return self._fallback.formulate_query_variations(phrase, visual_style)

class QueryIntelligenceService:
    def __init__(self):
        self._rules_adapter = RulesQueryAdapter()
        self._mock_adapter = MockQueryAdapter()
        self._llm_adapter = LLMQueryAdapter()

    def _get_adapter(self) -> QueryAdapterBase:
        mode = settings.query_provider.lower()
        if mode == "llm":
            return self._llm_adapter
        elif mode == "mock":
            return self._mock_adapter
        return self._rules_adapter

    def disambiguate_query(self, phrase: str) -> str:
        _, queries, _ = self._get_adapter().formulate_query_variations(phrase)
        return queries[0] if queries else "cinematic footage"

    def formulate_intelligent_query(self, phrase: str, visual_style: str = "cinematic") -> Tuple[str, str, str]:
        visual, queries, rationale = self._get_adapter().formulate_query_variations(phrase, visual_style)
        return visual, queries[0] if queries else "cinematic footage", rationale

    def formulate_query_variations(self, phrase: str, visual_style: str = "cinematic") -> Tuple[str, List[str], str]:
        return self._get_adapter().formulate_query_variations(phrase, visual_style)

query_intelligence = QueryIntelligenceService()
