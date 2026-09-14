---
name: design-taste-frontend
description: Anti-slop frontend skill for landing pages, portfolios, and redesigns. The agent reads the brief, infers the design direction, ships interfaces that do not look templated, and runs a strict mechanical pre-flight check before declaring done.
scope: Landing pages, portfolios, redesigns. NOT dashboards, data tables, or multi-step product UI. For those use Fluent UI, Carbon, Atlassian or Polaris (Section 2.A), and TanStack Table or AG Grid for data tables.
---

# Anti-Slop Frontend Skill

Every rule below is **contextual**. None of it fires automatically. Read the brief first, then pull only what fits.

## 0. BRIEF INFERENCE

Infer what the user actually wants before touching code. Most LLM design output is bad because the model jumps to a default aesthetic instead of reading the room.

**Read these signals first:**

1. **Page kind** - landing (SaaS / consumer / agency / event), portfolio (dev / designer / studio), redesign (preserve vs overhaul), editorial / blog.
2. **Vibe words** - "minimalist", "calm", "Linear-style", "Awwwards", "brutalist", "premium consumer", "Apple-y", "playful", "serious B2B", "editorial", "glassy", "dark tech".
3. **Reference signals** - linked URLs, pasted screenshots, named products, competing brands.
4. **Audience** - B2B procurement panel vs. design-conscious consumer vs. recruiter scanning a portfolio. The audience picks the aesthetic, not your taste.
5. **Existing brand assets** - logo, color, type, photography. For redesigns these are starting material, not optional input.
6. **Quiet constraints** - accessibility-first audiences, public-sector, regulated industries, trust-first commerce, kids' products. These OVERRIDE aesthetic preference.

**Emit a one-line Design Read before generating:**

> "Reading this as: \<page kind> for \<audience>, with a \<vibe> language, leaning toward \<design system or aesthetic family>."

**Ask exactly one question, and only when the read genuinely diverges.** Example: *"Closer to Linear-clean or Awwwards-experimental?"* Never a multi-question dump. If you can infer from context, do not ask - declare the read and proceed.

**Anti-default discipline.** Do not default to: AI-purple gradients, centered hero over dark mesh, three equal feature cards, glassmorphism on everything, infinite-loop micro-animations, Inter + slate-900. Reach past them deliberately, based on the read.

---

## 1. THE THREE DIALS

Set three dials after the design read. Every layout, motion, and density decision is gated by them.

* `DESIGN_VARIANCE: 8` - 1 = Perfect Symmetry, 10 = Artsy Chaos
* `MOTION_INTENSITY: 6` - 1 = Static, 10 = Cinematic / Physics
* `VISUAL_DENSITY: 4` - 1 = Art Gallery / Airy, 10 = Cockpit / Packed Data

**Baseline 8 / 6 / 4.** Use these unless the design read overrides. Do not ask the user to edit this file - overrides happen conversationally. These exact variable names are the global variables; never invent aliases like `LAYOUT_VARIANCE`.

### 1.A Dial inference (design read to dial values)

| Signal | VARIANCE | MOTION | DENSITY |
|---|---|---|---|
| minimalist / clean / calm / editorial / Linear-style | 5-6 | 3-4 | 2-3 |
| premium consumer / Apple-y / luxury / brand | 7-8 | 5-7 | 3-4 |
| playful / wild / Awwwards / experimental / agency | 9-10 | 8-10 | 3-4 |
| landing page / portfolio / marketing site (default) | 7-9 | 6-8 | 3-5 |
| trust-first / public-sector / regulated / a11y-critical | 3-4 | 2-3 | 4-5 |
| redesign - preserve | match existing | +1 | match existing |
| redesign - overhaul | +2 | +2 | match existing |

### 1.B What each dial means at its extremes

* **VARIANCE 1-3:** symmetrical 12-col grid, equal fr-units, equal padding, centered. **4-7:** `margin-top: -2rem` overlaps, mixed image aspect ratios, left-aligned headers over centered data. **8-10:** masonry, `grid-template-columns: 2fr 1fr 1fr`, `padding-left: 20vw`. **VARIANCE >= 4 above `md:` MUST collapse to strict single column (`w-full`, `px-4`, `py-8`) below 768px.**
* **MOTION 1-3:** no automatic animation, CSS `:hover` / `:active` only. **4-7:** `transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1)`, `animation-delay` cascades on load. **8-10:** scroll-triggered reveals, parallax, scroll-driven animation. `window.addEventListener('scroll')` stays banned at every level (Section 5).
* **DENSITY 1-3:** `py-32` to `py-48` section gaps. **4-7:** `py-16` to `py-24`. **8-10:** tight padding, no card boxes, 1px lines separate data, `font-mono` mandatory for all numbers.

---

## 2. BRIEF TO DESIGN SYSTEM MAP

Do not invent CSS for things that have an official package. Do not pretend an aesthetic trend is an official system.

### 2.A When to reach for a real design system

