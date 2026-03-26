# Voice Map — Stitch Batch 2 Prompt

## Context
This is Batch 2 of a mobile app design. Batch 1 already established the design system and core screens (Login, Chat, Voice Mode, Sidebar). **Match the exact same design system from Batch 1** — same colors, typography, spacing, and visual style.

> **IMPORTANT:** Attach the Batch 1 output images as reference when using this prompt. All screens must feel like they belong to the same app.

**Navigation model:** This app has NO bottom tab bar. The main navigation is through a sidebar (left drawer) in the Chat screen. The sidebar contains: "새 대화" button → "내 문서" link → "Knowledge Graph" link → conversation history list → user profile + Settings gear. The screens in this batch (DocList, DocDetail, GraphView, Settings) are all reached from the sidebar. Each has a back arrow (←) in the header to return to Chat.

## What to Generate
Design 4 additional screens for "Voice Map". These are the document management and knowledge graph screens.

Generate these 4 screens:
1. **DocList** — document library listing
2. **DocDetail** — single document view with related docs
3. **GraphView** — knowledge graph visualization
4. **Settings** — app settings and account

---

## Design System (same as Batch 1)

**Viewport:** 390 × 844pt. Mobile-only.

**Colors:**
- Background: #FFFFFF (primary), #F7F7F8 (secondary)
- Primary accent: #4F46E5 (Indigo 600)
- Text: #111827 (primary), #6B7280 (secondary)
- Keyword tags: #DBEAFE (blue), #FEF3C7 (amber), #D1FAE5 (green)
- Card border: #E5E7EB

**Typography:** Inter / Pretendard. Page title 20px semibold, body 15px regular, metadata 13px #6B7280.

**Corner radius:** 12px cards, 20px bubbles, 8px chips/tags.

**Icons:** Line-style, 1.5px stroke, 24px.

---

## Screen 1: DocList (Document Library)

A clean list of AI-generated documents, sorted newest first. Accessed from Chat sidebar or header.

- **Header bar (56px):** Left: back arrow (←). Center: "내 문서" in 17px semibold. Right: (empty, reserved for future search icon — show nothing).
- **Document list (scrollable, white background):**
  - Each document card: white background, bottom border #F3F4F6, 16px horizontal padding, 16px vertical padding.
    - **Title:** "AI 스타트업 수익 모델 분석" in 16px semibold, #111827. Single line.
    - **Tags row (below title, 6px gap):** 2-3 colored tag chips. Each chip: 12px text, 6px vertical / 10px horizontal padding, 8px corner radius. Example tags:
      - "수익모델" in #1E40AF on #DBEAFE background
      - "B2B" in #92400E on #FEF3C7 background
      - "SaaS" in #065F46 on #D1FAE5 background
    - **Date (below tags, 4px gap):** "2026년 3월 23일" in 13px, #9CA3AF
  - Show 5-6 document cards with realistic Korean titles:
    - "AI 스타트업 수익 모델 분석" — 수익모델, B2B, SaaS — 오늘
    - "GraphRAG 기술 조사 노트" — GraphRAG, 벡터DB — 오늘
    - "Q2 마케팅 채널 전략" — 마케팅, 성장 — 어제
    - "사용자 페르소나 정의" — UX리서치, 타깃 — 3월 21일
    - "프로덕트 로드맵 v2" — 기획, 로드맵 — 3월 20일

No floating buttons. Clean vertical list.

---

## Screen 2: DocDetail (Document View)

A single document view with rendered markdown content and related documents section.

- **Header bar (56px):** Left: back arrow (←). Center: (no title, or very short truncated doc title). Right: more menu icon (⋯ three dots).
- **Document content area (scrollable, white background, 20px horizontal padding):**
  - **Title:** "AI 스타트업 수익 모델 분석" in 24px bold, #111827. Top margin 16px.
  - **Tags row (12px below title):** Same tag chips as DocList — "수익모델", "B2B", "SaaS"
  - **Metadata line (8px below tags):** "2026년 3월 23일 · AI 대화에서 생성됨" in 13px, #9CA3AF
  - **Content body (20px below metadata):** Rendered markdown text in 15px, #111827, line-height 1.6. Show 3-4 paragraphs of realistic Korean content about AI business models. Include:
    - An H2 heading: "## 주요 수익 모델 유형"
    - A short paragraph
    - A bullet list with 3-4 items
    - Another H2: "## B2B SaaS + API 하이브리드 접근"
    - Another paragraph
  - **Divider line:** #F3F4F6, 1px, full width. 24px vertical margin.
  - **Related documents section:**
    - Section title: "관련 문서" in 16px semibold, #111827
    - 2-3 compact related document cards (12px gap between):
      - Each card: #F7F7F8 background, 12px corner radius, 12px padding
      - Title in 14px semibold + 1-2 tag chips in smaller size (11px)
      - Example: "프로덕트 로드맵 v2" with "기획" tag
      - Example: "Q2 마케팅 채널 전략" with "마케팅", "성장" tags

