#!/usr/bin/env python3
"""
uiux-cli — Service de direction design UI/UX boosté à l'IA
Usage: python main.py [requête] [--model <model>] [--stack <stack>] [--json]
"""

import argparse
import json
import os
import sys
from datetime import datetime

from analyzer import analyze
from skill_runner import build_context_for_ai
from prompt_builder import build_prompt, build_feedback_prompt
from ollama_client import get_design_direction, check_ollama_available, list_available_models


# ─── Affichage ────────────────────────────────────────────────────────────────

SEPARATOR = "─" * 60

def print_banner():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           uiux-cli  ·  Design Direction AI               ║
║     Skill ui-ux-pro-max  ×  Ollama / Qwen                ║
╚══════════════════════════════════════════════════════════╝
""")

def export_direction(direction: dict, analysis: dict, fmt: str = "json") -> str:
    """Exporte la direction dans un fichier JSON ou Markdown."""
    os.makedirs("exports", exist_ok=True)
    slug = (analysis["product_type"] + "_" + "_".join(analysis["styles"][:1])).replace(" ", "-").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        filepath = f"exports/{slug}_{timestamp}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"meta": analysis, "direction": direction}, f, indent=2, ensure_ascii=False)
    else:
        filepath = f"exports/{slug}_{timestamp}.md"
        d = direction.get("design_direction", {})
        c = direction.get("colors", {})
        t = direction.get("typography", {})
        lines = [
            f"# Direction Design — {analysis['product_type'].title()}",
            f"> Générée le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"\n## Contexte\n- **Produit** : {analysis['product_type']}\n- **Stack** : {analysis['stack']}\n- **Styles** : {', '.join(analysis['styles'])}",
            f"\n## Direction\n- **Pattern** : {d.get('pattern','')}\n- **Style** : {d.get('style','')}\n- **Mood** : {d.get('mood','')}\n\n> {d.get('rationale','')}",
            "\n## Couleurs\n| Rôle | Hex |\n|---|---|",
        ]
        for k, v in c.items():
            lines.append(f"| {k} | `{v}` |")
        lines.append(f"\n## Typographie\n- **Heading** : {t.get('heading','')}\n- **Body** : {t.get('body','')}\n- **Scale** : {t.get('scale','')}")
        for section, key in [("✨ Effets clés", "key_effects"), ("🚫 Anti-patterns", "anti_patterns"), ("🧭 Priorités UX", "ux_priorities")]:
            items = direction.get(key, [])
            if items:
                lines.append(f"\n## {section}")
                lines.extend(f"- {i}" for i in items)
        if direction.get("stack_notes"):
            lines.append(f"\n## Notes Stack\n{direction['stack_notes']}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    return filepath


def print_direction(direction: dict, as_json: bool = False):
    """Affiche la direction design de façon lisible."""
    if as_json:
        print(json.dumps(direction, indent=2, ensure_ascii=False))
        return

    if "error" in direction:
        print(f"\n❌ Erreur: {direction['error']}")
        if "raw" in direction:
            print(f"Réponse brute:\n{direction['raw']}")
        return

    d = direction.get("design_direction", {})
    c = direction.get("colors", {})
    t = direction.get("typography", {})
    
    print(f"\n{SEPARATOR}")
    print(f"🎨  DIRECTION DESIGN")
    print(SEPARATOR)

    if d:
        print(f"\n  Pattern    : {d.get('pattern', '—')}")
        print(f"  Style      : {d.get('style', '—')}")
        print(f"  Mood       : {d.get('mood', '—')}")
        print(f"\n  Rationale  : {d.get('rationale', '—')}")

    if c:
        print(f"\n{SEPARATOR}")
        print(f"🎨  COULEURS")
        print(SEPARATOR)
        for key, val in c.items():
            print(f"  {key:<12}: {val}")

    if t:
        print(f"\n{SEPARATOR}")
        print(f"📝  TYPOGRAPHIE")
        print(SEPARATOR)
        print(f"  Heading    : {t.get('heading', '—')}")
        print(f"  Body       : {t.get('body', '—')}")
        print(f"  Scale      : {t.get('scale', '—')}")

    effects = direction.get("key_effects", [])
    if effects:
        print(f"\n{SEPARATOR}")
        print(f"✨  EFFETS CLÉS")
        print(SEPARATOR)
        for e in effects:
            print(f"  • {e}")

    anti = direction.get("anti_patterns", [])
    if anti:
        print(f"\n{SEPARATOR}")
        print(f"🚫  ANTI-PATTERNS À ÉVITER")
        print(SEPARATOR)
        for a in anti:
            print(f"  • {a}")

    ux = direction.get("ux_priorities", [])
    if ux:
        print(f"\n{SEPARATOR}")
        print(f"🧭  PRIORITÉS UX")
        print(SEPARATOR)
        for u in ux:
            print(f"  • {u}")

    stack_notes = direction.get("stack_notes", "")
    if stack_notes:
        print(f"\n{SEPARATOR}")
        print(f"⚙️   NOTES STACK")
        print(SEPARATOR)
        print(f"  {stack_notes}")

    confidence = direction.get("confidence", "—")
    clarif = direction.get("clarification_needed")
    
    print(f"\n{SEPARATOR}")
    print(f"  Confiance  : {confidence}")
    if clarif:
        print(f"\n  ❓ Clarification demandée par l'IA:")
        print(f"     {clarif}")
    print(SEPARATOR)


def print_analysis(analysis: dict):
    """Affiche l'analyse de la requête."""
    print(f"\n📊 Analyse de la requête:")
    print(f"   Produit  : {analysis['product_type']}")
    print(f"   Stack    : {analysis['stack']}")
    print(f"   Styles   : {', '.join(analysis['styles'])}")
    print(f"   Query BM25: \"{analysis['skill_query']}\"")


