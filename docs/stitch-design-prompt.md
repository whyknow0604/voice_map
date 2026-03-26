# Voice Map — Stitch Design Prompt

## App Overview
Voice Map is a mobile-first "thinking hard drive" app for knowledge workers (grad students, researchers, planners). Users speak or type their ideas, an AI structures them through Socratic dialogue, and automatically turns conversations into searchable, interconnected documents.

**Core value proposition:** "I spoke, and it became a document. And it connected."

**Platform:** Mobile hybrid app (iOS/Android via React + Capacitor). Design for mobile viewport (390×844pt) as primary, but keep desktop-responsive in mind.

---

## Design Direction

### Style & Mood
- **Minimal & Clean** — generous whitespace, content-first hierarchy
- **Reference apps:** Claude mobile app, ChatGPT mobile app (for conversation UI), Obsidian (for graph view & knowledge connection concept)
- **Light mode only** (for MVP)

### Typography
- Modern sans-serif: **Inter** or **Pretendard** (for Korean support)
- Clear hierarchy: large bold headings, regular body text, small metadata
- Prioritize readability for long-form conversation and document content

### Color Palette
- White/light gray backgrounds
- 1 primary accent color (suggest a calm, intellectual tone — like deep blue, teal, or muted indigo)
- Subtle secondary colors for tags/keywords
- Minimal use of color — let content breathe

### Iconography
- Line-style icons, thin stroke
- Consistent 24px icon set

---

## Screen Architecture (6 screens + 1 overlay)

### Screen Flow Diagram
```
Login → Chat (home) ←→ DocList
                ↓              ↓
         Voice Overlay    DocDetail
                               ↓
                          GraphView

Sidebar: Conversation History (hamburger menu on mobile)
Settings: accessible from Chat header
```

---

## Screen 1: Login
**Purpose:** Google OAuth sign-in. First screen users see.

**Layout:**
- App logo + "Voice Map" branding at center-top
- Tagline: "말하면 생각이 문서가 됩니다" (or English equivalent)
- Single "Continue with Google" button (Google branded)
- Clean, centered layout with ample whitespace
- Subtle background illustration or gradient (optional — keep minimal)

**Key elements:**
- App icon/logo
- Tagline text
- Google Sign-in button
- "By continuing, you agree to..." footer text

---

## Screen 2: Chat (Main Home Screen)
**Purpose:** Primary interaction screen. Text-based AI conversation with Socratic follow-up questions. This is the home screen after login.

**Layout — similar to Claude/ChatGPT mobile app:**
- **Header:** Hamburger menu (☰) left → "AI Idea Builder" center title → Settings gear (⚙) right
- **Message area:** Scrollable conversation thread
  - User messages: right-aligned, subtle accent background
  - AI messages: left-aligned, white/light background with AI avatar
  - AI responses include Socratic follow-up questions in the message
  - Typing indicator (three dots animation) when AI is responding
  - Streaming text render (tokens appear one by one)
- **Input bar (bottom, sticky):**
  - Text input field with placeholder "아이디어를 말해보세요..."
  - Microphone button (🎤) on the right — tapping opens Voice Overlay
  - Send button appears when text is entered
  - "Document" button (📄) to manually trigger documentation of current conversation

**Empty state (new conversation):**
- Centered greeting: "무엇에 대해 생각하고 계신가요?"
- 3-4 suggestion chips: example prompts like "새 사업 아이디어 정리", "논문 주제 브레인스토밍", "프로젝트 기획 구체화"

**Interaction notes:**
- Long-press a message to copy
- When AI finishes a conversation arc, show a subtle "📄 문서로 정리하기" prompt

---

## Screen 3: Voice Overlay (Full-screen overlay on Chat)
**Purpose:** Real-time bi-directional voice conversation with AI using Gemini Live API. Triggered by tapping the microphone button in Chat.

**Layout — similar to ChatGPT Advanced Voice mode:**
- Full-screen dark/dimmed overlay on top of Chat
- **Center:** Animated waveform visualization (circular or horizontal) showing voice activity
- **Status text:** "듣고 있어요..." / "생각하고 있어요..." / "말하고 있어요..."
- **Bottom controls:**
  - Large red "End" button (●) to stop voice session
  - Small "Text mode" toggle — switches to showing real-time transcript in the chat instead of voice-only
- **Top:** Minimal header with session duration timer and close (X) button

**States:**
1. Listening (user speaking) — waveform active, "듣고 있어요..."
2. Processing — waveform pulsing slowly, "생각하고 있어요..."
3. Speaking (AI responding) — waveform active with different pattern, "말하고 있어요..."
4. Idle — waveform still, ready for input