---

## Screen 3: GraphView (Knowledge Graph)

An interactive node-and-edge graph showing connections between documents. Visual and exploratory.

- **Header bar (56px):** Left: back arrow (←). Center: "Knowledge Graph" in 17px semibold. Right: filter funnel icon.
- **Graph canvas (full remaining area, #F7F7F8 background):**
  - Show 6-8 circular nodes scattered across the canvas, connected by thin lines (edges)
  - **Each node:** 56px diameter circle, white fill, #E5E7EB border (1.5px), with document title text in 11px, centered below or inside. Some nodes slightly larger (more connections = bigger, range 48-72px).
  - **Node colors:** Each node has a subtle colored accent on its border matching its primary tag color:
    - Blue border (#4F46E5) for tech-related
    - Amber border (#F59E0B) for strategy-related
    - Green border (#10B981) for research-related
  - **Edges:** Thin lines (#D1D5DB, 1px) connecting related nodes
  - **One node selected (highlighted):** #4F46E5 border (2px), slight drop shadow, to show active selection state
  - Example node labels: "수익 모델 분석", "GraphRAG 조사", "마케팅 전략", "페르소나 정의", "로드맵 v2", "투자 피칭"
- **Bottom sheet (collapsed state, peeking 80px from bottom):**
  - White background, 12px top corner radius, subtle top shadow
  - Handle bar: 36px wide, 4px height, #D1D5DB, centered at top (8px from top edge)
  - Preview of selected node: "수익 모델 분석" in 16px semibold + tag chips + "열기" button in #4F46E5 text, right-aligned
  - This sheet can be dragged up to reveal full details (show collapsed state only)

---

## Screen 4: Settings

Simple, clean settings screen with grouped sections. iOS-style grouped list.

- **Header bar (56px):** Left: back arrow (←). Center: "설정" in 17px semibold.
- **Content (scrollable, #F7F7F8 background):**
  - **Section 1 — "계정" (16px above, 13px label in #6B7280, uppercase-style)**
    - White card, 12px corner radius, 16px horizontal padding:
      - Row 1: User avatar (40px circle, placeholder image) + "민호" name (15px semibold) + "ceo@cozymakers.ai" email (13px #6B7280) — vertically stacked name/email next to avatar. Full row height 72px.
      - Thin divider #F3F4F6
      - Row 2: "로그아웃" in 15px, #EF4444 (red text). Height 48px. Centered vertically.
  - **Section 2 — "앱" (24px gap from section 1)**
    - White card, 12px corner radius:
      - Row 1: "언어" left in 15px #111827, "한국어" right in 15px #6B7280 + chevron (›). Height 48px.
      - Divider
      - Row 2: "알림" left, toggle switch on right (indigo when on). Height 48px.
  - **Section 3 — "정보" (24px gap)**
    - White card, 12px corner radius:
      - Row 1: "버전" left, "0.1.0" right in #6B7280. Height 48px.
      - Divider
      - Row 2: "오픈소스 라이선스" left, chevron right. Height 48px.
      - Divider
      - Row 3: "피드백 보내기" left, chevron right. Height 48px.

---

## Important Notes for Stitch
- **DO NOT add a bottom tab bar or bottom navigation bar to ANY screen.** This app has NO bottom tabs. Each screen has only a top header bar. Navigation back to Chat happens via the back arrow (←) in the header.
- All UI text is in Korean as shown. Do not translate to English.
- Design all screens at exactly 390 × 844pt.
- **Match Batch 1's design system exactly** — same colors, fonts, spacing, card styles, and header patterns.
- The GraphView screen is the most visually unique — use the node-edge layout as described, keeping it clean and readable.
