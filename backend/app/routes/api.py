from flask import Blueprint, request, jsonify, g
from functools import wraps
from sqlalchemy.orm import Session
import jwt as pyjwt
import bcrypt
from datetime import datetime, timedelta

from app.models.database import SessionLocal, User, TraitScore
from app.services.trait_service import TraitService
from app.core.config import config

api = Blueprint("api", __name__, url_prefix="/api/v1")


def get_db() -> Session:
    return SessionLocal()


# ── JWT Auth ──────────────────────────────────────────────────────────────────
def generate_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role":    role,
        "exp":     datetime.utcnow() + timedelta(seconds=config.JWT_EXPIRY),
    }
    return pyjwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "No token"}), 401
        try:
            payload   = pyjwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
            g.user_id = payload["user_id"]
            g.role    = payload["role"]
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def require_manager(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.role not in ["manager", "admin"]:
            return jsonify({"error": "Manager access required"}), 403
        return f(*args, **kwargs)
    return decorated


# ── Health ────────────────────────────────────────────────────────────────────
@api.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Traitlytics API"})


# ── Auth ──────────────────────────────────────────────────────────────────────
@api.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email     = data.get("email", "").strip().lower()
    password  = data.get("password", "")
    full_name = data.get("fullName", "").strip()
    role      = data.get("role", "individual")
    department= data.get("department", "")

    if not email or not password or not full_name:
        return jsonify({"error": "email, password, fullName required"}), 400

    db = get_db()
    try:
        if db.query(User).filter(User.email == email).first():
            return jsonify({"error": "Email already registered"}), 409

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user    = User(email=email, password_hash=pw_hash, full_name=full_name, role=role, department=department)
        db.add(user)
        db.commit()
        db.refresh(user)

        token = generate_token(user.id, user.role)
        return jsonify({
            "user":  {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
            "token": token,
        }), 201
    finally:
        db.close()


@api.route("/auth/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return jsonify({"error": "Invalid credentials"}), 401

        token = generate_token(user.id, user.role)
        return jsonify({
            "user":  {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
            "token": token,
        })
    finally:
        db.close()


# ── Assessment ────────────────────────────────────────────────────────────────
@api.route("/assessment/questions")
def get_questions():
    return jsonify(TraitService.get_questions())


@api.route("/assessment/submit", methods=["POST"])
@require_auth
def submit_assessment():
    data      = request.get_json() or {}
    responses = data.get("responses", {})

    if not responses:
        return jsonify({"error": "responses required"}), 400

    # Convert string keys to int
    responses = {int(k): v for k, v in responses.items()}

    db = get_db()
    try:
        result = TraitService.submit_assessment(db, g.user_id, responses)
        return jsonify(result), 201
    finally:
        db.close()


# ── Profile ───────────────────────────────────────────────────────────────────
@api.route("/profile")
@require_auth
def get_profile():
    db = get_db()
    try:
        profile = TraitService.get_user_profile(db, g.user_id)
        if not profile:
            return jsonify({"error": "No assessment found. Please take the assessment first."}), 404
        return jsonify(profile)
    finally:
        db.close()


@api.route("/profile/history")
@require_auth
def get_history():
    db = get_db()
    try:
        return jsonify(TraitService.get_trait_history(db, g.user_id))
    finally:
        db.close()


# ── Analytics ─────────────────────────────────────────────────────────────────
@api.route("/analytics/population")
@require_auth
def population_stats():
    db = get_db()
    try:
        return jsonify(TraitService.get_population_distribution(db))
    finally:
        db.close()


@api.route("/analytics/dominant-traits")
@require_auth
def dominant_traits():
    db = get_db()
    try:
        return jsonify(TraitService.get_dominant_trait_distribution(db))
    finally:
        db.close()


@api.route("/analytics/cohort")
@require_auth
@require_manager
def cohort_analysis():
    department = request.args.get("department", "")
    if not department:
        return jsonify({"error": "department required"}), 400
    db = get_db()
    try:
        return jsonify(TraitService.get_cohort_comparison(db, department))
    finally:
        db.close()


# ── Demo seed ─────────────────────────────────────────────────────────────────
@api.route("/demo/seed", methods=["POST"])
@require_auth
def seed_demo():
    """Seed historical data for demo purposes."""
    db = get_db()
    try:
        TraitService.seed_demo_data(db, g.user_id, count=5)
        return jsonify({"message": "Demo data seeded successfully"})
    finally:
        db.close()


@api.route("/profile/export/pdf")
@require_auth
def export_pdf():
    from flask import send_file
    from app.services.pdf_service import generate_pdf_report
    from app.models.database import User as UserModel
    import io

    db = get_db()
    try:
        profile = TraitService.get_user_profile(db, g.user_id)
        if not profile:
            return jsonify({"error": "No profile found"}), 404

        user      = db.query(UserModel).filter_by(id=g.user_id).first()
        user_name = user.full_name if user else "User"
        pdf_bytes = generate_pdf_report(profile, user_name)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"traitlytics_report.pdf"
        )
    finally:
        db.close()