| Brief reads as | Reach for |
|---|---|
| Microsoft / enterprise SaaS | `@fluentui/react-components` or `@fluentui/web-components` |
| Google-ish, Material-flavored | `@material/web` + Material 3 tokens |
| IBM-style B2B analytics | `@carbon/react` + `@carbon/styles` |
| Shopify admin surfaces | `polaris.js` web components / Polaris React |
| Atlassian / Jira-style | `@atlaskit/*` + `@atlaskit/tokens` |
| GitHub-style devtool / community | `@primer/css` or `@primer/react-brand` |
| UK public-sector service | `govuk-frontend` (regulatorily expected) |
| US public-sector / trust-first | `uswds` |
| Fast local-business / agency MVP | Bootstrap 5.3 |
| Modern accessible React foundation | `@radix-ui/themes` |
| Modern SaaS where you own the components | shadcn/ui (`npx shadcn@latest add ...`) |
| Tailwind-based modern SaaS / AI marketing | Tailwind v4 utilities + `dark:` variant |

**Honesty rule:** if the brief reads as one of the systems above, install and use the **official** package. Do not recreate its CSS by hand. Do not import a system's tokens then override 90% of them. shadcn/ui is allowed but **never in default state** - customize radii, colors, shadows, typography to the project aesthetic.

**One system per project.** Never mix Fluent with Carbon in the same tree. Never import shadcn/ui components into a Material 3 app.

### 2.B When the brief is an aesthetic, not a system

No single official package exists. Build with native CSS + Tailwind + a maintained component library, and be honest in comments about borrowed inspiration vs. official material. Glassmorphism = `backdrop-filter` + layered borders + highlight overlays, with a solid-fill fallback under `prefers-reduced-transparency`. Bento = CSS Grid with mixed cell sizes. Brutalism = native CSS, monospace, raw borders. Editorial = serif type, asymmetric grid, generous whitespace. Aurora / mesh = SVG or layered radial gradients. Kinetic type = native CSS + scroll-driven animations, GSAP only for hijacks.

**Apple Liquid Glass:** Apple documents this for Apple platforms only. **There is no official `liquid-glass.css`.** Any web implementation is an approximation through `backdrop-filter` + layered borders + highlights. Label it clearly as an approximation.

---

## 3. DEFAULT ARCHITECTURE & CONVENTIONS

Unless the design read picks a real design system (2.A), these are the defaults.

### 3.A Stack

* **Framework:** React or Next.js, defaulting to Server Components (RSC). Global state works ONLY in Client Components; in Next.js wrap providers in a `"use client"` component. Any component using Motion, scroll listeners, or pointer physics MUST be an isolated leaf with `'use client'` at the top. Server Components render static layouts only.
* **Styling:** Tailwind v4 (default); v3 only if the existing project demands it. For v4, do NOT use the `tailwindcss` plugin in `postcss.config.js` - use `@tailwindcss/postcss` or the Vite plugin.
* **Animation:** Motion (formerly Framer Motion), imported from `motion/react`. `framer-motion` still works as a legacy alias; prefer `motion/react` in new code.
* **Fonts:** `next/font`, or self-host with `@font-face` + `font-display: swap`. Never link Google Fonts via `<link>` in production.

### 3.B State

Local `useState` / `useReducer` for isolated UI. Global state (Zustand, Jotai, React context) ONLY to avoid deep prop-drilling. **NEVER** use `useState` for continuous values driven by user input (mouse position, scroll progress, pointer physics, magnetic hover) - use `useMotionValue` / `useTransform` / `useScroll`. `useState` re-renders the tree on every change and collapses on mobile.

### 3.C Icons

Allowed, in priority order: `@phosphor-icons/react`, `hugeicons-react`, `@radix-ui/react-icons`, `@tabler/icons-react`. **Discouraged:** `lucide-react` (only on explicit request or existing dependency). **NEVER hand-roll SVG icons** - install a second library or compose from primitives. One family per project; do not mix Phosphor with Lucide in the same tree. Standardize `strokeWidth` globally.

### 3.D Emoji policy

Discouraged by default in code, markup, and visible text - replace symbols with icon-library glyphs. Override only when the user explicitly asks for a playful / chat-style / social-native vibe, and even then sparingly.

### 3.E Responsiveness & layout mechanics

* Standardize breakpoints: `sm 640`, `md 768`, `lg 1024`, `xl 1280`, `2xl 1536`.
* Contain page layouts with `max-w-[1400px] mx-auto` or `max-w-7xl`.
* **Viewport stability:** NEVER `h-screen` for full-height heroes. ALWAYS `min-h-[100dvh]` (iOS Safari address bar causes layout jump).
* **Grid over flex-math:** NEVER `w-[calc(33%-1rem)]`. ALWAYS CSS Grid (`grid grid-cols-1 md:grid-cols-3 gap-6`).
* **Mobile collapse must be declared per section**, in the same component, for every multi-column layout. No "Tailwind handles it" assumptions.

### 3.F Dependency verification (mandatory)

Before importing ANY third-party library, check `package.json`. If the package is missing, output the install command first. **Never** assume a library exists.

---

## 4. HARD LOCKS (violating any of these is shipping broken work)

### 4.1 Color

