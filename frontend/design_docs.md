The following Design PRD is based on an analysis of Attio’s current live product, public design documentation, and the "Linear-style" SaaS aesthetic they pioneered. This document serves as a blueprint for developers and designers to replicate the Attio look and feel.

***

# Product Requirement Document: Design System & UI/UX
**Project:** Replicating Attio Design Aesthetic
**Target Output:** High-fidelity, data-dense SaaS Interface
**Core Philosophy:** "Power through Progressive Disclosure"

## 1. Design Philosophy
Attio's design is defined by **structural minimalism**. It avoids unnecessary decoration, relying on strict hierarchy, subtle borders, and precise spacing to organize high-density data.
* **Data-First:** Content is never hidden behind "pretty" wrappers. Tables and lists are the heroes.
* **Subtle Depth:** The interface is mostly flat but uses multiple layers of "elevation" (z-index) separated by delicate borders and ultra-soft shadows, not heavy drop shadows.
* **Squircle Geometry:** A softening of strict geometry. Icons and containers often sit somewhere between a square and a circle.

---

## 2. Design Tokens (The DNA)

### 2.1 Typography
**Font Family:** `Inter` (Sans-serif)
* **Source:** Google Fonts / rsms.me
* **Rendering:** Optimize for legibility. Use `-webkit-font-smoothing: antialiased`.

**Scale & Usage:**
* **Body (Base):** 13px or 14px (Attio leans smaller than the standard 16px to fit more data).
    * *Weight:* Regular (400) for text, Medium (500) for high-visibility data.
    * *Color:* `Neutral-900` (Light Mode), `Neutral-100` (Dark Mode).
* **Headings:**
    * `H1`: 24px, Medium (500), Tracking -0.02em.
    * `H2`: 20px, Medium (500), Tracking -0.01em.
    * `H3` (Section Headers): 11px or 12px, Uppercase, Bold (700), Tracking +0.04em, Color: `Neutral-500`.
* **Monospace:** `JetBrains Mono` or `Fira Code` (used sparingly for API keys/IDs).

### 2.2 Color Palette (Replication Values)
Attio uses a "semantic" color system. Do not use raw hex codes in components; use tokens.

**Neutrals (The Skeleton):**
* **Background (Light):** `#FFFFFF` (Page), `#F5F7F9` (Sidebar/Secondary).
* **Background (Dark):** `#1D1E20` (Page), `#161618` (Sidebar - *Note: This is a warm, charcoal dark, not pure black*).
* **Borders:**
    * Light Mode: `#E2E4E7` (Subtle), `#D0D5DD` (Strong).
    * Dark Mode: `rgba(255, 255, 255, 0.08)` (Subtle).

**Brand Colors:**
* **Primary Blue:** `#2E5BFF` (approx) – Used for primary buttons, active states, and links.
* **Accent Purple:** `#6E56CF` – Used for "Magical" or AI features.

**Functional / Status Colors:**
* **Success:** `#22C55E` (Green-500)
* **Warning:** `#F59E0B` (Amber-500)
* **Error:** `#EF4444` (Red-500)
* *Implementation Note:* Status tags always use a transparent background (e.g., `bg-green-500/10`) with the solid color as text.

### 2.3 Spacing & Grid
* **Base Unit:** 4px. All spacing, sizing, and line-heights must be multiples of 4 (e.g., 4, 8, 12, 16, 20, 24).
* **Density:** High.
    * *Padding inside buttons:* 6px 12px (Small), 8px 16px (Medium).
    * *Table row height:* 32px (Compact), 40px (Standard).

### 2.4 Shapes & Radius
* **Global Radius:** 6px or 8px (Small components like inputs/buttons).
* **Container Radius:** 12px (Modals, Cards).
* **Icon Radius:** "Squircle" (Superellipse). In CSS, approximate this with `border-radius: 22%` for a smooth look, or use an SVG mask. Attio explicitly mentions a **30% corner radius** for app icons.

---

## 3. Core UI Components

### 3.1 Buttons
* **Primary:**
    * Background: Brand Blue (`#2E5BFF`).
    * Text: White.
    * Shadow: `0 1px 2px rgba(0,0,0,0.1)`.
    * Hover: Lighten by 5%.
* **Secondary (Standard):**
    * Background: White (Light Mode), Charcoal (Dark Mode).
    * Border: 1px solid `Neutral-200`.
    * Text: `Neutral-700`.
    * Shadow: `0 1px 2px rgba(0,0,0,0.05)`.
* **Ghost / Tertiary:**
    * Background: Transparent.
    * Hover: `Neutral-100` (Light), `White/5` (Dark).

### 3.2 Inputs & Forms
* **Style:** Minimalist. No heavy backgrounds.
* **Default State:** White background, 1px Border `Neutral-200`, Radius 6px.
* **Focus State:** Border color changes to Brand Blue. **Important:** Add a "Focus Ring" shadow: `box-shadow: 0 0 0 2px rgba(46, 91, 255, 0.2)`.
* **Typography:** 14px text. Placeholder text should be `Neutral-400`.

### 3.3 The "Attio Card"
Most content lives in cards.
* **Background:** White.
* **Border:** 1px solid `Neutral-200` (Light) or `White/10` (Dark).
* **Shadow:** `0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)`.
* **Header:** Often has a subtle bottom border (`1px solid Neutral-100`) separating title from content.

### 3.4 Navigation (Sidebar)
* **Width:** Fixed (e.g., 240px) but collapsible.
* **Item State:**
    * *Inactive:* Text `Neutral-500`, Icon `Neutral-400`.
    * *Hover:* Background `Neutral-100`, Text `Neutral-900`.
    * *Active:* Background `Neutral-200` (or subtle Brand Tint), Text `Brand Primary`.
* **Section Headers:** Tiny, uppercase text (see Typography).

---

## 4. Key Visual Patterns to Implement

### 4.1 "Inset" Icons
Attio icons often look like they are pressed *into* the page or floating just above.
* **Technique:** Use a 1px inner border on icon containers.
* **CSS:** `box-shadow: inset 0 0 0 1px rgba(0,0,0,0.08);`

### 4.2 The "Command K" Palette
A central search/action bar is mandatory for this style.
* **Visuals:** Centered modal, heavy backdrop blur (`backdrop-filter: blur(4px)`), large shadow.
* **Interaction:** Instant appearance on `Cmd+K`.

### 4.3 Progressive Disclosure Tables
Tables should look simple at first glance.
* **Hidden Actions:** "Edit", "Delete", or "Open" buttons should only appear on **hover** of the table row.
* **Truncation:** Long text should fade out or truncate with an ellipsis `...`.

### 4.4 Loaders & States
* **Skeleton Loading:** Never use spinning wheels for initial load. Use pulsing grey blocks (`bg-neutral-200`) that match the shape of the content (avatar circle, text line).
* **"AI Thinking":** Use a subtle gradient shimmer animation for any AI-generated text or fields.

## 5. Assets & Implementation Guide
1.  **Icon Set:** Use **Heroicons** (closest open-source match) or **Phosphor Icons** (very popular in this aesthetic). Set stroke width to `1.5px` or `2px` (Medium).
2.  **CSS Framework:** Tailwind CSS is highly recommended as its default utility classes (`border-gray-200`, `text-sm`, `tracking-tight`) align perfectly with this PRD.
3.  **Dark Mode:** It is not optional. Build with CSS variables (`var(--bg-primary)`) from day one to support toggling.