**On voice session end:**
- Overlay closes, returns to Chat screen
- Full transcript appears in chat as messages
- "📄 문서로 정리할까요?" prompt appears

---

## Screen 4: DocList (Document Library)
**Purpose:** Browse all auto-generated documents, sorted by newest first.

**Layout:**
- **Header:** Back arrow (←) left → "내 문서" center title → (future: search icon)
- **Document cards (vertical list):**
  - Each card shows: Title (bold), keyword tags (colored chips), created date
  - Subtle card style with light border or shadow
  - Tap to navigate to DocDetail
- **Infinite scroll** (20 items per page)
- No search/filter in MVP — simple chronological list

**Empty state:**
- Illustration + "아직 문서가 없어요"
- "AI와 대화하면 자동으로 문서가 만들어져요" subtitle
- CTA button: "대화 시작하기" → navigates to Chat

**Navigation:** Accessible from Chat header or sidebar

---

## Screen 5: DocDetail (Document View & Edit)
**Purpose:** View and edit a single document. Markdown editor with inline editing.

**Layout:**
- **Header:** Back arrow (←) → document title (editable inline) → More menu (⋯)
- **Body:**
  - Title (large, editable)
  - Keywords/tags (editable, add/remove chips)
  - Content area: Markdown rendered view with "Edit" toggle to switch to editor mode
  - Divider
  - "관련 문서" section at bottom — top 5 related documents by similarity (pgvector)
    - Each related doc shown as compact card (title + keywords)
    - Tap to navigate to that document

**Edit mode:**
- Markdown editor (monospace font, syntax highlighting)
- Save/Cancel buttons at top or bottom
- Auto-save indicator

---

## Screen 6: GraphView (Knowledge Graph)
**Purpose:** Visualize connections between documents as an interactive node-edge graph. Experimental feature.

**Layout:**
- **Header:** Back arrow (←) → "Knowledge Graph" center → Filter icon (optional)
- **Graph canvas (full remaining area):**
  - Nodes = documents (circles with title label)
  - Edges = keyword overlap or similarity connections
  - Color-coded by topic clusters
  - Pinch to zoom, pan, drag nodes
- **Bottom panel (collapsible):**
  - When a node is tapped: shows document title, keywords, "열기" button
  - When an edge is tapped: AI insight text "이 두 문서는 ~라는 맥락에서 연결됩니다"
  - Panel slides up from bottom (sheet style)

**Empty/sparse state:**
- "문서가 3개 이상이면 연결 관계가 나타나요"

---

## Screen 7: Settings
**Purpose:** App settings and account management.

**Layout:**
- **Header:** Back arrow (←) → "설정"
- **Sections (grouped list):**
  - Account: Google profile info, email, logout button
  - App: Language preference, notification settings
  - About: Version info, open source licenses, feedback link
- Simple iOS-style grouped table view

---

## Sidebar: Conversation History
**Purpose:** Access previous conversation sessions. Opens from hamburger menu in Chat.

**Layout — similar to ChatGPT sidebar:**
- Slides in from left (drawer style)
- **Top:** "새 대화" button (+ icon)
- **List:** Previous conversations sorted by recent
  - Each item: Auto-generated title (from first message or AI summary), date
  - Tap to load that conversation in Chat
  - Swipe left to delete
- **Bottom:** User profile thumbnail + Settings shortcut

---

## Global Design Notes

### Bottom Navigation (if needed)
Since the primary UX is Chat-centric (like Claude/ChatGPT), bottom tab navigation is NOT used. Instead:
- Chat is the home screen
- DocList and GraphView are accessible from sidebar or header
- This keeps the focus on the conversation experience

### Motion & Animation
- Smooth page transitions (slide left/right)
- Voice overlay: fade-in with scale animation
- Waveform: real-time audio-reactive animation
- Streaming text: cursor blink effect while loading
- Bottom sheet: spring animation for DocDetail panels

### Accessibility
- Minimum 44pt touch targets
- Sufficient color contrast (WCAG AA)
- Support for dynamic text sizing

### Mobile-First Responsive
- Primary: 390×844pt (iPhone 15 Pro)
- Secondary: 360×800pt (Android standard)
- Tablet: 2-column layout (sidebar always visible + main content)

---

## Stitch Generation Order (Suggested)
Since Stitch can generate up to 5 screens simultaneously:
1. **Batch 1:** Login, Chat (with empty state), Chat (with conversation), Voice Overlay, Sidebar
2. **Batch 2:** DocList, DocDetail, GraphView, Settings

---

*Generated for Google Stitch AI Design Tool — Voice Map v0.1~v0.4 MVP*
