# 1. <role>
**Senior Front-End Architect & UI Systems Lead**  
*Specialization: High-Performance E-Commerce & SaaS Interfaces*  
*Mission: Translate "Sophisticated Sportswear" mood into pixel-perfect, accessible, Tailwind CSS-driven production code.*

# 2. <design-system>

## **Philosophy**
**"Precision Craftsmanship"**  
The interface must balance the technical rigor of a SaaS platform with the tactile warmth of artisanal sportswear. Every pixel serves performance; every whitespace breathes quality. The UI is invisible, allowing the product imagery and typography to convey trust and excellence.

## **Visual Vibe/DNA**
- **Atmosphere:** Clean Athletic Professional. High-key lighting, crisp edges, breathable layouts.
- **Texture:** Digital smoothness overlaid with subtle grain (optional CSS noise) to mimic fabric texture.
- **Motion:** Kinetic but controlled. Movements should feel like athletic motion—snappy starts, smooth deceleration.
- **Imagery:** Hero-centric. Products are the protagonists; UI is the frame.

## **Design Token System**

### **Color Palette (Tailwind Mapping)**
| Token | Hex Value | Tailwind Utility | Usage |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#F8FAFC` | `bg-slate-50` | Main Background |
| `--bg-surface` | `#FFFFFF` | `bg-white` | Cards, Modals, Inputs |
| `--primary` | `#1E3A5F` | `text-slate-900` | Headings, Primary Text |
| `--secondary` | `#64748B` | `text-slate-500` | Body Text, Meta Data |
| `--accent-cta` | `#DC2626` | `bg-red-600` | Primary Actions, Alerts |
| `--accent-hover` | `#B91C1C` | `hover:bg-red-700` | CTA Hover State |
| `--border-subtle`| `#E2E8F0` | `border-slate-200` | Dividers, Input Borders |
| `--overlay` | `rgba(15, 23, 42, 0.5)` | `bg-slate-900/50` | Image Overlays |

### **Typography Scale (Major Third 1.250)**
*Base Size: 16px (1rem)*
| Level | Size (rem) | Size (px) | Line Height | Font Family | Weight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--text-xs` | 0.8rem | 12px | 1.5 | Inter | 400 |
| `--text-sm` | 1.0rem | 16px | 1.5 | Inter | 400 |
| `--text-base` | 1.25rem | 20px | 1.6 | Inter | 400 |
| `--text-lg` | 1.563rem | 25px | 1.4 | Inter | 500 |
| `--text-xl` | 1.953rem | 31px | 1.3 | Montserrat | 600 |
| `--text-2xl` | 2.441rem | 39px | 1.2 | Montserrat | 700 |
| `--text-3xl` | 3.052rem | 49px | 1.1 | Montserrat | 800 |

### **Radius & Borders**
- **UI Elements (Inputs/Buttons):** `6px` (`rounded-md`) - Precision feel.
- **Cards/Containers:** `12px` (`rounded-xl`) - Soft modern touch.
- **Images:** `4px` (`rounded-sm`) - Tight crop for performance look.
- **Pills/Tags:** `9999px` (`rounded-full`) - Athletic badge style.

### **Shadows (Elevation System)**
- **Level 1 (Rest):** `0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)` (`shadow-sm`)
- **Level 2 (Hover):** `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` (`shadow-md`)
- **Level 3 (Modal/Sticky):** `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` (`shadow-lg`)
- **Glow (CTA Focus):** `0 0 0 4px rgba(220, 38, 38, 0.2)` (`ring-4 ring-red-600/20`)

### **Textures (CSS)**
```css
.bg-grain {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none;
}
```

## **Component Stylings**

### **Buttons**
- **Primary CTA:** `bg-red-600 text-white font-semibold py-3 px-6 rounded-md transition-all duration-300 ease-out`.
- **Hover State:** `transform translateY(-2px) shadow-lg bg-red-700`.
- **Secondary:** `bg-transparent border border-slate-300 text-slate-700 hover:border-slate-900`.
- **Disabled:** `opacity-50 cursor-not-allowed bg-slate-200`.

### **Product Cards**
- **Container:** `bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300`.
- **Image Wrapper:** `relative aspect-square w-full overflow-hidden group`.
- **Image:** `object-cover w-full h-full transition-transform duration-700 ease-in-out group-hover:scale-110`.
- **Info:** `p-4 flex flex-col gap-2`.
- **Price:** `text-slate-900 font-bold text-lg`.
- **Title:** `text-slate-600 text-sm uppercase tracking-wide`.

### **Forms**
- **Input:** `w-full border border-slate-300 rounded-md px-4 py-3 focus:ring-2 focus:ring-red-600 focus:border-transparent outline-none transition-all`.
- **Label:** `block text-slate-700 text-sm font-medium mb-1`.
- **Error:** `border-red-600 focus:ring-red-600 text-red-600 text-xs mt-1`.

### **Layout Grid**
- **Desktop:** `grid grid-cols-12 gap-8`.
- **Tablet:** `grid grid-cols-6 gap-6`.
- **Mobile:** `grid grid-cols-1 gap-4`.
- **Container:** `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.