* **Max 1 accent color.** Saturation below 80% by default. Neutral bases (Zinc / Slate / Stone) with one high-contrast accent.
* **THE LILA RULE:** the AI-purple / blue-glow aesthetic is banned as a default - no automatic purple button glows, no random neon gradients. Override only when the brand explicitly asks for purple and you execute with intent (consistent palette, harmonised neutrals, restrained gradients).
* **COLOR CONSISTENCY LOCK:** once an accent is chosen it is used on the WHOLE page. A warm-grey site does not get a blue CTA in section 7. A rose site does not get a teal badge in the footer. Audit every component before shipping.
* **One palette per project** - do not fluctuate between warm and cool grays.
* **PREMIUM-CONSUMER PALETTE BAN (second-most-recurring AI tell).** For cookware / wellness / artisan / luxury / heritage craft / DTC home briefs the default reach is warm beige + brass + espresso. Banned as a default: backgrounds in the `#f5f1ea #f7f5f1 #fbf8f1 #efeae0 #ece6db #faf7f1 #e8dfcb` family, accents in the `#b08947 #b6553a #9a2436 #9c6e2a #bc7c3a #7d5621` family, text in the `#1a1714 #1a1814 #1b1814` family. **Rotate instead:** Cold Luxury (silver-grey + chrome + smoke), Forest (deep green + bone + amber), Black and Tan (off-black + warm tan, no beige), Cobalt + Cream, Terracotta + Slate, Olive + Brick + Paper, or pure monochrome + one saturated pop. If your last premium-consumer project used beige + brass, this one MUST use a different family. Override only when the brief names those colors or the brand is genuinely vintage / warm-craft and you can articulate why.

### 4.2 Shape, elevation, cards

* **SHAPE CONSISTENCY LOCK:** pick ONE corner-radius scale for the page and stick to it - all-sharp (0), all-soft (12-16px), or all-pill. Mixed systems are allowed only with a documented rule ("buttons full-pill, cards 16px, inputs 8px") followed everywhere.
* Use cards ONLY when elevation communicates real hierarchy. Otherwise group with `border-t`, `divide-y`, or negative space.
* When a shadow is used, tint it to the background hue - no pure-black drop shadows on light backgrounds.
* For `VISUAL_DENSITY > 7`: generic card containers are banned. Data metrics breathe in plain layout.

### 4.3 States and contrast (all mandatory)

* **Full state cycles are required**, not "static success state only": skeleton loaders matching the final layout shape (not generic spinners), composed empty states that show how to populate, clear inline error states (toasts only for transient), and tactile `:active` feedback (`-translate-y-[1px]` or `scale-[0.98]`).
* **BUTTON CONTRAST CHECK:** verify button text is readable against the button background. `bg-white` CTA with a `text-white` label, and transparent buttons with no border over the page background, are both banned. WCAG AA minimum (4.5:1 body, 3:1 large text at 18px+). Ghost buttons over photography need a backdrop, scrim, or stroke.
* **CTA WRAP BAN:** CTA labels MUST fit one line at desktop. If a label wraps, either shorten it (3 words max for primary CTAs, ideally 1-2) or widen the button - do not constrain `max-width` on CTAs. A wrapped desktop CTA is a Pre-Flight Fail.
* **NO DUPLICATE CTA INTENT:** two CTAs with the same intent on one page is a Pre-Flight Fail. "Get in touch" + "Let's talk" + "Start a project" are all contact intent - pick ONE label and use it everywhere (nav, hero, footer). Same for signup intent and portfolio intent.
* **FORM CONTRAST CHECK:** inputs, placeholders, focus rings, helper text, and error text all pass WCAG AA against the section background. Light placeholders on near-white forms, white forms on white sections, and labels below 4.5:1 are banned.
* **Forms:** label ABOVE input, error text BELOW, `gap-2` for input blocks. **No placeholder-as-label. Ever.**

### 4.4 Hero

* **Hero MUST fit the initial viewport.** Headline max 2 lines desktop, subtext max **20 words** AND max 3-4 lines, CTAs visible without scroll. If copy is too long, reduce font scale or cut copy. If you cannot state the value prop in 20 words, the value prop is unclear - not the rule too tight.
* **Plan font scale and image size together.** Default `text-4xl md:text-5xl lg:text-6xl`; `text-6xl md:text-7xl` only when the headline is 3-5 words. A 4-line hero headline is always a font-size error, never a copy-length error.
* **TOP PADDING CAP:** hero top padding max `pt-24` at desktop. More reads as a layout bug, not intentional space. Need more air? Increase font or asset size, not padding.
* **HERO STACK DISCIPLINE - max 4 text elements**, from: (1) eyebrow OR brand strip OR neither - pick zero or one, (2) headline, (3) subtext, (4) 1 primary + max 1 secondary CTA. **BANNED inside the hero:** tagline below the CTAs, trust micro-strip, pricing teaser, feature bullet list, social-proof avatar row. All of those belong in sections directly below.
* **"Used by" / "Trusted by" logo wall belongs UNDER the hero, never inside it.**
* **Hero needs a real visual.** Text plus a gradient blob is a placeholder, not a hero.

### 4.5 Navigation

