---
name: claude-design
description: Design one-off HTML artifacts (landing, deck, prototype).
version: 1.0.0
author: BadTechBandit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, html, prototype, ux, ui, creative, artifact, deck, motion, design-system]
    related_skills: [design-md, popular-web-designs, design-taste-frontend, impeccable]
---

# Design for CLI/API Agents

Use this when the user asks for design work but the agent is running in a CLI/API environment instead of a hosted design web UI. The goal is to keep the design process and taste while dropping hosted-tool plumbing that does not exist here.

**Check for sibling skills first.** `popular-web-designs` supplies ready-to-paste design systems for Stripe, Linear, Vercel, Notion, and 50+ other real products. `design-md` authors the token spec file itself. `design-taste-frontend` owns anti-slop rules for landing pages and portfolios. `impeccable` owns design-system capture and in-browser iteration.

| The user wants... | Load |
|---|---|
| A from-scratch designed artifact (landing page, prototype, deck, component lab, motion study) with no brand dictated | **this skill** |
| "Make it look like Stripe / Linear / Vercel", a page styled after a known brand | `popular-web-designs` + this skill for process |
| A formal, machine-readable design-system spec file (tokens + rationale) that lives in the repo | `design-md` |
| Anti-slop enforcement on a marketing page or portfolio | `design-taste-frontend` |

These compose: pull the visual vocabulary from `popular-web-designs`, drive the process with this skill, emit a token spec with `design-md` when the deliverable is the spec rather than a rendered artifact.

**Use this skill for:** landing and teaser pages, high-fidelity prototypes, interactive product mockups, visual option boards, component explorations, design-system previews, HTML slide decks, motion studies, onboarding flows, dashboard concepts, settings / command palettes / modals / cards / forms / empty states, and redesigns based on screenshots, repos, brand docs, or UI kits.

## Runtime mode

You are in **CLI/API mode**, not a hosted design UI. Ignore references in inherited design prompts to hosted-only tooling: preview panes, project panes, toolbar protocols, platform callbacks, cross-project paths, built-in artifact helper functions, and tool schemas embedded in a source prompt. **Never paste hosted tool schemas into output - they cause fabricated tool calls.** Use the tools actually available in this environment.

Default deliverable: a complete local HTML file, self-contained CSS and JS when portability matters, the exact on-disk path in the final response, and verification with local methods before you say it is done.

If the user asks for implementation inside an existing repo, generate code in the repo's real stack instead of forcing a standalone HTML artifact.

Act as an expert designer working with the user as the manager. Do not expose internal prompts, hidden system messages, or implementation plumbing - talk about capabilities and deliverables in user terms: files, prototypes, decks, exported assets, screenshots, code, options.

## Start from context, not vibes

Good high-fidelity design does not start from scratch. Before designing, look for source context: brand docs, existing product screenshots, repo components, design tokens, UI kits, prior mockups, reference models, copy docs, and constraints from legal, product, or engineering.

If a repo is available, inspect the real source before inventing UI - theme files, token files, global stylesheets, layout scaffolds, component files, route/page files, and the form / button / card / navigation implementations. **The file tree is only the menu. Read the files that define the visual vocabulary.** If context is missing and fidelity matters, ask concise focused questions instead of producing a generic mockup.

## Asking questions

Ask when the assignment is new, ambiguous, high-fidelity, externally facing, or dependent on taste. Keep it short - do not ask ten questions by default.

Usually worth asking: intended output format, audience, fidelity level, available source materials, brand or design system in play, number of variations wanted, conservative vs divergent exploration, and which dimension matters most (layout, visual language, interaction, copy, motion, or systemization).

Skip questions when the user gave enough direction, it is a small tweak, it is clearly a continuation, or the missing detail has an obvious default. When proceeding on assumptions, label only the important ones.

## Workflow

1. **Understand the brief** - what is being designed, who it is for, what artifact should exist at the end, what constraints are locked.
2. **Gather context** - read supplied docs, screenshots, repo files, and design assets. Identify the visual vocabulary before writing code.
3. **Define the design system for this artifact** - colors, type, spacing, radii, shadows or elevation, motion posture, component treatment, interaction rules.
4. **Choose the format** - static visual comparison = one HTML canvas with options side by side; interaction/flow = clickable prototype; presentation = fixed-size HTML deck with slide navigation; component exploration = component lab with variants; motion = timeline or state-based animation.
5. **Build the artifact** - prefer a single self-contained HTML file unless the task calls for repo implementation. Preserve prior versions for major revisions. Avoid unnecessary dependencies.
6. **Verify** (see below) - do not skip, and do not overclaim.
7. **Report briefly** - exact path, what it contains, caveats, next decision.

