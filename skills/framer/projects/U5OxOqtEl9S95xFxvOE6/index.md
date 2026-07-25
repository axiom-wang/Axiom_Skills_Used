# Framer Project Context

## Project Details

- Project ID: U5OxOqtEl9S95xFxvOE6
- Safe Project ID: U5OxOqtEl9S95xFxvOE6
- Session ID: 2
- Generated At: 2026-07-18T05:33:02.853Z
- Project inventory: [[project-inventory.md]]

## How to use this file

This `index.md` is the map. Read the **Always** row first — it is the core foundation, needed for every change. Then read the row that matches your task, plus **every** additional row a multi-domain task touches (e.g. a landing page with a blog is *pages + CMS + components*; do not guess the other domains from memory). Open a guide only when a row names one, and request guides through [[prompt/implementation-guidance-documentation-index.md]]. Fuller patterns and sequencing live in [[recipes.md]].

## Task map

| Doing… | Read before you start |
|---|---|
| **Always — every change** | All files are required: [[prompt/core-principles.md]] (layout, spacing, width, fills, overflow) · [[prompt/core-examples.md]] (worked DSL patterns) · [[prompt/implementation-strategy.md]] (pick creation/edit/recreation, write a design plan, settle reusable-systems + site-metadata) · [[prompt/updating-the-project.md]] (DSL grammar) · [[prompt/tools.md]] (reads, screenshots, `reviewChanges`). House rules: [[prompt/overview.md]], [[prompt/guardrails.md]], [[prompt/critical-reminders.md]]. |
| **Pages / sections** — create, redesign, add sections, visual polish, review | + [[prompt/design-rules.md]] · [[prompt/how-projects-work.md]] §Layout Recipe + §Width Rules + §Links |
| **Responsive breakpoints** | [[recipes.md]] § Responsive breakpoints · [[prompt/how-projects-work.md]] §Layout Recipe (rules 7–8) |
| **CMS** — collections, items, fields, collection lists, CMS-backed content | [[prompt/how-projects-work.md]] §CMS · [[prompt/updating-the-project.md]] (variable/CMS DSL) · guide **CMS Collection Lists** |
| **CMS detail pages** | [[prompt/how-projects-work.md]] §CMS detail pages · guide **CMS Detail Pages** |
| **Components / variants / icons** | [[prompt/how-projects-work.md]] §Components + §Icons · guide **Buttons** or others as needed |
| **Forms** | [[prompt/how-projects-work.md]] §Forms · guide **Forms** |
| **Navigation / links / redirects** | [[prompt/how-projects-work.md]] §Links + §Layout Templates · guide **Navigations** |
| **Publish** | [[prompt/how-projects-work.md]] §Hosting · [[prompt/critical-reminders.md]] |

## Prompt Sections

- `prompt/overview.md` - Overview
- `prompt/guardrails.md` - Guardrails
- `prompt/implementation-strategy.md` - Implementation Strategy
- `prompt/tools.md` - Tools
- `prompt/design-rules.md` - Design Rules
- `prompt/updating-the-project.md` - Updating the Project
- `prompt/core-principles.md` - Core Principles
- `prompt/how-projects-work.md` - How Projects Work
- `prompt/implementation-guidance-documentation-index.md` - Implementation Guidance Documentation Index
- `prompt/core-examples.md` - Core Examples
- `prompt/critical-reminders.md` - Critical Reminders

## Project Inventory

Current project-specific pages, components, CMS data, styles, fonts, icons, and IDs are stored in [[project-inventory.md]]. Treat it as a generated snapshot: read it for orientation, and use the live `read-project` CLI when you need fresh project state.