* **Must render on a single line at desktop.** If items do not fit at `lg` (1024px), condense labels, drop secondary items, or move to a hamburger. A two-line desktop nav is broken.
* **Height cap 80px desktop, default 64-72px.** No agency nav bars eating 15% of the viewport.

### 4.6 Page-level composition

* **SECTION-LAYOUT-REPETITION BAN.** Once a layout family is used for a section (3-column image cards, full-width quote, split text-image), that family appears at most ONCE per page. A page with 8 sections must use at least 4 different layout families.
* **ZIGZAG ALTERNATION CAP.** Max 2 consecutive sections with the left-image/right-text zigzag. The 3rd consecutive image+text split is a Pre-Flight Fail - break it with a full-width section, vertical stack, bento grid, marquee, or another family.
* **BENTO CELL COUNT RULE.** A bento grid has EXACTLY as many cells as you have content for. 3 items = 3 cells. 5 items = 5 cells. An empty cell in the middle or at the end means you planned wrong - re-shape the grid, never paste a blank tile.
* **BENTO BACKGROUND DIVERSITY.** At least 2-3 cells in any multi-cell grid need real visual variation (a real image, a non-AI-purple gradient, a pattern, a tinted background). Six white-on-white text cards read as AI default even when the rest of the page is good.
* **ANTI-CENTER BIAS:** centered hero / H1 sections are avoided when `DESIGN_VARIANCE > 4`. Force split-screen (50/50), left-content/right-asset, asymmetric whitespace, or scroll-pinned structure. Override for editorial / manifesto / launch briefs where the message IS the design.
* **PAGE THEME LOCK.** The page has ONE theme; sections do not invert. No light warm-paper section sandwiched between dark sections. Section-level tints within the same family are fine (`bg-zinc-950` next to `bg-zinc-900`); flipping to `bg-amber-50` mid-page is broken. Exception: one deliberate full theme switch with a strong transition, once per page. With a themed design system (Radix Themes, shadcn/ui `<Theme>`), set the theme ONCE in `layout.tsx` or the page root - sections never override.

### 4.7 The eyebrow rule (the #1 violated rule in production tests)

An "eyebrow" is the small uppercase wide-tracking label above a section headline (`FOUR COLORWAYS`, `SELECTED WORK`). CSS signature: `text-[11px] uppercase tracking-[0.18em]` or `font-mono text-[10.5px] uppercase tracking-[0.22em]`. Every AI-built site puts one above EVERY section, producing a templated rhythm.

* **Maximum 1 eyebrow per 3 sections.** Hero counts as 1. A 9-section page may use at most 3 eyebrows total.
* If section A has an eyebrow, the next 2 sections cannot have one.
* **Mechanically checked:** count `uppercase tracking` instances across section components. If count > `ceil(sectionCount / 3)`, the output fails.
* **What to do instead:** drop it. The headline alone is enough. A section's position on the page already categorizes it.

### 4.8 Split-header ban

The pattern "left big headline + right small explainer paragraph" as a section header is **banned as default**. Sections carry ONE focused message. If you genuinely need both, stack them vertically (headline above, body below, max-width 65ch). Reach for the split header only when the right column carries a real visual or interactive element, not filler text.

### 4.9 Content density

Landing pages live on the **first impression**, not the full read. Cut ruthlessly.

* **Default shape per section:** headline <= 8 words + sub-paragraph <= 25 words + one visual asset OR one CTA. Anything more must be justified by the section's job.
* **No data-dump sections.** A 20-row table or giant pricing matrix on a marketing page is the wrong layout. Use top 3-5 highlights + "View full list", a marquee for breadth, or a different page if the data is the product.
* **Long lists need a different UI component, not a longer list.** Default `<ul>` with `divide-y` is the lazy choice. Above 5 items use a 2-column split with grouped items, a card grid, tabs / accordion, horizontal scroll-snap pills, a carousel, or a marquee. **A 10-row spec table with a hairline under every row is the WORST default.** For spec sheets, use a 2-col card grid (spec name + large display value + one-line "why it matters"), scroll-snap pills, 3 grouped clusters with one divider each, or 3-4 featured tiles with the rest behind a disclosure.
* **One copy register per page.** Do not mix technical mono, editorial prose, and marketing punch unless the brand voice calls for it.
* **Fake-precise numbers are flagged.** Numbers come from real data, or are explicitly labeled mock, or are banned. Do not fake engineering precision the brand does not claim.
* **COPY SELF-AUDIT (before ship):** re-read every visible string - headlines, eyebrows, button labels, body, captions, alt text, footer, errors. Rewrite anything grammatically broken, with unclear referents, that sounds like AI hallucination, or that reads like an LLM trying to sound thoughtful (mock-poetic micro-meta, fake-craftsman labels). If unsure, replace with a plain functional sentence. AI-generated cute copy is worse than boring copy.
* **Quotes:** max 3 lines of body, never 6; cut the original rather than overflow. Attribution = name + role + optional company, never name only. Use real typographic quotes or none. No em-dash flourishes (4.11).

### 4.10 Images and visual assets

Landing pages and portfolios are **visual products**. Text-only pages with fake-screenshot divs are slop.