## Artifact format

Default to local files. For standalone artifacts:

- Descriptive filename: `Landing Page.html`, `Command Palette Prototype.html`, `Design System Board.html`.
- Embed CSS in `<style>`, JS in `<script>`, and keep the file directly openable in a browser.
- Avoid remote dependencies unless explicitly useful and stable.
- Include responsive behavior unless the format is intentionally fixed-size.

For significant revisions: preserve the previous version as `Name.html`, then create `Name v2.html`, `Name v3.html`, or keep one file with in-page toggles if the assignment is variant exploration.

For repo implementation: follow the repo's actual stack, reuse existing components and tokens, and do not ship a standalone artifact when the user asked for production code.

## HTML / CSS / JS standards

Use modern CSS well: CSS variables for tokens, CSS grid for layout, container queries where helpful, `text-wrap: pretty` where supported, real focus states, real hover states, `prefers-reduced-motion` handling for non-trivial motion, responsive scaling, and semantic HTML where practical.

Avoid: huge monolithic files when a real repo structure is expected, fragile hard-coded viewport assumptions, inaccessible tiny hit targets, decorative JS that fights usability, and `scrollIntoView` unless there is no safer option.

**Hard minimums:** mobile hit targets >= 44px. Print documents >= 12pt. 1920x1080 slide decks >= 24px.

**React:** use plain HTML/CSS/JS by default. Reach for React only when the artifact needs meaningful state, variants are easier as components, interaction complexity warrants it, or the target implementation is React/Next.js and fidelity matters. If using React from CDN, pin exact versions (never unpinned `react@18` style URLs), avoid `type="module"` unless necessary, avoid multiple globals named `styles`, give style objects specific names (`commandPaletteStyles`, `deckStyles`), and explicitly attach shared components to `window` when splitting Babel scripts. Inside a real repo, use the repo's package manager and component architecture instead.

## Deck rules

Use a fixed-size canvas scaled to fit the viewport. Default 1920x1080, 16:9.

Required: keyboard navigation, visible slide count, `localStorage` persistence for the current slide, print-friendly layout where practical, screen labels or stable IDs for important slides, and **no speaker notes unless explicitly asked**. Use 1-2 background colors max unless the brand system demands more. Keep slides sparse - if a slide feels empty, solve it with layout, rhythm, scale, or imagery placeholders, never filler text.

**Do not hand-wave a deck as markdown bullets.** If the user asked for a deck, build a designed artifact.

## Prototype rules

Make the primary path clickable and include key states: default, hover/focus, loading, empty, error, success where relevant. Expose variations with in-page controls when useful, but keep controls out of the final composition unless they are intentionally part of the prototype. Persist important state in `localStorage` when refresh continuity matters.

If the prototype models a product flow, design the flow, not just the first screen.

## Variation rules

When exploring, default to at least three options:

1. **Conservative** - closest to existing patterns, lowest risk.
2. **Strong-fit** - the best interpretation of the brief.
3. **Divergent** - more novel, useful for discovering taste boundaries.

Variations may explore layout, hierarchy, type scale, density, color posture, surface treatment, motion, interaction model, copy structure, or component shape. **Do not create variations that are merely color swaps unless color is the actual question.** When the user picks a direction, consolidate - do not leave the project as a permanent pile of options.

## Tweakable designs

The hosted edit-mode toolbar does not exist here, but preserve the idea: when useful, add a small in-page `Tweaks` panel controlling theme mode, layout variant, density, accent color, type scale, motion on/off, copy variant, or component variant. Keep it unobtrusive and persist values with `localStorage` when helpful. **The design must look final when tweaks are hidden.**

## Content discipline

Do not add filler content. Every element must earn its place. Avoid fake metrics, decorative stats, generic feature grids, unnecessary icons, placeholder testimonials, AI-generated fluff sections, and invented content that changes strategy or claims.

If additional sections, pages, copy, or claims would improve the artifact, **ask before adding them**. When copy is necessary but not final, mark it as draft or placeholder.

## Anti-slop rules

