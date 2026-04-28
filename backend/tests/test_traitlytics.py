"""
Traitlytics Backend Tests — 32 tests
Run: pytest tests/ -v
"""

import pytest
import json
from unittest.mock import patch
from app.ml.big_five import BigFivePipeline, QUESTIONS


def make_responses(value: int = 3) -> dict:
    return {q["id"]: value for q in QUESTIONS}


def make_varied_responses() -> dict:
    import random
    random.seed(42)
    return {q["id"]: random.randint(1, 5) for q in QUESTIONS}


class TestBigFivePipeline:

    @pytest.fixture
    def pipeline(self):
        return BigFivePipeline()

    def test_pipeline_initializes(self, pipeline):
        assert pipeline is not None
        assert pipeline._population_stats is not None

    def test_all_five_traits_in_output(self, pipeline):
        profile = pipeline.predict(make_varied_responses())
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            assert hasattr(profile, trait)

    def test_scores_in_valid_range(self, pipeline):
        profile = pipeline.predict(make_varied_responses())
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            assert 0 <= getattr(profile, trait) <= 100

    def test_percentiles_in_valid_range(self, pipeline):
        profile = pipeline.predict(make_varied_responses())
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            assert 1 <= getattr(profile, f"{trait}_pct") <= 99

    def test_dominant_trait_is_valid(self, pipeline):
        profile = pipeline.predict(make_varied_responses())
        assert profile.dominant_trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

    def test_dominant_trait_is_highest_score(self, pipeline):
        profile = pipeline.predict(make_varied_responses())
        scores  = {t: getattr(profile, t) for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}
        assert scores[profile.dominant_trait] == max(scores.values())

    def test_descriptions_generated(self, pipeline):
        profile = pipeline.predict(make_varied_responses())
        assert isinstance(profile.descriptions, dict)
        assert len(profile.descriptions) == 5

    def test_profile_has_is_valid_flag(self, pipeline):
        profile = pipeline.predict(make_varied_responses())
        assert isinstance(profile.is_valid, bool)


class TestResponseValidation:

    @pytest.fixture
    def pipeline(self):
        return BigFivePipeline()

    def test_valid_responses_pass(self, pipeline):
        assert pipeline._validate_responses(make_varied_responses()) is True

    def test_all_same_responses_fail(self, pipeline):
        assert pipeline._validate_responses(make_responses(3)) is False

    def test_incomplete_responses_fail(self, pipeline):
        assert pipeline._validate_responses({i: 3 for i in range(1, 30)}) is False

    def test_out_of_range_responses_fail(self, pipeline):
        r = make_varied_responses(); r[1] = 6
        assert pipeline._validate_responses(r) is False

    def test_zero_value_responses_fail(self, pipeline):
        r = make_varied_responses(); r[1] = 0
        assert pipeline._validate_responses(r) is False


class TestReverseScoring:

    @pytest.fixture
    def pipeline(self):
        return BigFivePipeline()

    def test_high_responses_give_high_scores(self, pipeline):
        responses = {q["id"]: (5 if not q["reverse"] else 1) for q in QUESTIONS}
        profile   = pipeline.predict(responses)
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            assert getattr(profile, trait) > 50

    def test_low_responses_give_low_scores(self, pipeline):
        responses = {q["id"]: (1 if not q["reverse"] else 5) for q in QUESTIONS}
        profile   = pipeline.predict(responses)
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            assert getattr(profile, trait) < 50

    def test_reverse_scored_items_flip_correctly(self, pipeline):
        raw = pipeline._compute_raw_scores(
            {q["id"]: (5 if not q["reverse"] else 1) for q in QUESTIONS}
        )
        for trait in raw:
            assert raw[trait] > 50


class TestPercentileComputation:

    @pytest.fixture
    def pipeline(self):
        return BigFivePipeline()

    def test_average_score_near_50th_percentile(self, pipeline):
        avg_scores  = {t: pipeline._population_stats[t]["mean"] for t in pipeline._population_stats}
        percentiles = pipeline._compute_percentiles(avg_scores)
        for trait in pipeline._population_stats:
            assert 40 <= percentiles[f"{trait}_pct"] <= 60

    def test_high_score_gives_high_percentile(self, pipeline):
        scores      = {t: 90.0 for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}
        percentiles = pipeline._compute_percentiles(scores)
        for trait in scores:
            assert percentiles[f"{trait}_pct"] > 70

    def test_low_score_gives_low_percentile(self, pipeline):
        scores      = {t: 20.0 for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}
        percentiles = pipeline._compute_percentiles(scores)
        for trait in scores:
            assert percentiles[f"{trait}_pct"] < 30

    def test_percentiles_bounded_1_to_99(self, pipeline):
        scores      = {t: 0.0 for t in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}
        percentiles = pipeline._compute_percentiles(scores)
        for trait in scores:
            assert 1 <= percentiles[f"{trait}_pct"] <= 99


class TestDriftDetection:

    @pytest.fixture
    def pipeline(self):
        return BigFivePipeline()

    def test_stable_scores_return_stable(self, pipeline):
        scores = [
            {"openness": 60, "conscientiousness": 55, "extraversion": 50, "agreeableness": 65, "neuroticism": 45},
            {"openness": 62, "conscientiousness": 56, "extraversion": 51, "agreeableness": 64, "neuroticism": 46},
        ]
        assert pipeline.detect_trait_drift(scores)["openness"] == "stable"

    def test_increasing_scores_detected(self, pipeline):
        scores = [
            {"openness": 40, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
            {"openness": 70, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
        ]
        assert pipeline.detect_trait_drift(scores)["openness"] == "increasing"

    def test_decreasing_scores_detected(self, pipeline):
        scores = [
            {"openness": 70, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
            {"openness": 40, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
        ]
        assert pipeline.detect_trait_drift(scores)["openness"] == "decreasing"

    def test_single_score_returns_stable(self, pipeline):
        scores = [{"openness": 60, "conscientiousness": 55, "extraversion": 50, "agreeableness": 65, "neuroticism": 45}]
        assert all(v == "stable" for v in pipeline.detect_trait_drift(scores).values())

    def test_empty_scores_returns_stable(self, pipeline):
        assert all(v == "stable" for v in pipeline.detect_trait_drift([]).values())


class TestAPIEndpoints:

    @pytest.fixture
    def client(self):
        from app.main import app
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_health_endpoint(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert json.loads(r.data)["status"] == "ok"

    def test_get_questions_returns_50(self, client):
        r = client.get("/api/v1/assessment/questions")
        assert r.status_code == 200
        assert len(json.loads(r.data)) == 50

    def test_questions_have_id_and_text(self, client):
        r    = client.get("/api/v1/assessment/questions")
        data = json.loads(r.data)
        for q in data:
            assert "id" in q and "text" in q
            assert "trait" not in q

    def test_submit_assessment_requires_auth(self, client):
        assert client.post("/api/v1/assessment/submit", json={"responses": {}}).status_code == 401

    def test_profile_requires_auth(self, client):
        assert client.get("/api/v1/profile").status_code == 401

    def test_cohort_requires_manager_role(self, client):
        with patch("app.routes.api.pyjwt.decode") as mock:
            mock.return_value = {"user_id": 1, "role": "individual", "exp": 9999999999}
            r = client.get("/api/v1/analytics/cohort?department=Engineering",
                           headers={"Authorization": "Bearer faketoken"})
            assert r.status_code == 403

    def test_register_missing_fields(self, client):
        assert client.post("/api/v1/auth/register", json={"email": "test@test.com"}).status_code == 400