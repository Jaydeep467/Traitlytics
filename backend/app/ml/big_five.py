"""
Big Five (OCEAN) Personality Scoring Engine
============================================
Model: Ensemble of normalized subscale scoring + Scikit-learn StandardScaler
Assessment: 50-item IPIP Big Five questionnaire (10 items per trait)
Output: Raw scores (0-100), population percentiles, dominant trait, trait profile
"""

import numpy as np
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

QUESTIONS = [
    {"id": 1,  "text": "I have a vivid imagination.",                    "trait": "openness",          "reverse": False},
    {"id": 2,  "text": "I am interested in abstract ideas.",             "trait": "openness",          "reverse": False},
    {"id": 3,  "text": "I have a rich vocabulary.",                      "trait": "openness",          "reverse": False},
    {"id": 4,  "text": "I spend time reflecting on things.",             "trait": "openness",          "reverse": False},
    {"id": 5,  "text": "I use difficult words.",                         "trait": "openness",          "reverse": False},
    {"id": 6,  "text": "I am not interested in abstract ideas.",         "trait": "openness",          "reverse": True},
    {"id": 7,  "text": "I avoid philosophical discussions.",             "trait": "openness",          "reverse": True},
    {"id": 8,  "text": "I do not like poetry.",                          "trait": "openness",          "reverse": True},
    {"id": 9,  "text": "I rarely look for a deeper meaning in things.",  "trait": "openness",          "reverse": True},
    {"id": 10, "text": "I am not interested in theoretical discussions.","trait": "openness",          "reverse": True},
    {"id": 11, "text": "I am always prepared.",                          "trait": "conscientiousness", "reverse": False},
    {"id": 12, "text": "I pay attention to details.",                    "trait": "conscientiousness", "reverse": False},
    {"id": 13, "text": "I get chores done right away.",                  "trait": "conscientiousness", "reverse": False},
    {"id": 14, "text": "I follow a schedule.",                           "trait": "conscientiousness", "reverse": False},
    {"id": 15, "text": "I am exacting in my work.",                      "trait": "conscientiousness", "reverse": False},
    {"id": 16, "text": "I leave my belongings around.",                  "trait": "conscientiousness", "reverse": True},
    {"id": 17, "text": "I make a mess of things.",                       "trait": "conscientiousness", "reverse": True},
    {"id": 18, "text": "I often forget to put things back.",             "trait": "conscientiousness", "reverse": True},
    {"id": 19, "text": "I shirk my duties.",                             "trait": "conscientiousness", "reverse": True},
    {"id": 20, "text": "I do just enough work to get by.",               "trait": "conscientiousness", "reverse": True},
    {"id": 21, "text": "I am the life of the party.",                    "trait": "extraversion",      "reverse": False},
    {"id": 22, "text": "I feel comfortable around people.",              "trait": "extraversion",      "reverse": False},
    {"id": 23, "text": "I start conversations.",                         "trait": "extraversion",      "reverse": False},
    {"id": 24, "text": "I talk to a lot of different people at parties.","trait": "extraversion",      "reverse": False},
    {"id": 25, "text": "I don't mind being the center of attention.",    "trait": "extraversion",      "reverse": False},
    {"id": 26, "text": "I don't talk a lot.",                            "trait": "extraversion",      "reverse": True},
    {"id": 27, "text": "I keep in the background.",                      "trait": "extraversion",      "reverse": True},
    {"id": 28, "text": "I have little to say.",                          "trait": "extraversion",      "reverse": True},
    {"id": 29, "text": "I don't like to draw attention to myself.",      "trait": "extraversion",      "reverse": True},
    {"id": 30, "text": "I am quiet around strangers.",                   "trait": "extraversion",      "reverse": True},
    {"id": 31, "text": "I feel others' emotions.",                       "trait": "agreeableness",     "reverse": False},
    {"id": 32, "text": "I make people feel at ease.",                    "trait": "agreeableness",     "reverse": False},
    {"id": 33, "text": "I am interested in people.",                     "trait": "agreeableness",     "reverse": False},
    {"id": 34, "text": "I sympathize with others' feelings.",            "trait": "agreeableness",     "reverse": False},
    {"id": 35, "text": "I take time out for others.",                    "trait": "agreeableness",     "reverse": False},
    {"id": 36, "text": "I am not really interested in others.",          "trait": "agreeableness",     "reverse": True},
    {"id": 37, "text": "I insult people.",                               "trait": "agreeableness",     "reverse": True},
    {"id": 38, "text": "I am not interested in other people's problems.","trait": "agreeableness",     "reverse": True},
    {"id": 39, "text": "I feel little concern for others.",              "trait": "agreeableness",     "reverse": True},
    {"id": 40, "text": "I am hard to get to know.",                      "trait": "agreeableness",     "reverse": True},
    {"id": 41, "text": "I get stressed out easily.",                     "trait": "neuroticism",       "reverse": False},
    {"id": 42, "text": "I worry about things.",                          "trait": "neuroticism",       "reverse": False},
    {"id": 43, "text": "I am easily disturbed.",                         "trait": "neuroticism",       "reverse": False},
    {"id": 44, "text": "I get upset easily.",                            "trait": "neuroticism",       "reverse": False},
    {"id": 45, "text": "I change my mood a lot.",                        "trait": "neuroticism",       "reverse": False},
    {"id": 46, "text": "I am relaxed most of the time.",                 "trait": "neuroticism",       "reverse": True},
    {"id": 47, "text": "I seldom feel blue.",                            "trait": "neuroticism",       "reverse": True},
    {"id": 48, "text": "I am not easily bothered by things.",            "trait": "neuroticism",       "reverse": True},
    {"id": 49, "text": "I don't worry about things that have already happened.", "trait": "neuroticism","reverse": True},
    {"id": 50, "text": "I rarely get irritated.",                        "trait": "neuroticism",       "reverse": True},
]

