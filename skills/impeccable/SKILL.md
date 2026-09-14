---
name: impeccable
description: Design, redesign, critique, audit, and polish production frontend interfaces. Use for websites, landing pages, dashboards, product UI, app shells, components, forms, settings, empty states, and design systems or tokens. Covers visual hierarchy, information architecture, accessibility, performance, responsive behavior, theming, typography, spacing, layout, color, motion, UX copy, and error states. Also covers capturing an existing project's design system, and live in-browser iteration on UI elements. Not for backend-only or non-UI tasks.
version: 3.5.0
user-invocable: true
argument-hint: "[init|document · shape|craft · critique|audit · polish · live] [target]"
license: Apache 2.0
---

Designs and iterates production-grade frontend interfaces. Real working code, committed design choices, exceptional craft.

## Script path

Every `scripts/*.mjs` invocation below is written relative to this skill's own directory. Resolve it to whichever harness loaded this file:

```
~/.workbuddy/skills/impeccable/scripts/…    # WorkBuddy
~/<skill>/scripts/…       # Claude Code
~/.codex/skills/impeccable/scripts/…        # Codex
```

Never assume `.claude/skills/...` - that path is only valid when the skill is installed project-locally.

## Setup

You MUST do these steps before proceeding:

1. Run `node <skill>/scripts/context.mjs` once per session. If you've already seen its output in this conversation, do not re-run it. The script prints the project's PRODUCT.md (and DESIGN.md when present) as a markdown block, or reports it missing. Follow whatever it prints. **If it reports `NO_PRODUCT_MD`, stop and follow `reference/init.md` before doing anything else.** If the output ends with an `UPDATE_AVAILABLE` directive, follow it (ask the user once about updating, then continue); it never blocks the current task.
2. If the user invoked a sub-command, you MUST read `reference/<command>.md` next. **Non-optional.** The reference defines the command's flow; without it you will skip steps the user expects.
3. Familiarize yourself with any existing design system, conventions, and components in the code. Read at least one project file (CSS / tokens / theme / a representative component or page). **Required even when you loaded a sub-command reference in step 2.** Don't reinvent the wheel; use what's there when it works, branch out when the UX wins.
4. Read the matching register reference. **Non-optional; skipping it produces generic output.** If the project is marketing, a landing page, a campaign, long-form content, or a portfolio (design IS the product), read `reference/brand.md`. If it is app UI, admin, a dashboard, or a tool (design SERVES the product), read `reference/product.md`. Pick by first match: (1) task cue ("landing page" vs "dashboard"); (2) the surface in focus; (3) the `register` field in PRODUCT.md.
5. **If the project is brand-new (no existing CSS tokens / theme / committed brand colors found in step 3)**, run `node <skill>/scripts/palette.mjs` for a brand seed color and composition guidance. This anchors the primary brand color; compose the rest of the palette (bg, surface, ink, accent, muted) around it as the script instructs. Use OKLCH throughout. **Skip only if step 3 found committed brand colors** - then identity preservation wins.

## Design guidance

Produce ready-to-ship, production-grade code, not prototypes or starting points. Take no shortcuts unless the user asks (when in doubt, ask). Don't stop until the implementation is complete: beautiful, responsive, fast, precise, bug-free, on brand. Battle-test every page, section, or component using the tools available to you (browser screenshotting, computer use, etc).

### Color

- **Verify contrast.** Body text ≥4.5:1 against its background; large text (≥18px, or bold ≥14px) ≥3:1. Placeholder text needs the same 4.5:1, not the muted-gray default. The most common failure is muted gray body text on a tinted near-white. If contrast is even close, bump the body color toward the ink end of the ramp - light gray "for elegance" is the single biggest reason AI designs feel hard to read.
- Gray text on a colored background looks washed out. Use a darker shade of the background's own hue, or a transparency of the text color.

### Typography