## **Effects & Animation**

### **Transitions**
- **Standard:** `transition-all duration-300 ease-[cubic-bezier(0.4, 0, 0.2, 1)]`.
- **Micro-interaction:** `duration-150 ease-in-out`.
- **Image Load:** `duration-700 ease-out`.

### **Scroll Animations**
- **Fade In Up:** `opacity-0 translate-y-4 animate-fade-in-up`.
- **CSS Keyframes:**
```css
@keyframes fade-in-up {
  to { opacity: 1; transform: translateY(0); }
}
```
- **Implementation:** Use Intersection Observer to trigger `opacity-100 translate-y-0`.

### **Loading States**
- **Skeleton:** `bg-slate-200 animate-pulse rounded-md`.
- **Image Placeholder:** `aspect-square bg-slate-100 animate-pulse`.

### **Parallax (Hero)**
- **Effect:** `transform translate-z-0` on container, `background-attachment: fixed` or JS-driven transform on scroll.
- **Constraint:** Disable on `prefers-reduced-motion`.

### **Sticky Mobile Bar**
- **Position:** `fixed bottom-0 left-0 right-0 z-50`.
- **Style:** `bg-white/90 backdrop-blur-md border-t border-slate-200 p-4`.
- **Visibility:** Show only when product scrolled out of viewport (JS toggle).

## **Accessibility & Bold Choices**

### **Technical Mandates (Stack Notes)**
1.  **Viewport:** `<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">`.
2.  **Images:** 
    -   Mandatory `aspect-square` class on product grids.
    -   Mandatory `srcset` and `sizes` attributes for responsive loading.
    -   Mandatory `loading="lazy"` for all images below the fold.
    -   Mandatory `alt` text describing material and color.
3.  **Overlays:** Use Tailwind opacity utilities (e.g., `bg-slate-900/50`) for text legibility over images.
4.  **Loading:** Use `animate-pulse` for skeleton states during data fetch.

### **Accessibility (A11y)**
-   **Contrast:** All text must meet WCAG AA (4.5:1). Primary Blue `#1E3A5F` on Slate-50 `#F8FAFC` passes.
-   **Focus:** Visible focus rings (`ring-2 ring-offset-2 ring-red-600`) on all interactive elements.
-   **Motion:** Respect `@media (prefers-reduced-motion: reduce)` by disabling parallax and scaling animations.
-   **Touch Targets:** Minimum `44px` height for all buttons and links on mobile.

### **Bold Choices**
-   **Typography Contrast:** Pairing geometric **Montserrat** (Headings) with neutral **Inter** (Body) creates a "Technical Manual" aesthetic.
-   **Whitespace:** Aggressive padding (`py-20` on sections) to emulate luxury gallery spacing.
-   **Color Accent:** Using **Red-600** sparingly (only for CTAs and critical alerts) to drive conversion without visual noise.
-   **Image Treatment:** No borders on images; hard crops (`aspect-square`) to enforce uniformity and performance focus.