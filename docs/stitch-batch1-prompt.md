# Voice Map — Stitch Batch 1 Prompt

## What to Generate
Design 5 mobile app screens for "Voice Map", an AI conversation app where users type or speak ideas, and AI responds with Socratic follow-up questions to deepen their thinking.

Generate these 5 screens:
1. **Login** — Google sign-in screen
2. **Chat (Empty State)** — new conversation, no messages yet
3. **Chat (Active Conversation)** — mid-conversation with AI messages
4. **Voice Mode (Full-screen Overlay)** — voice conversation overlay
5. **Sidebar (Conversation History)** — left drawer with past conversations

---

## Design System

**Style:** Minimal & clean. Generous whitespace, content-first. Similar to Claude mobile app and ChatGPT mobile app.

**Viewport:** 390 × 844pt (iPhone 15 Pro). Mobile-only.

**⚠️ CRITICAL — NO BOTTOM TAB BAR:**
This app does NOT have a bottom navigation/tab bar. The layout is like ChatGPT mobile app: only a top header bar and a bottom text input bar. There is NO tab bar, NO bottom navigation, NO dock with icons at the bottom of the screen. The only element at the bottom is the text input field. Navigation between sections (Docs, Graph, Settings) happens through the sidebar or header icons — never through a bottom tab bar. This is extremely important for the overall UX.

**Colors (Light mode only):**
- Background: #FFFFFF (primary), #F7F7F8 (secondary/message area)
- Primary accent: #4F46E5 (Indigo 600) — buttons, active states, links
- Text: #111827 (primary), #6B7280 (secondary/metadata)
- User message bubble: #EEF2FF (Indigo 50)
- AI message bubble: #FFFFFF with #E5E7EB border
- Voice overlay background: #111827 (dark)
- Keyword tags: #DBEAFE (blue), #FEF3C7 (amber), #D1FAE5 (green)

**Typography:**
- Font: Inter (English) / Pretendard (Korean)
- Page title: 20px semibold
- Section header: 16px semibold
- Body text: 15px regular
- Metadata/caption: 13px regular, secondary color

**Icons:** Line-style, 1.5px stroke, 24px size. Use standard mobile icons (hamburger menu, gear, mic, send arrow, document, back arrow, close X).

**Corner radius:** 12px for cards/buttons, 20px for message bubbles, full-round for avatars.

**Spacing:** 16px standard padding, 12px between list items, 8px between inline elements.

---

## Screen 1: Login

Simple centered layout on white background.

- **Top area (40% from top):** Voice Map logo (abstract sound-wave or mind-map icon) + "Voice Map" text in 28px semibold
- **Below logo:** Tagline "말하면 생각이 문서가 됩니다" in 15px, secondary color
- **Center:** "Continue with Google" button — white background, #E5E7EB border, Google "G" icon on left, 16px text. Full width with 24px side margins. Height 52px.
- **Bottom (safe area above):** "By continuing, you agree to our Terms and Privacy Policy" in 12px, secondary color, with underlined links

No other elements. Maximum whitespace. Clean and trustworthy.

---

## Screen 2: Chat (Empty State)

This is the home screen after login. No messages yet.

- **Header bar:** Left: hamburger menu icon (☰). Center: "Voice Map" in 17px semibold. Right: gear icon (⚙). Height 56px, white background, bottom border #F3F4F6.
- **Center area (vertically centered in remaining space):**
  - AI avatar (32px circle, indigo gradient) above
  - "무엇에 대해 생각하고 계신가요?" in 20px semibold, centered
  - 4 suggestion chips below, arranged in 2×2 grid with 8px gap:
    - "새 사업 아이디어 정리"
    - "논문 주제 브레인스토밍"
    - "프로젝트 기획 구체화"
    - "회의 안건 정리"
  - Each chip: white background, #E5E7EB border, 14px text, 12px vertical padding, 16px horizontal padding, 12px corner radius