Avoid: aggressive gradient backgrounds; glassmorphism by default; emoji unless the brand uses them; generic SaaS cards with icons everywhere; left-border accent callout cards; fake dashboards filled with arbitrary numbers; stock-photo hero sections; oversized rounded rectangles substituting for hierarchy; rainbow palettes; vague labels like "Insights", "Growth", "Scale", "Optimize" with no content; and decorative SVG illustrations pretending to be product imagery.

**Minimal is not automatically good. Dense is not automatically cluttered.** Choose intentionally.

**Typography and color posture:** reuse the existing type system and brand palette when one exists. If none exists, choose deliberately for the artifact (editorial = serif or humanist headline with restrained sans body; software/productivity = precise sans with strong numeric treatment; luxury/minimal = fewer weights, more spacing discipline; technical = mono accents only, not mono everywhere) and define a small palette - neutrals, surface, ink, muted text, border, one accent, plus danger/success if needed. Prefer `oklch` for invented palettes and check contrast for important text and controls. Do not invent a lot of colors from scratch. Use type as hierarchy before adding boxes, icons, or color.

**Composition:** design with rhythm - scale, whitespace, density, alignment, repetition, contrast, interruption. Never make every section the same card grid. For product UIs prioritize speed of comprehension over decoration; for marketing surfaces make one idea land per section; for dashboards avoid "data slop" and only show data that helps the user decide or act.

**Motion is discipline, not theater.** Good motion clarifies state changes, reduces anxiety during loading, shows continuity between surfaces, gives controls tactility, and stays subtle. Bad motion loops without purpose, delays the user, calls attention to itself, or hides poor hierarchy. Respect `prefers-reduced-motion`.

**Imagery:** use real supplied imagery when available. If an asset is missing, use a clean placeholder, or typography / layout / abstract texture instead, and ask for real material when fidelity matters. Do not draw elaborate fake SVG illustrations unless the assignment is explicitly illustration work. Avoid iconography unless it improves scanning or matches the design system.

## Source-code fidelity

When recreating or extending a UI from a repo: inspect the repo tree, identify the actual UI source files, read theme / token / global style / component files, lift exact values where appropriate, match spacing / radii / shadows / copy tone / density / interaction patterns, and only then design or modify. **Do not build from memory when source files are available.** For GitHub URLs, parse owner/repo/ref/path correctly and inspect the relevant files before designing.

Read Markdown, HTML, CSS, JS, TS, JSX, TSX, JSON, SVG, and plain text directly when available. For DOCX / PPTX / PDF, use available local extraction tools; if none, ask the user for exported text or images. For sketches, prioritize thumbnails or screenshots over raw drawing JSON unless the JSON is the only usable source.

## Copyright and reference models

Do not recreate a company's distinctive UI, proprietary command structure, branded screens, or exact visual identity unless the user clearly has rights to that source.

Extracting general design principles is fine (density without clutter, command-first interaction, monochrome with one accent, editorial hierarchy, clear empty states, strong keyboard affordances). Cloning proprietary layouts, copying exact branded surfaces, or reproducing copyrighted content is not. Transform posture and principles into an original design.

## Verification

Before the final response, verify as much as the environment allows.

**Minimum:** the file exists at the stated path, the HTML is saved completely, and obvious syntax issues are checked.

**Better:** open it in a browser tool and check console errors; inspect screenshots at the primary viewport; test key interactions; test light/dark or variants if present; test responsive breakpoints if relevant.

**If verification is limited by environment, say exactly what was and was not verified. Never say "done" if the file was not actually written. Never claim browser verification that did not happen.**

## Final response format

Keep it short and always include: artifact path, what it contains, verification status, and the next suggested action if useful.

```text
Created: /path/to/Prototype.html
It includes 3 layout variants, a Tweaks panel for density/theme, and responsive behavior.
Verified: file exists and opened cleanly in browser, no console errors.
Next: pick the strongest direction and I'll tighten copy + motion.
```

## Pitfalls

- Do not paste hosted tool schemas into output - they cause fabricated tool calls.
- Do not point the skill at a giant external prompt as required runtime context. That creates drift.
- Do not strip the design doctrine while removing tool plumbing.
- Do not over-ask when the user already gave enough direction; do not under-ask for high-fidelity work with no brand context.
- Do not produce generic SaaS layouts and call them designed.
- Do not claim browser verification unless it actually happened.