- Cap body line length at 65-75ch.
- Hierarchy through scale + weight contrast (≥1.25 ratio between steps). Avoid flat scales.
- Cap font-family count at 3 (display + body + optional mono). More than 3 reads as indecision. One well-tuned family with weight contrast usually beats three competing typefaces.
- Don't pair fonts that are similar but not identical (two geometric sans, two humanist sans). Pair on a contrast axis (serif + sans, geometric + humanist), or use one family in multiple weights.
- No all-caps body copy. Reserve uppercase for short labels (≤4 words), sparingly-used eyebrows, and badges.
- Display heading ceiling: `clamp()` max ≤ 6rem (~96px). Above that the page is shouting, not designing.
- Display heading letter-spacing floor: ≥ -0.04em. Tighter and letters touch; cramped, not "designed".
- `text-wrap: balance` on h1-h3 for even line lengths; `text-wrap: pretty` on long prose to reduce orphans.

### Layout

- Vary spacing for rhythm.
- Cards are the lazy answer. Use them only when truly the best affordance. Nested cards are always wrong.
- Flexbox for 1D, Grid for 2D. Don't default to Grid when `flex-wrap` would be simpler.
- Responsive grids without breakpoints: `repeat(auto-fit, minmax(280px, 1fr))`.
- Build a semantic z-index scale (dropdown → sticky → modal-backdrop → modal → toast → tooltip). Never arbitrary values like 999 or 9999.

### Motion

- Motion is part of the build, not an afterthought.
- Don't animate CSS layout properties unless truly needed.
- Ease out with exponential curves (ease-out-quart / quint / expo). No bounce, no elastic.
- Use libraries for advanced needs (motion, gsap, anime.js, lenis).
- **Reduced motion is not optional.** Every animation needs a `@media (prefers-reduced-motion: reduce)` alternative: typically a crossfade or instant transition.
- Staggering items within one list is legitimate. The tell is the uniform reflex (one identical entrance applied to every section), not motion itself; each reveal should fit what it reveals. Suppressing the reflex is never a reason to ship a page with no motion at all.
- **Reveal animations must enhance an already-visible default.** Don't gate content visibility on a class-triggered transition: transitions pause on hidden tabs and headless renderers, so the reveal never fires and the section ships blank.
- Premium motion materials are not just transform/opacity. Blur, `backdrop-filter`, `clip-path`, `mask`, and shadow/glow are part of the palette when they materially improve the effect and stay smooth.

### Interaction

- Dropdowns rendered with `position: absolute` inside an `overflow: hidden` or `overflow: auto` container get clipped. Use the native `<dialog>` / popover API, `position: fixed`, or a portal to escape the stacking context.

### Copy

- Every word earns its place. No restated headings, no intros that repeat the title.
- **No em dashes.** Use commas, colons, semicolons, periods, or parentheses. Also not `--`.
- **No aphoristic-cadence body copy as a default voice.** Don't fall into "serious statement, then punchy short negation" as the page's recurring rhythm. If three or more section copy blocks land on a short rebuttal-shaped sentence, rewrite. Specific, not aphoristic.
- **No marketing buzzwords.** The streamline / empower / supercharge / leverage / unleash / transform / seamless / world-class / enterprise-grade / next-generation / cutting-edge / game-changer / mission-critical family. Pick a specific noun and a verb describing what the product literally does.
- Button labels: verb + object. "Save changes" beats "OK"; "Delete project" beats "Yes". The label says what will happen.
- Link text needs standalone meaning. "View pricing plans" beats "Click here"; screen readers announce links out of context.

### New projects only (when no prior work exists)

