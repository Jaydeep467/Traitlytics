"""
Traitlytics Demo Seeder
=======================
Seeds 200 realistic Indian user profiles with varied personality assessments.
Run: python seed_demo.py
"""

import sys
import os
import random
import bcrypt
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import SessionLocal, create_tables, User, Assessment, TraitScore
from app.ml.big_five import get_pipeline, QUESTIONS

# ── Indian Names Dataset ──────────────────────────────────────────────────────
FIRST_NAMES_MALE = [
    "Aarav", "Arjun", "Vivek", "Rohit", "Karan", "Aditya", "Rajesh", "Suresh",
    "Manish", "Vikram", "Amit", "Nikhil", "Sanjay", "Ravi", "Deepak", "Ankur",
    "Prateek", "Varun", "Shivam", "Hardik", "Yash", "Parth", "Dev", "Harsh",
    "Akash", "Tushar", "Gaurav", "Neeraj", "Rahul", "Kunal", "Ishaan", "Kabir",
    "Pranav", "Siddharth", "Ankit", "Mohit", "Tarun", "Vishal", "Rohan", "Ayaan",
    "Dhruv", "Kartik", "Rishabh", "Lakshay", "Abhinav", "Chirag", "Nihal", "Omkar",
]

FIRST_NAMES_FEMALE = [
    "Priya", "Ananya", "Sneha", "Pooja", "Divya", "Neha", "Riya", "Kavya",
    "Sakshi", "Shreya", "Meera", "Isha", "Nisha", "Tanvi", "Swati", "Ankita",
    "Kritika", "Aishwarya", "Pallavi", "Simran", "Komal", "Juhi", "Aditi", "Nidhi",
    "Deepika", "Sunita", "Rekha", "Geeta", "Sonal", "Mansi", "Preeti", "Richa",
    "Monika", "Shweta", "Jyoti", "Vandana", "Rashmi", "Archana", "Poonam", "Seema",
]

LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Patel", "Kumar", "Gupta", "Joshi", "Mehta",
    "Shah", "Malhotra", "Kapoor", "Chopra", "Bose", "Das", "Rao", "Nair",
    "Iyer", "Reddy", "Pillai", "Menon", "Banerjee", "Chatterjee", "Mukherjee",
    "Mishra", "Tiwari", "Pandey", "Dubey", "Srivastava", "Agarwal", "Bhatt",
    "Patil", "Desai", "Kulkarni", "Jain", "Saxena", "Shukla", "Yadav", "Chauhan",
]

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Marketing", "Sales",
    "HR", "Finance", "Operations", "Data Science", "Research"
]

ROLES = ["individual"] * 8 + ["manager"] * 2  # 80% individual, 20% manager


# ── Personality archetypes for realistic distribution ─────────────────────────
ARCHETYPES = [
    # (openness, conscientiousness, extraversion, agreeableness, neuroticism)
    # Creative/Artistic
    {"base": {"openness": 4.2, "conscientiousness": 2.8, "extraversion": 3.2, "agreeableness": 3.5, "neuroticism": 3.0}, "weight": 10},
    # Leader/Extrovert
    {"base": {"openness": 3.5, "conscientiousness": 4.0, "extraversion": 4.5, "agreeableness": 3.8, "neuroticism": 2.2}, "weight": 12},
    # Analyst/Introvert
    {"base": {"openness": 3.8, "conscientiousness": 4.2, "extraversion": 2.0, "agreeableness": 3.2, "neuroticism": 2.8}, "weight": 15},
    # Team Player
    {"base": {"openness": 3.2, "conscientiousness": 3.5, "extraversion": 3.8, "agreeableness": 4.5, "neuroticism": 2.5}, "weight": 12},
    # High Achiever
    {"base": {"openness": 3.6, "conscientiousness": 4.8, "extraversion": 3.5, "agreeableness": 3.2, "neuroticism": 2.0}, "weight": 10},
    # Anxious/Sensitive
    {"base": {"openness": 3.8, "conscientiousness": 3.2, "extraversion": 2.5, "agreeableness": 4.0, "neuroticism": 4.2}, "weight": 8},
    # Adventurous
    {"base": {"openness": 4.5, "conscientiousness": 2.5, "extraversion": 4.2, "agreeableness": 3.5, "neuroticism": 2.8}, "weight": 8},
    # Steady/Reliable
    {"base": {"openness": 2.8, "conscientiousness": 4.5, "extraversion": 3.0, "agreeableness": 4.2, "neuroticism": 2.0}, "weight": 12},
    # Average/Balanced
    {"base": {"openness": 3.2, "conscientiousness": 3.2, "extraversion": 3.2, "agreeableness": 3.5, "neuroticism": 3.0}, "weight": 13},
]


