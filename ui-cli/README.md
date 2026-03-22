# uiux-cli — Direction Design UI/UX × IA

Service CLI Python qui combine le skill **ui-ux-pro-max** (base de données UI/UX)
avec **Ollama/Qwen** pour générer des directions de design structurées.

## Architecture

```
Requête utilisateur
       ↓
  [Analyzer]          → détecte stack, produit, style
       ↓
  [Skill Runner]      → recherche BM25 dans les CSV (styles, couleurs, typo, UX...)
       ↓
  [Prompt Builder]    → fusionne données CSV + contexte dans un prompt enrichi
       ↓
  [Ollama / Qwen]     → raisonne, comble les lacunes, génère la direction
       ↓
  Direction JSON      → pattern, couleurs, typo, effets, anti-patterns, UX
       ↓
  [Feedback loop]     → l'utilisateur peut raffiner en boucle
```

## Prérequis

```bash
# 1. Installer Ollama
# https://ollama.com

# 2. Télécharger Qwen
ollama pull qwen2.5

# 3. Démarrer Ollama
ollama serve
```

## Installation

```bash
git clone <repo>
cd uiux-cli
# Aucune dépendance externe — Python stdlib uniquement
```

## Usage

### Mode interactif (recommandé)
```bash
python main.py
```

### One-shot direct
```bash
python main.py "landing page pour une startup fintech dark mode"
python main.py "dashboard SaaS analytics react" --stack react
python main.py "app mobile beauté iOS" --model qwen2.5:14b
```

### Sortie JSON pure (pour intégration)
```bash
python main.py "portfolio freelance minimal" --json
```

### Feedback et itération
Dans le mode interactif, après avoir reçu une direction :
```
feedback: je veux quelque chose de plus coloré et ludique
feedback: la palette est trop froide, utilise des tons chauds
feedback: ajoute plus de détails sur les animations
```

### Options
```
--model, -m     Modèle Ollama (défaut: qwen2.5:latest)
--stack, -s     Force un stack (react, nextjs, vue, svelte, html-tailwind...)
--json, -j      Sortie JSON uniquement
--verbose, -v   Affiche les détails d'analyse et domaines trouvés
--list-models   Liste les modèles Ollama disponibles
```

## Ce que l'IA apporte (vs skill seul)

| Skill ui-ux-pro-max | + Qwen/Ollama |
|---|---|
| Recherche BM25 dans CSV | Comprend les requêtes ambiguës |
| Règles pré-définies | Adapte selon le contexte projet |
| Guidelines statiques | Justifie et argumente les choix |
| Une seule passe | Itère selon le feedback |
| Données structurées | Comble les lacunes avec le raisonnement |

## Structure du projet

```
uiux-cli/
├── main.py              ← CLI principal + boucle interactive
├── analyzer.py          ← détection stack/produit/style
├── skill_runner.py      ← interface avec le skill ui-ux-pro-max
├── prompt_builder.py    ← construction du prompt enrichi
├── ollama_client.py     ← appels Ollama + parsing JSON
├── README.md
└── skill/               ← skill ui-ux-pro-max (données + scripts)
    ├── SKILL.md
    ├── data/            ← CSV (styles, colors, typography, ux...)
    └── scripts/         ← moteur BM25
```

## Exemple de sortie

```
─────────────────────────────────────────────────
🎨  DIRECTION DESIGN
─────────────────────────────────────────────────

  Pattern    : Hero + Social Proof + CTA
  Style      : Glassmorphism + Dark Mode
  Mood       : Confiance, modernité, innovation

  Rationale  : Pour une fintech dark mode, le glassmorphism
               renforce la perception premium tout en maintenant
               la lisibilité des données financières...

─────────────────────────────────────────────────
🎨  COULEURS
─────────────────────────────────────────────────
  primary    : #1A56DB
  secondary  : #7E3AF2
  cta        : #0E9F6E
  background : #111827
  text       : #F9FAFB

─────────────────────────────────────────────────
✨  EFFETS CLÉS
─────────────────────────────────────────────────
  • Backdrop blur 20px sur les cartes
  • Hover transitions 200ms ease
  • Gradient subtle sur les CTAs

─────────────────────────────────────────────────
🚫  ANTI-PATTERNS À ÉVITER
─────────────────────────────────────────────────
  • Trop d'animations simultanées
  • Texte gris sur fond sombre (contraste insuffisant)
  • Boutons sans état hover visible
```