- **Bottom input bar (sticky, above safe area). This is the ONLY bottom element — NO tab bar below it:**
  - White background, 12px padding all around
  - Left of text field: circular "+" button (28px, #F7F7F8 background, #6B7280 icon) for attachments
  - Text field: #F7F7F8 background, 44px height, 24px corner radius, placeholder "아이디어를 말해보세요..." in 15px secondary color
  - Right of text field: microphone icon (🎤) in #6B7280, 24px — for voice input (STT)
  - Far right: circular voice mode button (28px, #111827 background, white waveform icon) — tapping this opens the full-screen Voice Mode overlay
  - When text is entered: mic icon changes to send arrow (↑) in #4F46E5

---

## Screen 3: Chat (Active Conversation)

Same layout as Screen 2 but with an ongoing conversation. Show 4-5 messages.

- **Header bar:** Same as empty state
- **Message area (scrollable, #F7F7F8 background):**
  - **User message 1:** Right-aligned bubble with #EEF2FF background, 20px corner radius. Text: "AI 스타트업의 수익 모델에 대해 정리하고 싶어" in 15px, #111827.
  - **AI message 1:** Left-aligned. Small AI avatar (24px, indigo) on top-left. White bubble with subtle #E5E7EB border. Text in 15px with a Socratic follow-up question: "흥미로운 주제네요. 먼저 어떤 유형의 AI 서비스를 염두에 두고 계신가요? B2B SaaS, API 과금, 소비자 구독 등 다양한 모델이 있는데, 특정 방향이 있으신지 궁금합니다."
  - **User message 2:** "B2B SaaS 쪽으로 생각하고 있어. 근데 API 과금도 병행하면 좋을 것 같아."
  - **AI message 2 (currently streaming):** White bubble, partial text visible: "좋은 하이브리드 접근이네요. 두 모델을 병행할 때 고려해야 할 포인트가 몇 가지 있는데요..." with a blinking cursor (|) at the end to indicate streaming.
- **Bottom input bar:** Same layout as empty state (+ button, text field, mic, voice mode button). NO tab bar below it. Additionally, show a subtle "📄 문서로 정리하기" banner/chip above the input bar — a thin 36px bar with #F7F7F8 background suggesting the user can save this conversation as a document.

---

## Screen 4: Voice Mode (In-Chat with AI Orb)

Voice mode keeps the chat screen visible. Messages continue to appear as text while the AI speaks. An animated orb/sphere appears above the input bar as the AI's voice avatar. Similar to ChatGPT's voice mode — NOT a separate dark overlay screen.

- **Background:** #111827 (dark navy) — the entire screen background switches to dark when voice mode is active, but the chat messages remain readable.
- **Top bar:** Left: "Auto" or model indicator text in #4F46E5, 14px. No other header elements — clean and minimal.
- **Message area (same as Chat, but on dark background):**
  - Previous messages remain visible and scrollable
  - User's voice input appears as a right-aligned message bubble (dark gray background, e.g. #374151, white text): "안녕"
  - AI's text response appears left-aligned in white text (no bubble, directly on dark background): "안녕, 민호! 만나서 반가워. 오늘은 어떤 이야기 나눠 볼까?"
  - Below AI response: small action icons row (copy, thumbs up, thumbs down, share, more) in #6B7280, 20px icons
- **AI Orb (above input bar, centered):**
  - Animated sphere/orb: ~120px diameter, positioned at bottom-center of the screen, above the input bar
  - The orb has a soft gradient glow — light blue/indigo tones (#818CF8 → #93C5FD → white center), suggesting an ethereal, glowing sphere
  - This orb represents the AI listening/speaking state. Show it in a "speaking" state with visible animation energy.
- **Bottom input bar (same position as normal chat):**
  - Dark background matching the screen (#1F2937)
  - Left: circular "+" button (28px, #374151 background, #9CA3AF icon)
  - Center: text field with dark background (#374151), placeholder "아이디어를 말해보세요..." in #9CA3AF
  - Right: microphone icon (🎤) in white, 24px — currently active/recording state
  - Far right: circular close button (X) — 28px, white background, dark X icon — tapping exits voice mode and returns to normal chat

Overall mood: dark and focused but with full context. The user can see the conversation while speaking. The AI orb is the visual focal point, floating above the input bar.

---

## Screen 5: Sidebar (Navigation + Conversation History)

Left drawer that slides over the Chat screen. Show it overlapping Screen 2 or 3, with the right edge of Chat visible behind a dark scrim. **This sidebar is the app's main navigation hub** — it provides access to new conversations, documents, knowledge graph, and past conversation history.

- **Sidebar width:** ~300px (about 77% of screen width)
- **Sidebar background:** White
- **Top section (navigation area):**
  - "새 대화" button: full width of sidebar, 44px height, #4F46E5 text with "+" icon on left, white background. 16px padding from edges.
  - Thin divider #F3F4F6 (8px vertical margin)
  - Navigation links (each 44px height, 16px horizontal padding):
    - 📄 icon (20px, #6B7280) + "내 문서" text in 15px #111827 — navigates to Document Library
    - 🔗 icon (20px, #6B7280) + "Knowledge Graph" text in 15px #111827 — navigates to Graph View
  - Thin divider #F3F4F6 (8px vertical margin)
  - Section label: "최근 대화" in 13px #9CA3AF, 16px left padding, 8px bottom margin
- **Conversation list (scrollable, fills remaining space):**
  - Each item: 56px height, 16px horizontal padding
    - Title: "AI 스타트업 수익 모델 정리" in 15px, #111827, single line truncated
    - Subtitle: "오늘" or "3월 22일" in 13px, #9CA3AF
  - Active conversation highlighted with #F7F7F8 background
  - Show 5-6 conversation items with realistic Korean titles:
    - "AI 스타트업 수익 모델 정리" — 오늘
    - "GraphRAG 기술 검토" — 오늘
    - "Q2 마케팅 전략 브레인스토밍" — 어제
    - "사용자 인터뷰 질문 설계" — 3월 21일
    - "프로덕트 로드맵 v2 논의" — 3월 20일
- **Bottom section:**
  - Thin top border #F3F4F6
  - User avatar (32px circle, photo placeholder) + "민호" name in 15px + gear icon (⚙) on right — gear navigates to Settings
  - 16px padding, 56px height

**Scrim:** The area to the right of the sidebar (visible Chat screen behind) should have a semi-transparent black overlay (#000000 40% opacity).

---

## Important Notes for Stitch
- **DO NOT add a bottom tab bar or bottom navigation bar to ANY screen.** This app uses a sidebar for navigation, NOT bottom tabs. The only element at the bottom of Chat screens is the text input bar.
- All UI text is in Korean as shown above. Do not translate to English.
- Design all screens at exactly 390 × 844pt.
- Maintain consistent spacing, colors, and typography across all 5 screens.
- This is Batch 1 of 2. The design system established here will be carried forward to Batch 2 (DocList, DocDetail, GraphView, Settings screens).