def generate_realistic_responses(archetype: dict) -> dict:
    """Generate responses that reflect a personality archetype with realistic noise."""
    responses = {}
    for q in QUESTIONS:
        trait = q["trait"]
        base  = archetype["base"][trait]
        # Add realistic noise (±0.8 on 1-5 scale)
        noise = random.gauss(0, 0.5)
        raw   = base + noise
        score = max(1, min(5, round(raw)))
        responses[q["id"]] = score
    return responses


def pick_archetype() -> dict:
    """Weighted random archetype selection."""
    weights = [a["weight"] for a in ARCHETYPES]
    return random.choices(ARCHETYPES, weights=weights, k=1)[0]


def generate_name() -> tuple:
    """Generate a realistic Indian name."""
    gender    = random.choice(["male", "female"])
    first     = random.choice(FIRST_NAMES_MALE if gender == "male" else FIRST_NAMES_FEMALE)
    last      = random.choice(LAST_NAMES)
    full_name = f"{first} {last}"
    email     = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@gmail.com"
    return full_name, email


def seed_users(db, count: int = 200):
    print(f"🌱 Seeding {count} user profiles...")
    pipeline   = get_pipeline()
    created    = 0
    pw_hash    = bcrypt.hashpw("Demo1234!".encode(), bcrypt.gensalt()).decode()

    for i in range(count):
        full_name, email = generate_name()

        # Skip if email exists
        if db.query(User).filter(User.email == email).first():
            full_name, email = generate_name()

        role       = random.choice(ROLES)
        department = random.choice(DEPARTMENTS)

        user = User(
            email=email, password_hash=pw_hash,
            full_name=full_name, role=role, department=department,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 180))
        )
        db.add(user)
        db.flush()

        # Generate 1-3 assessments per user (for drift detection demo)
        num_assessments = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        archetype = pick_archetype()

        for j in range(num_assessments):
            responses = generate_realistic_responses(archetype)
            profile   = pipeline.predict(responses)

            assessment = Assessment(
                user_id=user.id,
                responses={str(k): v for k, v in responses.items()},
                completed_at=datetime.utcnow() - timedelta(days=random.randint(0, 90) - j * 30),
            )
            db.add(assessment)
            db.flush()

            score = TraitScore(
                user_id=user.id, assessment_id=assessment.id,
                openness=profile.openness, conscientiousness=profile.conscientiousness,
                extraversion=profile.extraversion, agreeableness=profile.agreeableness,
                neuroticism=profile.neuroticism, openness_pct=profile.openness_pct,
                conscientiousness_pct=profile.conscientiousness_pct,
                extraversion_pct=profile.extraversion_pct,
                agreeableness_pct=profile.agreeableness_pct,
                neuroticism_pct=profile.neuroticism_pct,
                dominant_trait=profile.dominant_trait,
                created_at=assessment.completed_at,
            )
            db.add(score)

        created += 1
        if created % 50 == 0:
            db.commit()
            print(f"  ✅ {created}/{count} profiles created...")

    db.commit()
    print(f"✅ Successfully seeded {created} user profiles!")


if __name__ == "__main__":
    create_tables()
    db = SessionLocal()
    try:
        seed_users(db, count=210)
    finally:
        db.close()
    print("🎉 Demo data seeding complete!")