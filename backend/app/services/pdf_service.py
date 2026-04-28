"""
PDF Report Generator for Traitlytics
Generates a professional personality report using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

TRAIT_COLORS = {
    "openness":          "#38bdf8",
    "conscientiousness": "#34d399",
    "extraversion":      "#fbbf24",
    "agreeableness":     "#a78bfa",
    "neuroticism":       "#f87171",
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
    """Generate a professional PDF personality report."""
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )

    styles  = getSampleStyleSheet()
    content = []

    # ── Header ────────────────────────────────────────────────────────────────
    header_style = ParagraphStyle(
        "Header", parent=styles["Normal"],
        fontSize=24, fontName="Helvetica-Bold",
        textColor=HexColor("#38bdf8"), spaceAfter=4, alignment=TA_CENTER
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=11, textColor=HexColor("#64748b"),
        spaceAfter=2, alignment=TA_CENTER
    )
    content.append(Paragraph("🧠 Traitlytics", header_style))
    content.append(Paragraph("Big Five Personality Assessment Report", sub_style))
    content.append(Paragraph(f"Prepared for: {user_name}", sub_style))
    content.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}", sub_style))
    content.append(Spacer(1, 0.2*inch))
    content.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1e293b")))
    content.append(Spacer(1, 0.2*inch))

    # ── Dominant Trait ────────────────────────────────────────────────────────
    dominant = profile.get("dominant_trait", "openness")
    dom_style = ParagraphStyle(
        "Dom", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=HexColor(TRAIT_COLORS[dominant]),
        spaceAfter=4, alignment=TA_CENTER
    )
    content.append(Paragraph(f"Dominant Trait: {TRAIT_LABELS[dominant]}", dom_style))
    content.append(Spacer(1, 0.15*inch))

    # ── Score Table ───────────────────────────────────────────────────────────
    section_style = ParagraphStyle(
        "Section", parent=styles["Normal"],
        fontSize=13, fontName="Helvetica-Bold",
        textColor=HexColor("#e2e8f0"), spaceAfter=8
    )
    content.append(Paragraph("Trait Score Summary", section_style))

    traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    table_data = [["Trait", "Score", "Percentile", "Level"]]
    for trait in traits:
        score = profile.get(trait, 0)
        pct   = profile.get(f"{trait}_pct", 0)
        level = "High" if score >= 60 else "Average" if score >= 40 else "Low"
        table_data.append([
            TRAIT_LABELS[trait],
            f"{score:.0f}/100",
            f"{pct:.0f}th",
            level,
        ])

    table = Table(table_data, colWidths=[2.8*inch, 1.0*inch, 1.0*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  HexColor("#0f172a")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  HexColor("#38bdf8")),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  10),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",       (0, 0), (0, -1),  "LEFT"),
        ("BACKGROUND",  (0, 1), (-1, -1), HexColor("#020817")),
        ("TEXTCOLOR",   (0, 1), (-1, -1), HexColor("#e2e8f0")),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#0f172a"), HexColor("#020817")]),
        ("GRID",        (0, 0), (-1, -1), 0.5, HexColor("#1e293b")),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    content.append(table)
    content.append(Spacer(1, 0.2*inch))

    # ── Trait Descriptions ────────────────────────────────────────────────────
    content.append(Paragraph("Detailed Trait Analysis", section_style))

    desc_style = ParagraphStyle(
        "Desc", parent=styles["Normal"],
        fontSize=9, textColor=HexColor("#94a3b8"),
        spaceAfter=6, leading=14
    )
    trait_name_style = ParagraphStyle(
        "TraitName", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold",
        spaceAfter=2
    )

    for trait in traits:
        score = profile.get(trait, 0)
        level = "high" if score >= 50 else "low"
        color = TRAIT_COLORS[trait]

        name_para = ParagraphStyle(
            f"TN_{trait}", parent=styles["Normal"],
            fontSize=11, fontName="Helvetica-Bold",
            textColor=HexColor(color), spaceAfter=2
        )
        content.append(Paragraph(
            f"{TRAIT_LABELS[trait]} — {score:.0f}/100",
            name_para
        ))
        content.append(Paragraph(
            TRAIT_DESCRIPTIONS[trait][level],
            desc_style
        ))

    content.append(Spacer(1, 0.2*inch))
    content.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#1e293b")))

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=HexColor("#475569"),
        alignment=TA_CENTER, spaceBefore=8
    )
    content.append(Paragraph(
        "This report is based on the IPIP Big Five personality model. "
        "Scores are computed against published population norms (Goldberg et al.). "
        "Generated by Traitlytics — Personality Analytics Platform.",
        footer_style
    ))

    doc.build(content)
    return buffer.getvalue()