**Priority order:**
1. **Image-generation tool first.** If ANY image-gen tool exists in the environment, you MUST use it for section-specific assets (hero photography, product shots, texture backgrounds, mood images) at the right aspect ratio per section. Do not skip because hand-rolled CSS feels faster.
2. **Real web images second.** `https://picsum.photos/seed/{descriptive-seed}/{w}/{h}` with a section-describing seed, brand-provided URLs, or open-license sources if allowed.
3. **Last resort: tell the user.** Never fill the page with hand-rolled SVG illustrations or div-based fake screenshots. Leave labeled slots (`<!-- TODO: hero product photo, 1600x1200 -->`) and list every needed image placement in your final response.

**Even minimalist sites need real images.** A pure-text page is not minimalism, it is incomplete work. A restrained Linear-style site still needs 2-3 real images - generate B&W minimalist photography rather than skip them.

**Real logos for social proof.** Never plain text wordmarks in a row. Use Simple Icons (`https://cdn.simpleicons.org/{slug}/ffffff` or the npm package) or devicon for tech stacks. For invented brand names, generate a simple SVG monogram matching the page style. Ensure logos render in both light and dark mode. **LOGO-ONLY rule:** logos and nothing else - never print industry labels below them.

**Hand-rolled decorative SVGs are strongly discouraged**, never a default. Acceptable only when explicitly requested, or for a single simple geometric mark you are confident in.

**Div-based fake screenshots are banned.** A fake product UI built from `<div>` rectangles, fake task lists, fake terminals is the #1 LLM design tell. Show a real screenshot URL, a generated image, a real component preview, or editorial photography instead.

### 4.11 Em-dash ban (the single most-violated tell)

**Em-dash (`—`) is COMPLETELY banned.** No "limited use" allowance, no "natural language frequency" allowance, no "body copy is fine" allowance.

Banned in headlines, eyebrows, labels, pills, button text, image captions, nav items, body copy, and quote attribution. En-dash (`–`) is banned as a separator too - date and number ranges use a hyphen (`2018-2026`, `€40-80k`).

The ONLY permitted dash characters on the page are the regular hyphen `-` (compounds, ranges, markup dividers) and the minus sign in math (`-5°C`). A single visible `—` or `–` fails the Pre-Flight Check and must be rewritten.

This rule is binary because the agent has historically ignored it when phrased as "use sparingly."

---

## 5. MOTION DISCIPLINE

Kept tight on purpose - motion is where scope creep happens. Everything here is mandatory.

* **Motion must be motivated.** Before adding any animation, answer "what does this communicate?" Valid: hierarchy, storytelling, feedback, state transition. Invalid: "it looked cool." If you cannot articulate the reason in one sentence, drop the animation.
* **"Motion claimed, motion shown."** If `MOTION_INTENSITY > 4` the page must actually move (hero entry transitions, scroll-reveal on key sections, hover physics on CTAs). A static page claiming `MOTION_INTENSITY: 7` is broken. If you cannot ship working motion in scope, drop the dial to 3 and ship a clean static page. Never half-build motion that breaks (cut-off ScrollTriggers, jumpy enters, missing cleanups).
* **`window.addEventListener("scroll", ...)` is BANNED.** Also banned: custom scroll progress from `window.scrollY` in React state, and `requestAnimationFrame` loops touching React state. Use Motion's `useScroll()`, GSAP ScrollTrigger, IntersectionObserver, or CSS `animation-timeline: view()`.
* **Marquee: max ONE per page.** Two or more horizontal scrolling text marquees reads as lazy filler.
* **Sticky-stack and horizontal-pan pitfalls.** A "card stack on scroll" must be a REAL sticky-stack, not a sequential reveal list. Both patterns fail in the same way: the trigger fires midway instead of at the viewport top. Fix with `start: "top top"` (not `"top center"` or `"top 80%"`), `pin: true` on the wrapper, scrub the inner track, and set `end: "+={trackWidth - viewportWidth}"` for horizontal pan. Every pinned section except the last needs its own trigger; drive the shrink of card N from card N+1's scroll trigger. Prefer Motion's `whileInView` with `viewport={{ once: true }}` for simple enter-on-scroll - save GSAP for actual pin/scrub work.
* **Use Motion's `layout` / `layoutId`** for visible state changes (list re-ordering, expanding modals, shared elements). Do not wrap static content in `layout` "for safety" - it costs measurement work. For staggered reveals where order matters, use `staggerChildren` (parent and children must share the same Client Component tree) or CSS `animation-delay: calc(var(--index) * 100ms)`.
* **Spring physics, not linear.** `type: "spring", stiffness: 100, damping: 20`. In CSS: `cubic-bezier(0.16, 1, 0.3, 1)`.

---

## 6. PERFORMANCE & ACCESSIBILITY GUARDRAILS