- **Use OKLCH.**
- **The cream / sand / beige body bg is the saturated AI default.** The whole warm-neutral band (OKLCH L 0.84-0.97, C < 0.06, hue 40-100) reads as cream / sand / paper / parchment regardless of what you call it. Token names like `--paper`, `--cream`, `--sand`, `--bone`, `--flour`, `--linen`, `--parchment`, `--wheat`, `--biscuit`, `--ivory` are tells in themselves. If the brief is "warm, traditional, family-coastal-Italian" or "magazine-warm" or "editorial-restraint", DO NOT translate that into a near-white warm-tinted bg. Pick instead: (a) a saturated brand color as the body (terracotta, oxblood, deep ochre, near-black), (b) a true off-white at chroma 0, or chroma toward the brand's own hue, not warmth-by-default, or (c) a darker mid-tone tinted neutral that is clearly the brand's own. "Warmth" is carried by accent + typography + imagery, not by the body bg.
- Tinted neutrals: add 0.005-0.015 chroma toward the brand's hue. Don't default-tint toward warm or cool "because the brand feels that way" - that's the cross-project monoculture move.
- **Dark vs. light is never a default.** Not dark "because tools look cool dark", not light "to be safe". Before choosing, write one sentence of physical scene: who uses this, where, under what ambient light, in what mood. If the sentence doesn't force the answer, it isn't concrete enough. Add detail until it does.
- **Pick a color strategy before picking colors.** Four steps on the commitment axis: **Restrained** (tinted neutrals + one accent ≤10%; product default, brand minimalism), **Committed** (one saturated color carrying 30-60% of the surface; brand default for identity-driven pages), **Full palette** (3-4 named roles, each deliberate; brand campaigns, product data viz), **Drenched** (the surface IS the color; brand heroes, campaign pages).

### Absolute bans

Match-and-refuse. If you're about to write any of these, rewrite the element with different structure.

- **Side-stripe borders.** `border-left` / `border-right` greater than 1px as a colored accent on cards, list items, callouts, or alerts. Never intentional. Rewrite with full borders, background tints, leading numbers/icons, or nothing.
- **Gradient text.** `background-clip: text` combined with a gradient background. Decorative, never meaningful. Use a single solid color; emphasis via weight or size.
- **Glassmorphism as default.** Blurs and glass cards used decoratively. Rare and purposeful, or nothing.
- **The hero-metric template.** Big number, small label, supporting stats, gradient accent. SaaS cliché.
- **Identical card grids.** Same-sized cards with icon + heading + text, repeated endlessly.
- **Tiny uppercase tracked eyebrow above every section.** The 2023-era kicker (small all-caps, wide tracking, "ABOUT" / "PROCESS" / "PRICING" above each heading) is now the saturated AI scaffold, appearing on 55-95% of generations regardless of brief - which is the definition of a tell. One named kicker as a deliberate brand system is voice; an eyebrow on every section is AI grammar. Choose a different cadence.
- **Numbered section markers as default scaffolding (01 / 02 / 03).** The eyebrow trope one tier deeper. Numbers earn their place when the section actually IS a sequence (a real 3-step process, an ordered flow, a typed timeline) and the order carries information the reader needs. One deliberate numbered sequence on a page is voice; numbered eyebrows across a site are AI grammar.
- **Text that overflows its container.** Long heading words plus large clamp scales plus narrow grids cause headline overflow on tablet/mobile. Test heading copy at every breakpoint; if it overflows, reduce the clamp max or rewrite the copy. The viewport is part of the design.

### The AI slop test

If someone could look at this interface and say "AI made that" without doubt, it's failed. Cross-register failures are the absolute bans above; register-specific failures live in each reference.

**Category-reflex check.** Run at two altitudes; the second catches what the first misses.

- **First-order:** if someone could guess the theme + palette from the category alone, it's the first training-data reflex. Rework the scene sentence and color strategy until the answer isn't obvious from the domain.
- **Second-order:** if someone could guess the aesthetic family from category-plus-anti-references ("AI workflow tool that's not SaaS-cream → editorial-typographic", "fintech that's not navy-and-gold → terminal-native dark mode"), it's the trap one tier deeper: the first reflex was avoided, the second wasn't. Rework until both answers are not obvious. The brand register's reflex-reject aesthetic lanes list catches the currently-saturated families.

## Commands

