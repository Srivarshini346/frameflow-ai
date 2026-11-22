import re
from typing import Tuple, Dict, Any, List
from app.core.logger import logger

class QueryIntelligenceService:
    """
    Context-Aware Query Formulation & Meaning Disambiguation Engine:
    1. Disambiguates homonyms (mouse, cloud, bank, python, value) based on semantic sentence context.
    2. Translates abstract philosophical thoughts into concrete, filmed physical metaphors.
    3. Handles numbers & statistics by mapping to neutral business footage without invented on-screen text.
    """

    HOMONYMS = {
        "mouse": {
            "tech_terms": {"computer", "click", "screen", "laptop", "software", "desk", "pc", "cursor", "device", "work"},
            "tech_visual": "modern ergonomic computer mouse on clean office desk",
            "tech_query": "computer mouse desk",
            "nature_visual": "small wild field mouse in natural outdoor habitat",
            "nature_query": "field mouse nature"
        },
        "cloud": {
            "tech_terms": {"data", "server", "computing", "storage", "network", "backup", "software", "infrastructure", "digital"},
            "tech_visual": "modern enterprise server room with glowing blue LED network cables",
            "tech_query": "server room technology",
            "nature_visual": "fluffy white cumulus clouds drifting across vast bright blue sky",
            "nature_query": "clouds sky time-lapse"
        },
        "bank": {
            "tech_terms": {"money", "finance", "loan", "investment", "deposit", "economy", "account", "capital", "wealth"},
            "tech_visual": "impressive modern architectural financial corporate banking tower lobby",
            "tech_query": "financial corporate banking",
            "nature_visual": "lush green river bank with crystal clear flowing water at sunrise",
            "nature_query": "river bank nature"
        },
        "python": {
            "tech_terms": {"code", "programming", "developer", "software", "script", "data", "engineer", "algorithm", "syntax"},
            "tech_visual": "focused software engineer typing code on laptop in modern office",
            "tech_query": "software developer coding",
            "nature_visual": "green tree python curled on rainforest branch in tropical canopy",
            "nature_query": "python snake wildlife"
        },
        "value": {
            "tech_terms": {"sales", "revenue", "growth", "stock", "price", "market", "finance", "investor", "dividend"},
            "tech_visual": "confident executive team reviewing corporate financial charts on digital display",
            "tech_query": "business growth corporate",
            "nature_visual": "two trusted partners closing successful agreement with firm handshake",
            "nature_query": "business partnership handshake"
        }
    }

    ABSTRACT_METAPHORS = [
        (re.compile(r'\btrust\b.*?\b(earn|slow|build|fragile)\b', re.IGNORECASE), "artisan builder carefully aligning foundation stone blocks for solid structure", "foundation building craft"),
        (re.compile(r'\b(time|seconds?|hours?)\b.*?\b(asset|precious|slipp|fleeting)\b', re.IGNORECASE), "close-up of elegant mechanical watch tourbillon gears rotating precisely", "clock gears time"),
        (re.compile(r'\b(freedom|liberty|peace)\b.*?\b(mind|spirit|soul)\b', re.IGNORECASE), "adventurous hiker standing on mountain peak arms open looking over sunrise horizon", "mountain summit sunrise"),
        (re.compile(r'\bcuriosity\b.*?\b(discover|spark|wonder)\b', re.IGNORECASE), "young scientist observing glowing illuminated experiment in research laboratory", "scientific discovery lab"),
        (re.compile(r'\bsilence\b.*?\b(loud|powerful|speak)\b', re.IGNORECASE), "tranquil glassy mountain lake reflecting snow peaks with zero ripples", "tranquil mountain lake"),
    ]

    def disambiguate_query(self, phrase: str) -> str:
        """
        Disambiguates homonyms, abstract metaphors, and numbers, returning the clean search query.
        """
        _, query, _ = self.formulate_intelligent_query(phrase)
        return query

    def formulate_intelligent_query(self, phrase: str, visual_style: str = "cinematic") -> Tuple[str, str, str]:
        """
        Takes raw narration phrase and outputs:
        (concrete_visual_intent, primary_query, disambiguation_rationale)
        """
        lower = phrase.lower()

        # 1. Check for abstract metaphorical expressions
        for pattern, visual, query in self.ABSTRACT_METAPHORS:
            if pattern.search(lower):
                return (
                    f"{visual_style} shot: {visual}",
                    query,
                    "Abstract line resolved to physical visual metaphor"
                )

        # 2. Check for numbers and statistical statements ("sales grew 40% in 2025")
        has_stats = bool(re.search(r'\b\d+(?:\.\d+)?%?\b', phrase)) or any(w in lower for w in ("revenue", "quarterly", "sales grew", "profit", "metrics"))
        if has_stats and any(w in lower for w in ("grow", "sales", "revenue", "percent", "fiscal", "year", "quarter")):
            return (
                f"{visual_style} shot: professional business executives analyzing market strategy in sunlit modern conference room (neutral footage, no invented numbers)",
                "business strategy meeting",
                "Statistical statement mapped to neutral corporate business footage"
            )

        # 3. Check for double-meaning homonyms
        for word, config in self.HOMONYMS.items():
            if re.search(r'\b' + re.escape(word) + r'\b', lower):
                # Count context terms
                tokens = set(re.findall(r'[a-zA-Z]+', lower))
                tech_overlap = len(tokens.intersection(config["tech_terms"]))
                if tech_overlap > 0:
                    return (
                        f"{visual_style} shot: {config['tech_visual']}",
                        config["tech_query"],
                        f"Disambiguated '{word}' to technological context based on terms: {list(tokens.intersection(config['tech_terms']))[:2]}"
                    )
                else:
                    return (
                        f"{visual_style} shot: {config['nature_visual']}",
                        config["nature_query"],
                        f"Disambiguated '{word}' to natural/literal context"
                    )

        # 4. Standard semantic conversion
        # Extract salient action and subject words
        words = re.findall(r'[a-zA-Z]{3,}', lower)
        stopwords = {
            "the", "and", "that", "this", "with", "from", "for", "are", "was", "were",
            "been", "being", "have", "has", "had", "does", "did", "can", "could", "will"
        }
        salient = [w for w in words if w not in stopwords]
        query = " ".join(salient[:3]) if salient else "cinematic atmosphere"
        visual = f"{visual_style} shot: dynamic scene representing {' '.join(salient[:4]) if salient else 'scenic landscape'}"

        return visual, query, "Standard semantic keyword extraction"

query_intelligence = QueryIntelligenceService()
