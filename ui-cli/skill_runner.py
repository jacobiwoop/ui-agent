"""
Skill Runner — exécute le skill ui-ux-pro-max et retourne les données structurées.
"""

import sys
import os
import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent / "skill"
SCRIPTS_DIR = SKILL_DIR / "scripts"


def _import_skill():
    """Importe dynamiquement core.py et design_system.py du skill."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    
    # Patch DATA_DIR pour pointer vers le bon dossier
    import core as _core
    _core.DATA_DIR = SKILL_DIR / "data"
    return _core


def search_domain(query: str, domain: str, max_results: int = 3) -> list:
    """Recherche dans un domaine spécifique du skill."""
    try:
        core = _import_skill()
        result = core.search(query, domain, max_results)
        return result.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]


def search_stack(query: str, stack: str, max_results: int = 3) -> list:
    """Recherche les guidelines pour un stack spécifique."""
    try:
        core = _import_skill()
        result = core.search_stack(query, stack, max_results)
        return result.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]


def generate_design_system(query: str, project_name: str = None) -> dict:
    """Génère le design system complet via le skill."""
    try:
        if str(SCRIPTS_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_DIR))
        
        import core as _core
        _core.DATA_DIR = SKILL_DIR / "data"
        
        from design_system import DesignSystemGenerator
        gen = DesignSystemGenerator()
        # Patch DATA_DIR dans design_system aussi
        import design_system as _ds
        _ds.DATA_DIR = SKILL_DIR / "data"
        
        result = gen.generate(query, project_name)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_ux_guidelines(query: str, max_results: int = 3) -> list:
    """Récupère les guidelines UX pertinentes."""
    return search_domain(query, "ux", max_results)


def get_colors(product_type: str) -> list:
    """Récupère la palette de couleurs pour un type de produit."""
    return search_domain(product_type, "color", 2)


def get_typography(style_query: str) -> list:
    """Récupère les recommandations typographiques."""
    return search_domain(style_query, "typography", 2)


def get_style(style_query: str) -> list:
    """Récupère les recommandations de style."""
    return search_domain(style_query, "style", 3)


def build_context_for_ai(analysis: dict) -> dict:
    """
    Construit le contexte complet depuis le skill pour l'IA.
    Retourne un dict structuré prêt à être injecté dans le prompt Ollama.
    """
    q = analysis["skill_query"]
    stack = analysis["stack"]
    product = analysis["product_type"]

    context = {
        "styles": get_style(q),
        "colors": get_colors(product),
        "typography": get_typography(q),
        "ux_guidelines": get_ux_guidelines(q),
        "stack_guidelines": search_stack(q, stack),
    }

    # Filtrage : supprime les résultats vides ou en erreur
    return {k: v for k, v in context.items() if v and "error" not in str(v)}
