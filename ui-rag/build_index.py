#!/usr/bin/env python3
"""
build_index.py — Indexation one-shot des CSV UI/UX dans ChromaDB.

À lancer une seule fois (ou après modification des CSV) :
    python build_index.py
    python build_index.py --reset   ← repart de zéro
"""

import csv
import argparse
from pathlib import Path
from vector_store import get_store

DATA_DIR = Path(__file__).parent / "skill" / "data"


# ── Constructeurs de chunks par fichier ──────────────────────────────────────

def chunks_styles() -> list[dict]:
    """styles.csv → chunks sémantiques."""
    chunks = []
    filepath = DATA_DIR / "styles.csv"
    with open(filepath, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            name = row.get("Style Category", "")
            keywords = row.get("Keywords", "")
            best_for = row.get("Best For", "")
            effects = row.get("Effects & Animation", "")
            ai_prompt = row.get("AI Prompt Keywords", "")
            mood = row.get("Type", "")

            text = f"{name} · {keywords} · {best_for} · {effects} · {ai_prompt}".strip(" ·")

            chunks.append({
                "id": f"style_{i}",
                "text": text,
                "metadata": {
                    "domain": "style",
                    "source": "styles.csv",
                    "name": name,
                    "mood": mood,
                    "complexity": row.get("Complexity", ""),
                    "light_mode": row.get("Light Mode ✓", ""),
                    "dark_mode": row.get("Dark Mode ✓", ""),
                    "performance": row.get("Performance", ""),
                    "accessibility": row.get("Accessibility", ""),
                    "checklist": row.get("Implementation Checklist", "")[:200],
                    "css_keywords": row.get("CSS/Technical Keywords", "")[:200],
                    "design_vars": row.get("Design System Variables", "")[:200],
                }
            })
    return chunks


def chunks_colors() -> list[dict]:
    """colors.csv → chunks sémantiques."""
    chunks = []
    filepath = DATA_DIR / "colors.csv"
    with open(filepath, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            product = row.get("Product Type", "")
            notes = row.get("Notes", "")
            text = f"{product} · {notes}"

            chunks.append({
                "id": f"color_{i}",
                "text": text,
                "metadata": {
                    "domain": "color",
                    "source": "colors.csv",
                    "product_type": product,
                    "primary": row.get("Primary (Hex)", ""),
                    "secondary": row.get("Secondary (Hex)", ""),
                    "cta": row.get("CTA (Hex)", ""),
                    "background": row.get("Background (Hex)", ""),
                    "text_color": row.get("Text (Hex)", ""),
                    "border": row.get("Border (Hex)", ""),
                }
            })
    return chunks


def chunks_typography() -> list[dict]:
    """typography.csv → chunks sémantiques."""
    chunks = []
    filepath = DATA_DIR / "typography.csv"
    with open(filepath, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            name = row.get("Font Pairing Name", "")
            mood = row.get("Mood/Style Keywords", "")
            best_for = row.get("Best For", "")
            heading = row.get("Heading Font", "")
            body = row.get("Body Font", "")
            category = row.get("Category", "")

            text = f"{name} · {mood} · {best_for} · {heading} {body} · {category}"

            chunks.append({
                "id": f"typo_{i}",
                "text": text,
                "metadata": {
                    "domain": "typography",
                    "source": "typography.csv",
                    "name": name,
                    "heading": heading,
                    "body": body,
                    "category": category,
                    "google_url": row.get("Google Fonts URL", ""),
                    "css_import": row.get("CSS Import", "")[:300],
                    "tailwind": row.get("Tailwind Config", "")[:300],
                    "notes": row.get("Notes", ""),
                }
            })
    return chunks


def chunks_ux() -> list[dict]:
    """ux-guidelines.csv → chunks sémantiques."""
    chunks = []
    filepath = DATA_DIR / "ux-guidelines.csv"
    with open(filepath, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            category = row.get("Category", "")
            issue = row.get("Issue", "")
            description = row.get("Description", "")
            do_ = row.get("Do", "")
            dont = row.get("Don't", "")
            platform = row.get("Platform", "")

            text = f"{category} · {issue} · {description} · do: {do_} · avoid: {dont}"

            chunks.append({
                "id": f"ux_{i}",
                "text": text,
                "metadata": {
                    "domain": "ux",
                    "source": "ux-guidelines.csv",
                    "category": category,
                    "issue": issue,
                    "platform": platform,
                    "severity": row.get("Severity", ""),
                    "do": do_[:200],
                    "dont": dont[:200],
                    "code_good": row.get("Code Example Good", "")[:300],
                    "code_bad": row.get("Code Example Bad", "")[:300],
                }
            })
    return chunks


def chunks_products() -> list[dict]:
    """products.csv → chunks sémantiques."""
    chunks = []
    filepath = DATA_DIR / "products.csv"
    with open(filepath, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            product = row.get("Product Type", "")
            keywords = row.get("Keywords", "")
            style_rec = row.get("Primary Style Recommendation", "")
            considerations = row.get("Key Considerations", "")
            color_focus = row.get("Color Palette Focus", "")

            text = f"{product} · {keywords} · {style_rec} · {considerations} · {color_focus}"

            chunks.append({
                "id": f"product_{i}",
                "text": text,
                "metadata": {
                    "domain": "product",
                    "source": "products.csv",
                    "product_type": product,
                    "primary_style": style_rec,
                    "secondary_styles": row.get("Secondary Styles", ""),
                    "landing_pattern": row.get("Landing Page Pattern", ""),
                    "dashboard_style": row.get("Dashboard Style (if applicable)", ""),
                    "color_focus": color_focus,
                }
            })
    return chunks


def chunks_landing() -> list[dict]:
    """landing.csv → chunks sémantiques."""
    chunks = []
    filepath = DATA_DIR / "landing.csv"
    with open(filepath, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            name = row.get("Pattern Name", "")
            keywords = row.get("Keywords", "")
            conversion = row.get("Conversion Optimization", "")
            section_order = row.get("Section Order", "")

            text = f"{name} · {keywords} · {conversion}"

            chunks.append({
                "id": f"landing_{i}",
                "text": text,
                "metadata": {
                    "domain": "landing",
                    "source": "landing.csv",
                    "pattern": name,
                    "section_order": section_order[:300],
                    "cta_placement": row.get("Primary CTA Placement", ""),
                    "color_strategy": row.get("Color Strategy", ""),
                    "conversion": conversion[:200],
                }
            })
    return chunks


def chunks_stacks() -> list[dict]:
    """stacks/*.csv → chunks sémantiques."""
    chunks = []
    stacks_dir = DATA_DIR / "stacks"
    stack_files = list(stacks_dir.glob("*.csv"))

    for filepath in stack_files:
        stack_name = filepath.stem  # ex: "react", "nextjs"
        with open(filepath, encoding="utf-8") as f:
            for i, row in enumerate(csv.DictReader(f)):
                category = row.get("Category", "")
                guideline = row.get("Guideline", "")
                description = row.get("Description", "")
                do_ = row.get("Do", "")
                dont = row.get("Don't", "")

                text = f"{stack_name} · {category} · {guideline} · {description} · do: {do_}"

                chunks.append({
                    "id": f"stack_{stack_name}_{i}",
                    "text": text,
                    "metadata": {
                        "domain": "stack",
                        "stack": stack_name,
                        "source": f"stacks/{stack_name}.csv",
                        "category": category,
                        "guideline": guideline,
                        "severity": row.get("Severity", ""),
                        "do": do_[:200],
                        "dont": dont[:200],
                        "code_good": row.get("Code Good", "")[:300],
                        "code_bad": row.get("Code Bad", "")[:300],
                        "docs_url": row.get("Docs URL", ""),
                    }
                })
    return chunks


# ── Pipeline principal ────────────────────────────────────────────────────────

BUILDERS = [
    ("styles",     chunks_styles),
    ("colors",     chunks_colors),
    ("typography", chunks_typography),
    ("ux",         chunks_ux),
    ("products",   chunks_products),
    ("landing",    chunks_landing),
    ("stacks",     chunks_stacks),
]


def build(reset: bool = False):
    store = get_store()

    if reset:
        print("🗑️  Réinitialisation de l'index...")
        store.reset()
    elif store.is_built():
        count = store.count()
        print(f"✅ Index déjà construit ({count} chunks).")
        print("   Lance avec --reset pour reconstruire.")
        return

    print("🔨 Construction de l'index vectoriel...\n")

    all_chunks = []
    for name, builder in BUILDERS:
        chunks = builder()
        print(f"  {name:<12} → {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"\n  Total : {len(all_chunks)} chunks\n")
    store.add(all_chunks)

    print(f"\n✅ Index construit → {store.count()} chunks dans vectordb/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construit l'index vectoriel UI/UX")
    parser.add_argument("--reset", action="store_true", help="Repart de zéro")
    args = parser.parse_args()
    build(reset=args.reset)