| Command | Category | Description | Reference |
|---|---|---|---|
| `init` | Build | Set up project context: PRODUCT.md, DESIGN.md, live config, next steps | [reference/init.md](reference/init.md) |
| `document` | Build | Generate DESIGN.md from existing project code | [reference/document.md](reference/document.md) |
| `shape [feature]` | Build | Plan UX/UI before writing code | [reference/shape.md](reference/shape.md) |
| `craft [feature]` | Build | Shape, then build a feature end-to-end | [reference/craft.md](reference/craft.md) |
| `extract [target]` | Build | Pull reusable tokens and components into the design system | [reference/extract.md](reference/extract.md) |
| `critique [target]` | Evaluate | UX design review with heuristic scoring | [reference/critique.md](reference/critique.md) |
| `audit [target]` | Evaluate | Technical quality checks (a11y, perf, responsive) | [reference/audit.md](reference/audit.md) |
| `polish [target]` | Refine | Final quality pass before shipping | [reference/polish.md](reference/polish.md) |
| `live` | Iterate | Visual variant mode: pick elements in the browser, generate alternatives | [reference/live.md](reference/live.md) |

Plus two management commands: `pin <command>` and `unpin <command>`, detailed below.

### Routing rules

1. **No argument**: the user is asking "what should I do?" Make the menu context-aware instead of static. Setup has already run `context.mjs`; if that reported `NO_PRODUCT_MD` you are already in init, so finish that and skip this. Otherwise run `node <skill>/scripts/context-signals.mjs` once and read its JSON, then lead with the **2-3 highest-value next commands**, each with a one-line reason pulled from the signals, followed by the full menu (the table above, grouped by category). **Never auto-run a command; the recommendation is a suggestion the user confirms.**

   Reason over the signals; there is no score to obey:
   - `setup.hasDesign` false while `setup.hasCode` true → `document` (capture the visual system).
   - `critique.latest` is `null` → the project has never been critiqued; for a set-up project with a real surface, offering `/impeccable critique <surface>` is a strong default.
   - `critique.latest` with a low `score` or non-zero `p0` / `p1` → `polish` (it reads that snapshot as its backlog), or re-run `critique` if the snapshot looks stale.
   - `git.changedFiles` pointing at one surface → scope `audit` or `polish` to those files specifically, naming them.
   - `devServer.running` true → `live` is available for in-browser iteration; if false, don't lead with `live`.
   - Otherwise group by intent exactly as init's "Recommend starting points" step does (build new / improve what's there / iterate visually), tailored to `setup.register`.

   **If `scan.targets` is non-empty, run `node <skill>/scripts/detect.mjs --json <scan.targets joined by spaces>` once** (the bundled detector over local files: no network, no npx). `scan.via` tells you what they are: `git-changes` (the markup/style files in your dirty tree, the most relevant set), `source-dir` (e.g. `src`, `app`), `html`, or `root`. Fold the hits into your picks: many quality / contrast hits → `audit` or `polish`; a specific slop family → the matching fix. It's a real, current signal that beats guessing. If detect errors or the tree is large and slow, skip it and recommend the user run `audit` themselves; never block the suggestion on it.

   Keep it to 2-3 pointed picks with the exact command to type. The menu stays the fallback; the recommendation is the lede.
2. **First word matches a command**: load its reference file and follow its instructions. Everything after the command name is the target.
3. **First word doesn't match, but the intent clearly maps to one command** (e.g. "fix the spacing" → `polish`, "the colors feel flat" → `polish`, "review this" → `critique`): load that command's reference and proceed as if invoked. If two commands could fit, ask once which.
4. **No clear command match**: general design invocation. Apply the setup steps, the General rules, and the loaded register reference, using the full argument as context.

Setup (context gathering, register) is already loaded by then; sub-commands don't re-invoke `/impeccable`.

If the first word is `craft`, setup still runs first, but [reference/craft.md](reference/craft.md) owns the rest of the flow. If setup invokes `init` as a blocker, finish init, refresh context, then resume the original command and target.

`teach` is a deprecated alias for `init`: if the user types it, load [reference/init.md](reference/init.md) and proceed as if they ran `init`.

## Pin / Unpin

**Pin** creates a standalone shortcut so `/<command>` invokes `/impeccable <command>` directly. **Unpin** removes it. The script writes to every harness directory present in the project.

```bash
node <skill>/scripts/pin.mjs <pin|unpin> <command>
```