* **Animate ONLY `transform` and `opacity`.** Never `top`, `left`, `width`, `height`. Apply `will-change: transform` sparingly - only on elements that actually animate.
* **Reduced motion (mandatory).** Anything above `MOTION_INTENSITY > 3` MUST honor `prefers-reduced-motion`. In Motion, wrap with `useReducedMotion()` and degrade to static. In CSS, gate behind `@media (prefers-reduced-motion: no-preference)` or override under `reduce`. Infinite loops, parallax, scroll-hijack, and magnetic physics MUST collapse to static / instant.
* **Dark mode is mandatory for any consumer-facing page.** Design both modes from the start; never ship single-mode without explicit instruction. Respect `prefers-color-scheme` by default. Maintain hierarchy parity across modes - if a CTA pops in light it pops in dark - and keep the brand color recognisable. **No pure `#000000` and no pure `#ffffff`** - pure values kill depth. Test in both modes before finishing; never ship a page you have only seen in one mode.
* **Token strategy: pick one and stick to it.** Tailwind `dark:` variant (`bg-white dark:bg-zinc-950`), or CSS variables with semantic tokens (`--surface`, `--surface-elevated`, `--text-primary`, `--accent`) swapped under `[data-theme="dark"]` / `prefers-color-scheme`. Do not prescribe specific colors here - the brief and brand decide. Contrast: WCAG AA minimum for body, AAA target for hero copy.
* **Core Web Vitals:** LCP < 2.5s (hero image `next/image priority` or preloaded), INP < 200ms, CLS < 0.1 (reserve space for images, fonts, embeds). Run Lighthouse before declaring a page done.
* **Grain / noise filters EXCLUSIVELY** on fixed `pointer-events-none` pseudo-elements (`fixed inset-0 z-[60] pointer-events-none`), NEVER on scrolling containers - continuous GPU repaints destroy mobile FPS. Lazy-load anything not above the fold.
* **Z-index restraint.** Never spam `z-50` / `z-10`. Use z-index strictly for systemic layers (sticky navbars, modals, overlays, grain) and document the scale in a project constants file.

---

## 7. AI TELLS (forbidden patterns)

### 7.A Visual, type, layout

* **NO neon / outer glows** by default - inner borders or subtle tinted shadows.
* **NO pure black** (`#000000`) - off-black, zinc-950, or charcoal.
* **NO oversaturated accents.** **NO excessive gradient text** on large headers. **NO custom mouse cursors** (outdated, a11y-hostile, perf-hostile).
* **NO oversized H1s** that just scream - control hierarchy with weight and color, not raw scale. **AVOID Inter as a default** (Section 4.1 override path exists).
* **Serif discipline.** Serif is very discouraged as a default. "It feels creative / premium / editorial" is not a reason - the reflex "creative brief = serif" is one of the most-tested AI tells. Serif is acceptable only when the brief names a serif, or the family is genuinely editorial / luxury / publication / manuscript / heritage AND you can articulate why this serif fits this brand. Otherwise default to sans display (Geist Display, ABC Diatype, Söhne Breit, Cabinet Grotesk Display, GT Walsheim, PP Neue Montreal). **Banned as defaults:** `Fraunces`, `Instrument_Serif`. If a serif is justified, do not reuse the same one across consecutive projects.
* **Emphasis rule:** to emphasize a word inside a headline, use **italic or bold of the SAME font**. Injecting a serif word into a sans headline (or vice versa) is amateur.
* **Italic descender clearance:** with italic display type, `leading-none` / `leading-[1]` clips `y g j p q` descenders. Use `leading-[1.1]` minimum plus `pb-1` reserve on the wrapper, and audit every italic display word before shipping.
* **NO 3-column equal feature cards.** The generic three-identical-cards row is banned - use 2-col zig-zag, asymmetric grid, scroll-pinned, or horizontal scroll.
* **Mathematically consistent** padding and margins. No floating elements with awkward gaps.

### 7.B Content and data ("Jane Doe" effect)

* **NO generic names** ("John Doe", "Sarah Chan") - use realistic, locale-appropriate names.
* **NO generic avatars** (SVG eggs, Lucide user icons) - believable photo placeholders or specific styling.
* **NO fake-perfect numbers** (`99.99%`, `50%`, `1234567`) - use organic, messy data (`47.2%`, `+1 (312) 847-1928`).
* **NO startup-slop brand names** ("Acme", "Nexus", "SmartFlow", "Cloudly") - invent contextual, premium names that sound real.
* **NO filler verbs** ("Elevate", "Seamless", "Unleash", "Next-Gen", "Revolutionize").
* **NO hand-rolled SVG icons.** Use Phosphor / HugeIcons / Radix / Tabler; Lucide only on explicit request.
* **NO broken Unsplash links** - use `picsum.photos/seed/...`, generated placeholders, or real assets.

### 7.C Production-test tells (banned outright)

These came out of real LLM landing-page tests, not theory. Treat as hard bans unless the brief explicitly calls for them.

**Hero and top-of-page**
* **NO version labels in the hero** (`V0.6`, `v2.0`, `BETA`, `INVITE-ONLY PREVIEW`, `EARLY ACCESS`) as default eyebrows. Only when the brief is explicitly a launch or preview.
* **NO "Brand · No. 01"-style sub-eyebrows.**
* **NO section-number eyebrows** (`00 / INDEX`, `001 · Capabilities`, `06 · how it works`). Name the topic in plain language, do not enumerate.
* **NO `01 / 4`-style pagination** on images or bento tiles. If the user can count, they do not need the label.
* **NO "Index of Work, 2018 - 2026"-style range labels** as eyebrows.
* **NO decoration text strip at the hero bottom** (`BRAND. MOTION. SPATIAL.`, `TYPE / FORM / MOTION`). Agency-portfolio cliché. Only acceptable when it carries real navigable links or real status info.
* **NO scroll cues.** `Scroll`, `↓ scroll`, `Scroll to explore`, animated mouse-wheel icons. The user knows what scroll is.
* **NO floating top-right sub-text** in section headings - that tiny corner paragraph is the tell. Put the sub-text under the headline, or build a clean aligned 2-column header.

