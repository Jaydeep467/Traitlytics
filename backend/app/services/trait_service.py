import logging
import random
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.database import User, Assessment, TraitScore
from app.ml.big_five import get_pipeline, QUESTIONS, TraitProfile

logger = logging.getLogger(__name__)
TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


class TraitService:

    @staticmethod
    def get_questions():
        return [{"id": q["id"], "text": q["text"]} for q in QUESTIONS]

    @staticmethod
    def submit_assessment(db: Session, user_id: int, responses: dict) -> dict:
        pipeline = get_pipeline()
        profile  = pipeline.predict(responses)

        assessment = Assessment(user_id=user_id, responses={str(k): v for k, v in responses.items()})
        db.add(assessment)
        db.flush()

        score = TraitScore(
            user_id=user_id, assessment_id=assessment.id,
            openness=profile.openness, conscientiousness=profile.conscientiousness,
            extraversion=profile.extraversion, agreeableness=profile.agreeableness,
            neuroticism=profile.neuroticism, openness_pct=profile.openness_pct,
            conscientiousness_pct=profile.conscientiousness_pct, extraversion_pct=profile.extraversion_pct,
            agreeableness_pct=profile.agreeableness_pct, neuroticism_pct=profile.neuroticism_pct,
            dominant_trait=profile.dominant_trait,
        )
        db.add(score)
        db.commit()
        return TraitService._profile_to_dict(profile, score.id, assessment.id)

    @staticmethod
    def get_user_profile(db: Session, user_id: int):
        score = db.query(TraitScore).filter(TraitScore.user_id == user_id).order_by(desc(TraitScore.created_at)).first()
        if not score:
            return None
        return {
            "id": score.id, "openness": score.openness, "conscientiousness": score.conscientiousness,
            "extraversion": score.extraversion, "agreeableness": score.agreeableness, "neuroticism": score.neuroticism,
            "openness_pct": score.openness_pct, "conscientiousness_pct": score.conscientiousness_pct,
            "extraversion_pct": score.extraversion_pct, "agreeableness_pct": score.agreeableness_pct,
            "neuroticism_pct": score.neuroticism_pct, "dominant_trait": score.dominant_trait,
            "created_at": score.created_at.isoformat(),
        }

    @staticmethod
    def get_trait_history(db: Session, user_id: int):
        scores = db.query(TraitScore).filter(TraitScore.user_id == user_id).order_by(TraitScore.created_at).all()
        history = [{"date": s.created_at.isoformat(), "openness": s.openness, "conscientiousness": s.conscientiousness,
                    "extraversion": s.extraversion, "agreeableness": s.agreeableness, "neuroticism": s.neuroticism}
                   for s in scores]
        pipeline = get_pipeline()
        drift    = pipeline.detect_trait_drift(history)
        return {"history": history, "drift": drift}

    @staticmethod
    def get_population_distribution(db: Session):
        result = db.query(
            func.avg(TraitScore.openness).label("avg_openness"),
            func.avg(TraitScore.conscientiousness).label("avg_conscientiousness"),
            func.avg(TraitScore.extraversion).label("avg_extraversion"),
            func.avg(TraitScore.agreeableness).label("avg_agreeableness"),
            func.avg(TraitScore.neuroticism).label("avg_neuroticism"),
            func.count(TraitScore.id).label("total"),
        ).first()
        return {
            "total_profiles": result.total or 0,
            "averages": {
                "openness": round(result.avg_openness or 0, 1),
                "conscientiousness": round(result.avg_conscientiousness or 0, 1),
                "extraversion": round(result.avg_extraversion or 0, 1),
                "agreeableness": round(result.avg_agreeableness or 0, 1),
                "neuroticism": round(result.avg_neuroticism or 0, 1),
            },
        }

    @staticmethod
    def get_dominant_trait_distribution(db: Session):
        results = db.query(TraitScore.dominant_trait, func.count(TraitScore.id).label("count")).group_by(TraitScore.dominant_trait).all()
        return [{"trait": r.dominant_trait, "count": r.count} for r in results]

    @staticmethod
    def get_cohort_comparison(db: Session, department: str):
        dept_users  = db.query(User.id).filter(User.department == department).subquery()
        dept_scores = db.query(
            func.avg(TraitScore.openness).label("openness"),
            func.avg(TraitScore.conscientiousness).label("conscientiousness"),
            func.avg(TraitScore.extraversion).label("extraversion"),
            func.avg(TraitScore.agreeableness).label("agreeableness"),
            func.avg(TraitScore.neuroticism).label("neuroticism"),
        ).filter(TraitScore.user_id.in_(dept_users)).first()
        return {
            "department": department,
            "scores": {
                "openness": round(dept_scores.openness or 0, 1),
                "conscientiousness": round(dept_scores.conscientiousness or 0, 1),
                "extraversion": round(dept_scores.extraversion or 0, 1),
                "agreeableness": round(dept_scores.agreeableness or 0, 1),
                "neuroticism": round(dept_scores.neuroticism or 0, 1),
            }
        }

    @staticmethod
    def seed_demo_data(db: Session, user_id: int, count: int = 5):
        pipeline = get_pipeline()
        for i in range(count):
            responses = {}
            for q in QUESTIONS:
                base  = random.randint(2, 4)
                score = max(1, min(5, base + random.randint(-1, 1)))
                responses[q["id"]] = score
            profile    = pipeline.predict(responses)
            assessment = Assessment(user_id=user_id, responses={str(k): v for k, v in responses.items()})
            db.add(assessment)
            db.flush()
            score_obj = TraitScore(
                user_id=user_id, assessment_id=assessment.id,
                openness=profile.openness, conscientiousness=profile.conscientiousness,
                extraversion=profile.extraversion, agreeableness=profile.agreeableness,
                neuroticism=profile.neuroticism, openness_pct=profile.openness_pct,
                conscientiousness_pct=profile.conscientiousness_pct, extraversion_pct=profile.extraversion_pct,
                agreeableness_pct=profile.agreeableness_pct, neuroticism_pct=profile.neuroticism_pct,
                dominant_trait=profile.dominant_trait,
            )
            db.add(score_obj)
        db.commit()

    @staticmethod
    def _profile_to_dict(profile, score_id, assessment_id):
        return {
            "score_id": score_id, "assessment_id": assessment_id,
            "openness": profile.openness, "conscientiousness": profile.conscientiousness,
            "extraversion": profile.extraversion, "agreeableness": profile.agreeableness,
            "neuroticism": profile.neuroticism, "openness_pct": profile.openness_pct,
            "conscientiousness_pct": profile.conscientiousness_pct, "extraversion_pct": profile.extraversion_pct,
            "agreeableness_pct": profile.agreeableness_pct, "neuroticism_pct": profile.neuroticism_pct,
            "dominant_trait": profile.dominant_trait, "descriptions": profile.descriptions,
            "is_valid": profile.is_valid,
        }