def _prompt_export(direction: dict, analysis: dict):
    """Affiche les options d'export disponibles."""
    print(f"\n💡 Raffiner: feedback: <retour>  |  Exporter: export  |  export md")


# ─── Pipeline principal ───────────────────────────────────────────────────────

def run_pipeline(query: str, model: str, as_json: bool, verbose: bool) -> tuple:
    """Exécute le pipeline complet. Retourne (direction, analysis)."""
    print("\n⚙️  Analyse de la requête...")
    analysis = analyze(query)
    if verbose:
        print_analysis(analysis)

    print("📚 Recherche dans la base de données UI/UX...")
    skill_context = build_context_for_ai(analysis)
    if verbose:
        print(f"   Domaines trouvés: {', '.join(skill_context.keys())}")

    messages = build_prompt(analysis, skill_context)
    direction = get_design_direction(messages, model=model)
    return direction, analysis


def interactive_mode(model: str, as_json: bool, verbose: bool):
    """Mode interactif avec boucle feedback + export + contexte sticky."""
    print_banner()

    print("🔍 Vérification d'Ollama...")
    if not check_ollama_available(model):
        available = list_available_models()
        if available:
            print(f"⚠️  Modèle '{model}' non trouvé.")
            print(f"   Modèles disponibles: {', '.join(available)}")
            print(f"   Lance avec --model <nom>")
        else:
            print(f"❌ Ollama n'est pas disponible.")
            print(f"   Démarre Ollama: ollama serve")
            print(f"   Installe un modèle: ollama pull qwen3.5")
        sys.exit(1)

    print(f"✅ Ollama prêt · modèle: {model}\n")
    print("  Commandes: feedback: <retour>  |  export  |  export md  |  quit\n")

    history = []
    last_direction = None
    last_analysis = None  # contexte sticky

    while True:
        try:
            print(SEPARATOR)
            query = input("🎯 Requête : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAu revoir !")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("\nAu revoir !")
            break

        # ── Export ───────────────────────────────────────────────
        if query.lower() in ("export", "export json"):
            if not last_direction:
                print("\n⚠️  Aucune direction générée pour l'instant.")
                continue
            path = export_direction(last_direction, last_analysis, fmt="json")
            print(f"\n💾 Exporté → {path}")
            continue

        if query.lower() == "export md":
            if not last_direction:
                print("\n⚠️  Aucune direction générée pour l'instant.")
                continue
            path = export_direction(last_direction, last_analysis, fmt="md")
            print(f"\n💾 Exporté → {path}")
            continue

        # ── Feedback (contexte sticky) ───────────────────────────
        if query.lower().startswith("feedback:") and last_direction:
            feedback_text = query[9:].strip()
            print(f"\n💬 Feedback: {feedback_text}")

            # Garde le contexte de base + enrichit avec le feedback
            fb_analysis = last_analysis.copy()
            extra = analyze(feedback_text)
            fb_analysis["styles"] = list(set(fb_analysis["styles"] + extra["styles"]))
            fb_analysis["skill_query"] = f"{fb_analysis['skill_query']} {extra['skill_query']}".strip()

            skill_context = build_context_for_ai(fb_analysis)
            base_messages = build_prompt(fb_analysis, skill_context, history=history)
            feedback_msg = build_feedback_prompt(last_direction, feedback_text)
            base_messages.append(feedback_msg)

            direction = get_design_direction(base_messages, model=model)
            print_direction(direction, as_json=as_json)

            history.append(feedback_msg)
            history.append({"role": "assistant", "content": json.dumps(direction, ensure_ascii=False)})
            last_direction = direction
            last_analysis = fb_analysis
            _prompt_export(last_direction, last_analysis)

        # ── Nouvelle requête ─────────────────────────────────────
        else:
            history = []
            direction, analysis = run_pipeline(query, model, as_json, verbose)
            print_direction(direction, as_json=as_json)

            last_direction = direction
            last_analysis = analysis
            history.append({
                "role": "assistant",
                "content": json.dumps(direction, ensure_ascii=False)
            })
            _prompt_export(last_direction, last_analysis)


# ─── Entrée CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="uiux-cli — Direction design UI/UX boostée à l'IA"
    )
    parser.add_argument(
        "query", nargs="?",
        help="Requête directe (sans interactivité)"
    )
    parser.add_argument(
        "--model", "-m",
        default="qwen3.5:cloud",
        help="Modèle Ollama à utiliser (défaut: qwen3.5:cloud)"
    )
    parser.add_argument(
        "--stack", "-s",
        help="Force un stack spécifique (ex: react, nextjs, vue)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Sortie en JSON pur"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Affiche les détails d'analyse"
    )
    parser.add_argument(
        "--export", "-e",
        choices=["json", "md"],
        help="Exporte la direction (json ou md) — mode one-shot uniquement"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Liste les modèles Ollama disponibles"
    )

    args = parser.parse_args()

    if args.list_models:
        models = list_available_models()
        if models:
            print("Modèles disponibles:")
            for m in models:
                print(f"  • {m}")
        else:
            print("Aucun modèle trouvé (Ollama actif?)")
        return

    if args.query:
        # Mode one-shot
        if args.stack:
            args.query += f" {args.stack}"
        direction, analysis = run_pipeline(args.query, args.model, args.json, args.verbose)
        print_direction(direction, as_json=args.json)
        if args.export:
            path = export_direction(direction, analysis, fmt=args.export)
            print(f"\n💾 Exporté → {path}")
    else:
        # Mode interactif
        interactive_mode(args.model, args.json, args.verbose)


if __name__ == "__main__":
    main()