**Separators, dots, decoration**
* **The middle-dot (`·`) is rationed** - maximum 1 per line in metadata strips. Not the default separator for everything.
* **ZERO decorative status dots by default.** A colored dot before nav items, list rows, badges, or status labels is a tell. Only for real semantic state (live server status, real availability flag), max one per page section.
* **NO crosshair / hairline grid lines as decoration.** Only when they organize real content.
* **NO vertical rotated text** ("INDEX OF WORK" rotated 90°). Agency cliché; only when the brief is explicitly Awwwards-experimental and it serves a real composition purpose.
* **NO `<br>`-broken-and-italicized headlines** ("for thirty<br>*years.*"). Headlines read naturally first; get clever only when the brief demands it.

**Labels, captions, stamps**
* **NO pills / tags overlaid on images** (`Brand · 02`, `PLATE · BRAND`, `Field notes - journal`). Either let the image speak or add a caption below it, outside the frame.
* **NO photo-credit captions as decoration** (`Field study no. 12 · Ines Caetano`, `Plate 03 · House archive`). Allowed only for a real photographer on a real photo with permission.
* **NO version footers on marketing pages** (`v1.4.2`, `Build 0048`, `last sync 4s ago · main`). Those are devtool fixtures.
* **NO live-stock counters as decoration** ("Reservation 412 of 800") unless it is a real limited-run waitlist.
* **NO scoring / progress bars with filled background tracks** as comparison visuals. Use a number plus a small icon, or a tiny inline bar with no track.

**Copy and locale**
* **NO "Quietly in use at" / "Quietly trusted by"** social-proof headers. Use "Trusted by", "Used at", "Customers include", or no heading at all.
* **NO poetic section labels** ("From the field", "Field notes", "Currently on the bench", "On our desks"). Reads as performative-craftsman. Use plain functional labels or none.
* **NO mock-humble industry references** ("We respect the French ones") in body copy.
* **NO locale / city / time / weather strips** ("Lisbon 14:23 · 18°C", "1200-690 Lisbon, Portugal" in the footer). Banned for 99% of briefs - allowed only for a genuinely timezone-distributed studio, a travel brand, or a real physical venue. A single contact address in the footer is fine; an atmospheric locale strip is not.
* **NO micro-meta-sentences under eyebrows** ("Each of these is a feature we ship today, not a roadmap promise..."). Eyebrow + headline + body is enough.
* **NO generic step labels** ("Stage 1 / Stage 2", "Step 1 / Step 2", "Phase 01"). The step content is the label - use the verb-noun directly ("Install", "Configure", "Ship").
* **NO `border-t` + `border-b` on every row** of a long list or spec table. Pick one and use it sparsely (see Section 4.9).

---

## 8. THE BLOCK LIBRARY (contract)

Reusable page sections are implemented under `skills/taste-skill/blocks/`, one file per block:

```
blocks/
  hero/            asymmetric-split.md, editorial-manifesto.md, kinetic-type.md, ...
  feature/         bento-grid.md, sticky-scroll-stack.md, zig-zag.md, ...
  social-proof/  pricing/  cta/  footer/  navigation/  portfolio/  transition/
```

Do not freelance new blocks outside this schema. Required frontmatter:

```yaml
---
name: asymmetric-split-hero
category: hero
dial_compatibility:
  variance: [6, 10]
  motion: [3, 10]
  density: [2, 5]
when_to_use: "Landing pages with one strong asset and one strong message."
not_for: "Editorial / manifesto launches where the message IS the design."
stack: ["react", "next", "tailwind", "motion"]
---
```

Required body sections: (1) visual sketch, (2) props API, (3) minimal working code sketch (Server Component default, `'use client'` island for motion), (4) explicit mobile fallback below 768px, (5) one motion variant per `MOTION_INTENSITY` band with an explicit reduced-motion fallback, (6) dark-mode token notes, (7) anti-patterns, (8) links to real production examples.

**Discipline:** one block per file, no multi-block files. Every block renders standalone when dropped into a page. Every block passes the Pre-Flight Check (Section 9). Blocks that depend on a design system live under `blocks/<category>/<name>--<system>.md`.

---

## 9. FINAL PRE-FLIGHT CHECK

Run this matrix before outputting code. It is the last filter and it is **not optional** - run every line, and if any line fails the output is not done.

**Brief and direction**
- [ ] One-line **Design Read** declared, and **dial values** explicit and reasoned from the brief (not silently baselined)?
- [ ] **Design system** chosen from Section 2.A if applicable, or the aesthetic labeled honestly as an aesthetic?
- [ ] **One** design system per project - nothing mixed (Material + shadcn = fail)?

