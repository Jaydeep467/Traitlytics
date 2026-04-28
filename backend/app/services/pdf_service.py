"""
PDF Report Generator for Traitlytics
Clean light theme professional report.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

TRAIT_COLORS = {
    "openness":          "#0ea5e9",
    "conscientiousness": "#10b981",
    "extraversion":      "#f59e0b",
    "agreeableness":     "#8b5cf6",
    "neuroticism":       "#ef4444",
}

TRAIT_LABELS = {
    "openness":          "Openness to Experience",
    "conscientiousness": "Conscientiousness",
    "extraversion":      "Extraversion",
    "agreeableness":     "Agreeableness",
    "neuroticism":       "Neuroticism (Emotional Stability)",
}

TRAIT_DESCRIPTIONS = {
    "openness": {
        "high": "Highly creative, intellectually curious, and open to novel experiences. Thrives in innovative, dynamic environments requiring creative problem-solving.",
        "low":  "Practical, conventional, and detail-oriented. Performs best in structured, predictable roles with clear guidelines.",
    },
    "conscientiousness": {
        "high": "Highly organized, reliable, and goal-directed. Demonstrates strong performance in roles requiring attention to detail and sustained effort.",
        "low":  "Flexible, spontaneous, and adaptable. Works well in dynamic environments requiring quick pivots and creative solutions.",
    },
    "extraversion": {
        "high": "Energetic, assertive, and thrives in social settings. Natural fit for leadership, sales, and client-facing roles.",
        "low":  "Thoughtful, independent, and deep-focused. Excels in analytical, research, and individual contributor roles.",
    },
    "agreeableness": {
        "high": "Cooperative, empathetic, and highly team-oriented. Strong in collaborative, mentoring, and people-management contexts.",
        "low":  "Direct, competitive, and analytically objective. Effective in negotiation, independent analysis, and decision-making roles.",
    },
    "neuroticism": {
        "high": "Emotionally sensitive and stress-reactive. Benefits from structured support, clear expectations, and low-ambiguity environments.",
        "low":  "Emotionally stable and calm under pressure. Well-suited for high-stakes, fast-paced, and crisis management roles.",
    },
}


def generate_pdf_report(profile: dict, user_name: str) -> bytes:
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )

    styles  = getSampleStyleSheet()
    content = []

    # ── Header ────────────────────────────────────────────────────────────────
    content.append(Spacer(1, 0.2*inch))
    content.append(Paragraph("Traitlytics", ParagraphStyle(
        "H", parent=styles["Normal"], fontSize=22, fontName="Helvetica-Bold",
        textColor=HexColor("#0ea5e9"), spaceAfter=6, alignment=TA_CENTER
    )))
    content.append(Paragraph("Personality Analytics Platform", ParagraphStyle(
        "Sub1", parent=styles["Normal"], fontSize=11,
        textColor=HexColor("#64748b"), spaceAfter=2, alignment=TA_CENTER
    )))
    content.append(Paragraph("Big Five Personality Assessment Report", ParagraphStyle(
        "Sub2", parent=styles["Normal"], fontSize=10,
        textColor=HexColor("#94a3b8"), spaceAfter=2, alignment=TA_CENTER
    )))
    content.append(Paragraph(f"Prepared for: <b>{user_name}</b>", ParagraphStyle(
        "Sub3", parent=styles["Normal"], fontSize=10,
        textColor=HexColor("#475569"), spaceAfter=2, alignment=TA_CENTER
    )))
    content.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}", ParagraphStyle(
        "Sub4", parent=styles["Normal"], fontSize=9,
        textColor=HexColor("#94a3b8"), spaceAfter=4, alignment=TA_CENTER
    )))
    content.append(Spacer(1, 0.1*inch))
    content.append(HRFlowable(width="100%", thickness=1.5, color=HexColor("#0ea5e9")))
    content.append(Spacer(1, 0.15*inch))

    # ── Dominant Trait ────────────────────────────────────────────────────────
    dominant = profile.get("dominant_trait", "openness")
    content.append(Paragraph(f"Dominant Trait: {TRAIT_LABELS[dominant]}", ParagraphStyle(
        "Dom", parent=styles["Normal"], fontSize=14, fontName="Helvetica-Bold",
        textColor=HexColor(TRAIT_COLORS[dominant]), spaceAfter=12, alignment=TA_CENTER
    )))

    # ── Score Table ───────────────────────────────────────────────────────────
    content.append(Paragraph("Trait Score Summary", ParagraphStyle(
        "Sec", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold",
        textColor=HexColor("#0f172a"), spaceAfter=8
    )))

    traits     = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    table_data = [["Trait", "Score", "Percentile", "Level"]]
    for trait in traits:
        score = profile.get(trait, 0)
        pct   = profile.get(f"{trait}_pct", 0)
        level = "High" if score >= 60 else "Average" if score >= 40 else "Low"
        table_data.append([TRAIT_LABELS[trait], f"{score:.0f}/100", f"{pct:.0f}th", level])

    table = Table(table_data, colWidths=[2.8*inch, 1.0*inch, 1.0*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  HexColor("#0ea5e9")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  HexColor("#ffffff")),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  10),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 0), (0, -1),  "LEFT"),
        ("BACKGROUND",    (0, 1), (-1, -1), HexColor("#ffffff")),
        ("TEXTCOLOR",     (0, 1), (-1, -1), HexColor("#0f172a")),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [HexColor("#f8fafc"), HexColor("#ffffff")]),
        ("GRID",          (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    content.append(table)
    content.append(Spacer(1, 0.2*inch))

    # ── Trait Descriptions ────────────────────────────────────────────────────
    content.append(Paragraph("Detailed Trait Analysis", ParagraphStyle(
        "Sec2", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold",
        textColor=HexColor("#0f172a"), spaceAfter=10
    )))

    for trait in traits:
        score = profile.get(trait, 0)
        level = "high" if score >= 50 else "low"
        content.append(Paragraph(f"{TRAIT_LABELS[trait]} — {score:.0f}/100", ParagraphStyle(
            f"TN_{trait}", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold",
            textColor=HexColor(TRAIT_COLORS[trait]), spaceAfter=3
        )))
        content.append(Paragraph(TRAIT_DESCRIPTIONS[trait][level], ParagraphStyle(
            f"TD_{trait}", parent=styles["Normal"], fontSize=9,
            textColor=HexColor("#475569"), spaceAfter=10, leading=14
        )))

    content.append(Spacer(1, 0.1*inch))
    content.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#e2e8f0")))
    content.append(Paragraph(
        "This report is based on the IPIP Big Five personality model. "
        "Scores are computed against published population norms (Goldberg et al.). "
        "Generated by Traitlytics — Personality Analytics Platform.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=HexColor("#94a3b8"), alignment=TA_CENTER, spaceBefore=8)
    ))

    doc.build(content)
    return buffer.getvalue()