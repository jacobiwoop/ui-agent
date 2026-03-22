"""
Analyzer — extrait stack, type produit et style depuis la requête libre.
"""

import re

STACKS = [
    "react", "nextjs", "vue", "nuxtjs", "nuxt-ui", "svelte",
    "swiftui", "react-native", "flutter", "shadcn",
    "jetpack-compose", "astro", "html-tailwind"
]

PRODUCT_KEYWORDS = {
    "saas": ["saas", "dashboard", "app", "platform", "tool", "software"],
    "ecommerce": ["shop", "store", "ecommerce", "boutique", "produit", "vente", "cart", "panier"],
    "landing": ["landing", "page", "vitrine", "présentation", "présenter", "marketing"],
    "portfolio": ["portfolio", "cv", "freelance", "showcase", "galerie"],
    "healthcare": ["santé", "médecin", "clinique", "hôpital", "health", "medical"],
    "fintech": ["finance", "banque", "paiement", "crypto", "investissement", "fintech"],
    "beauty": ["beauté", "spa", "cosmétique", "salon", "bien-être", "wellness"],
    "education": ["éducation", "école", "cours", "formation", "apprendre", "learning"],
    "blog": ["blog", "article", "contenu", "publication", "journal"],
}

STYLE_KEYWORDS = {
    "glassmorphism": ["verre", "glass", "transparent", "blur", "frosted"],
    "minimalism": ["minimal", "clean", "simple", "épuré", "minimaliste"],
    "dark mode": ["dark", "sombre", "nuit", "night", "noir"],
    "brutalism": ["brutal", "raw", "brut", "fort", "bold"],
    "elegant": ["élégant", "luxe", "premium", "raffiné", "luxury"],
    "playful": ["fun", "ludique", "coloré", "joyeux", "jeune"],
    "professional": ["professionnel", "corporate", "sérieux", "b2b"],
}


def analyze(query: str) -> dict:
    """Extrait le contexte structuré depuis une requête libre."""
    q = query.lower()

    # Détection stack
    detected_stack = "html-tailwind"
    for stack in STACKS:
        if stack in q or stack.replace("-", " ") in q:
            detected_stack = stack
            break

    # Détection type produit
    detected_product = "saas"
    best_score = 0
    for product, keywords in PRODUCT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > best_score:
            best_score = score
            detected_product = product

    # Détection style
    detected_styles = []
    for style, keywords in STYLE_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            detected_styles.append(style)
    if not detected_styles:
        detected_styles = ["professional"]

    # Construction de la query skill (mots-clés pour BM25)
    skill_query = f"{detected_product} {' '.join(detected_styles)}"

    return {
        "original_query": query,
        "stack": detected_stack,
        "product_type": detected_product,
        "styles": detected_styles,
        "skill_query": skill_query,
    }