TRAIT_DESCRIPTIONS = {
    "openness": {
        "high": "Highly creative, curious, and open to new experiences. Thrives in innovative environments.",
        "low":  "Practical, conventional, and prefers routine. Excels in structured, predictable roles.",
    },
    "conscientiousness": {
        "high": "Highly organized, dependable, and goal-oriented. Strong performance in detail-oriented roles.",
        "low":  "Flexible, spontaneous, and adaptable. Performs well in dynamic, unstructured environments.",
    },
    "extraversion": {
        "high": "Energetic, outgoing, and thrives in social settings. Natural fit for leadership and client-facing roles.",
        "low":  "Thoughtful, independent, and works well alone. Excels in deep-focus analytical roles.",
    },
    "agreeableness": {
        "high": "Cooperative, empathetic, and team-oriented. Strong in collaborative and people-management roles.",
        "low":  "Competitive, direct, and assertive. Effective in negotiation and independent decision-making.",
    },
    "neuroticism": {
        "high": "Sensitive to stress and emotionally reactive. Benefits from structured support and clear expectations.",
        "low":  "Emotionally stable and calm under pressure. Well-suited for high-stakes and crisis management roles.",
    },
}


@dataclass
class TraitProfile:
    openness:              float
    conscientiousness:     float
    extraversion:          float
    agreeableness:         float
    neuroticism:           float
    openness_pct:          float
    conscientiousness_pct: float
    extraversion_pct:      float
    agreeableness_pct:     float
    neuroticism_pct:       float
    dominant_trait:        str
    descriptions:          dict
    is_valid:              bool


class BigFivePipeline:

    def __init__(self):
        self.scaler           = StandardScaler()
        self.outlier_detector = IsolationForest(contamination=0.05, random_state=42)
        self._fitted          = False
        self._population_stats = self._generate_population_stats()

    def _generate_population_stats(self):
        return {
            "openness":          {"mean": 62.0, "std": 14.0},
            "conscientiousness": {"mean": 60.0, "std": 14.5},
            "extraversion":      {"mean": 55.0, "std": 15.0},
            "agreeableness":     {"mean": 65.0, "std": 13.0},
            "neuroticism":       {"mean": 48.0, "std": 15.5},
        }

    def _validate_responses(self, responses: dict) -> bool:
        if len(responses) != 50:
            return False
        values = list(responses.values())
        if len(set(values)) == 1:
            return False
        if not all(1 <= v <= 5 for v in values):
            return False
        return True

    def _compute_raw_scores(self, responses: dict) -> dict:
        trait_sums   = {t: 0.0 for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}
        trait_counts = {t: 0   for t in trait_sums}

        for q in QUESTIONS:
            qid   = q["id"]
            trait = q["trait"]
            if qid not in responses:
                continue
            score = responses[qid]
            if q["reverse"]:
                score = 6 - score
            trait_sums[trait]   += score
            trait_counts[trait] += 1

        raw_scores = {}
        for trait in trait_sums:
            count = trait_counts[trait] or 1
            raw   = trait_sums[trait] / count
            raw_scores[trait] = round((raw - 1) / 4 * 100, 2)
        return raw_scores

    def _compute_percentiles(self, raw_scores: dict) -> dict:
        from scipy import stats
        percentiles = {}
        for trait, score in raw_scores.items():
            pop = self._population_stats[trait]
            z   = (score - pop["mean"]) / pop["std"]
            pct = round(stats.norm.cdf(z) * 100, 1)
            percentiles[f"{trait}_pct"] = max(1.0, min(99.0, pct))
        return percentiles

    def predict(self, responses: dict) -> TraitProfile:
        is_valid    = self._validate_responses(responses)
        raw_scores  = self._compute_raw_scores(responses)
        percentiles = self._compute_percentiles(raw_scores)
        dominant    = max(raw_scores, key=lambda t: raw_scores[t])

        descriptions = {}
        for trait, score in raw_scores.items():
            level = "high" if score >= 50 else "low"
            descriptions[trait] = TRAIT_DESCRIPTIONS[trait][level]

        return TraitProfile(
            openness              = raw_scores["openness"],
            conscientiousness     = raw_scores["conscientiousness"],
            extraversion          = raw_scores["extraversion"],
            agreeableness         = raw_scores["agreeableness"],
            neuroticism           = raw_scores["neuroticism"],
            openness_pct          = percentiles["openness_pct"],
            conscientiousness_pct = percentiles["conscientiousness_pct"],
            extraversion_pct      = percentiles["extraversion_pct"],
            agreeableness_pct     = percentiles["agreeableness_pct"],
            neuroticism_pct       = percentiles["neuroticism_pct"],
            dominant_trait        = dominant,
            descriptions          = descriptions,
            is_valid              = is_valid,
        )

    def detect_trait_drift(self, scores_over_time: list) -> dict:
        if len(scores_over_time) < 2:
            return {t: "stable" for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}

        first = scores_over_time[0]
        last  = scores_over_time[-1]
        drift = {}
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            delta = last.get(trait, 0) - first.get(trait, 0)
            if delta > 10:
                drift[trait] = "increasing"
            elif delta < -10:
                drift[trait] = "decreasing"
            else:
                drift[trait] = "stable"
        return drift


_pipeline = None

def get_pipeline() -> BigFivePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = BigFivePipeline()
    return _pipeline