**Locks**
- [ ] **Em-dash count = 0.** Zero `—` and zero `–` anywhere visible: headlines, eyebrows, pills, body, quotes, attribution, captions, buttons, alt text, nav.
- [ ] **Page theme lock** - ONE theme for the whole page, no section flipping to inverted mode mid-page?
- [ ] **Color consistency lock** - one accent color, used identically across all sections?
- [ ] **Shape consistency lock** - one corner-radius system applied consistently, or a documented mixed rule followed everywhere?
- [ ] **Palette check** - if premium-consumer, the palette is NOT the beige + brass + oxblood + espresso family, and is a different family from your previous premium-consumer project?
- [ ] **Serif check** - if a serif is used, it is justified (brief names it, or genuinely editorial / luxury), it is NOT Fraunces or Instrument_Serif, and it differs from your previous project?

**Contrast and CTAs**
- [ ] **Button contrast** - every CTA label is readable against its background (WCAG AA 4.5:1; no white-on-white)?
- [ ] **CTA wrap** - no CTA label wraps to 2+ lines at desktop?
- [ ] **No duplicate CTA intent** - each intent (contact / signup / portfolio / buy) has exactly ONE label used everywhere?
- [ ] **Form contrast** - inputs, placeholders, focus rings, labels, and error text all pass WCAG AA against the section background?

**Hero**
- [ ] **Hero fits the viewport** - headline <= 2 lines, subtext <= 20 words AND <= 4 lines, CTA visible without scroll?
- [ ] **Hero top padding** <= `pt-24` at desktop (content does not float halfway down)?
- [ ] **Hero stack** <= 4 text elements, with no tagline, trust strip, pricing teaser, bullet list, or avatar row inside it?
- [ ] **Logo wall** sits UNDER the hero (not inside), uses real SVG logos (Simple Icons / devicon / generated monogram), NOT plain text wordmarks, and carries NO industry labels below the logos?
- [ ] **Hero has a real image** - no text + gradient blob?

**Composition**
- [ ] **Eyebrow count (mechanical):** count `uppercase tracking` micro-labels above section headlines. Count <= `ceil(sectionCount / 3)`, hero counted as 1?
- [ ] **Split-header ban** - no "left big headline + right small explainer paragraph" as a section header?
- [ ] **Zigzag cap** - no 3+ consecutive sections with the same image+text-split layout?
- [ ] **Section-layout repetition** - no two sections share a layout family; 8 sections means at least 4 different families?
- [ ] **Bento** - exact cell count for the content (no empty cells mid-grid or at the end) AND at least 2-3 cells with real visual variation (image, non-AI-purple gradient, pattern)?
- [ ] **Navigation** on ONE line at desktop, height <= 80px?
- [ ] **Mobile collapse** declared explicitly (`w-full`, `px-4`, `max-w-7xl mx-auto`) for every high-variance layout?
- [ ] **Viewport stability** - `min-h-[100dvh]`, never `h-screen`?

**Content**
- [ ] **Copy self-audit** - every visible string re-read; no grammatically broken, hallucinated, or mock-poetic text shipped?
- [ ] **Content density** sane - no 20-row data tables, no fake-precise specs, sub-paragraphs <= 25 words by default?
- [ ] **Long lists** (> 5 items) use a real UI component, not default `<ul>` with `divide-y`; no `border-t` + `border-b` on every row?
- [ ] **Quotes** <= 3 lines of body, attribution clean (name + role), no em-dash?
- [ ] **Real images used** - image-gen tool first, then picsum seeds, then explicit labeled placeholder slots. NO div-based fake screenshots, NO hand-rolled decorative SVGs, NO pure-text minimalism?
- [ ] **Icons** from an allowed library only (Phosphor / HugeIcons / Radix / Tabler) - no hand-rolled SVG paths, one family per project?

**Motion and performance**
- [ ] **Motion motivated** - every animation justifiable in one sentence (hierarchy / storytelling / feedback / state transition)?
- [ ] **Motion claimed = motion shown** - if `MOTION_INTENSITY > 4`, the page actually animates?
- [ ] **No `window.addEventListener('scroll')`** - using `useScroll()` / ScrollTrigger / IntersectionObserver / CSS scroll-driven animations only?
- [ ] **Sticky-stack / horizontal-pan** use `start: "top top"` + `pin: true` + correct scrub/end distance?
- [ ] **Reduced motion** wrapped for everything above `MOTION_INTENSITY > 3`?
- [ ] **Motion isolated** in client-leaf components with `'use client'` at the top, memoized, with strict `useEffect` cleanups?
- [ ] **Animate `transform` / `opacity` only**; grain / noise on fixed `pointer-events-none` layers, not scrolling containers?
- [ ] **Dark mode** tokens defined and tested in both modes; no pure `#000` or `#fff`?
- [ ] **States** - empty, loading, and error states provided?
- [ ] **Core Web Vitals** plausibly hit (LCP < 2.5s, INP < 200ms, CLS < 0.1)?

If a single box cannot be honestly ticked, the page is not done. Fix it before delivering.
