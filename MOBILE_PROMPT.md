# Mobile Responsiveness Implementation Prompt

## Context
The current dashboard application (`frontend/src/app/dashboard`) is designed for desktop viewports and breaks on mobile devices. The goal is to refactor the key pages to be "mobile-first", utilizing horizontal scrolling patterns and responsive grid/flex layouts.

## Objectives

### 1. Dashboard Overview (`frontend/src/app/dashboard/page.tsx`)
The overview page contains 4 metric cards, a donut chart, and two lists (Locations, Sources).
- **Metric Cards**:
  - **Current**: Vertical stack on mobile (1 column).
  - **Requirement**: Implement a **horizontal scroll snap container** (Carousel) for mobile.
  - **Implementation**:
    - Use `flex overflow-x-auto snap-x snap-mandatory` on the container for mobile.
    - Reset to `grid` on `md` and larger screens.
    - Ensure cards have a minimum width (e.g., `min-w-[280px]`) on mobile to look good.
    - Hide scrollbars if possible or style them.
- **Intent Distribution**:
  - **Current**: Flex row that overflows/cramps on mobile.
  - **Requirement**: Stack the Chart and Legend vertically on mobile (`flex-col`), side-by-side on desktop (`lg:flex-row`).
- **Layout**:
  - Ensure all `grid-cols` switch to `1` on mobile and higher on desktop.
  - Verify padding (`p-4` vs `p-8`).

### 2. Sessions List (`frontend/src/app/dashboard/sessions/page.tsx`)
The sessions list is currently a strict 12-column grid table.
- **Structure**:
  - **Current**: `grid-cols-12` with fixed spans.
  - **Requirement**: Responsive Card Layout for mobile.
- **Implementation**:
  - **Header**: Hide the table header row on mobile (`hidden md:grid`).
  - **Rows**:
    - Change container to `flex flex-col` or `block` on mobile.
    - Inside each row, use a flexible layout where:
      - "Customer" name/avatar is prominent at the top.
      - "Contact Info" stacks below.
      - "Action" buttons (Lead toggle) are easily tappable.
      - "First Seen" can be small text or hidden if less important.
    - Restore `grid grid-cols-12` on `md` screens.
  - **Search Bar**: Stack the title and search input vertically on mobile (`flex-col items-start`).

### 3. Guest Detail (`frontend/src/app/dashboard/sessions/[guestId]/page.tsx`)
- **Header**: Ensure the title, "Lead" badge, and action buttons wrap correctly on small screens (`flex-wrap`).

## Tech Stack
- Next.js 14+ (App Router)
- Tailwind CSS (Use standard responsive modifiers: `hidden`, `block`, `md:flex`, `lg:grid`, etc.)
- Lucide React Icons

## Design Principles
- **Touch Targets**: Ensure buttons are large enough for touch.
- **Spacing**: Reduce outer padding on mobile to maximize screen real estate.
- **Scroll**: Use native scrolling with snap points for horizontal sections.
