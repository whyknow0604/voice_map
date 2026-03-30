# Sprint 3 Wave 0 감사 보고서: 코드-명세서-디자인 불일치

> 작성일: 2026-03-27
> 작성자: Tech Lead Agent
> 목적: 실제 코드 vs Notion API 명세서 vs Stitch 디자인 대조

---

## 1. BE API 엔드포인트 대조

### 1-1. Notion 03.API 명세서에 등록된 엔드포인트

| # | 메서드 | 엔드포인트 | 상태 |
|---|--------|-----------|------|
| 1 | POST | /api/auth/google | 설계중 |
| 2 | GET | /api/documents | 설계중 |
| 3 | GET | /api/documents/{id} | 설계중 |
| 4 | POST | /api/documents | 설계중 |
| 5 | PUT | /api/documents/{id} | 설계중 |
| 6 | WebSocket | /ws/chat | 설계중 |

### 1-2. 실제 코드에 존재하는 엔드포인트

| # | 메서드 | 엔드포인트 | 파일 |
|---|--------|-----------|------|
| 1 | GET | /health | main.py |
| 2 | POST | /api/v1/auth/google | endpoints/auth.py |
| 3 | GET | /api/v1/auth/me | endpoints/auth.py |
| 4 | POST | /api/v1/conversations | endpoints/conversations.py |
| 5 | GET | /api/v1/conversations | endpoints/conversations.py |
| 6 | GET | /api/v1/conversations/{id} | endpoints/conversations.py |
| 7 | WebSocket | /ws/chat | endpoints/chat.py |
| 8 | WebSocket | /ws/voice | endpoints/voice.py |

### 1-3. 불일치 목록

| # | 항목 | Notion 명세서 | 실제 코드 | 불일치 유형 | 조치 필요 |
|---|------|-------------|----------|-----------|----------|
| A1 | URL prefix | `/api/auth/google` | `/api/v1/auth/google` | 경로 불일치 | 명세서에 `/v1` prefix 반영 필요 |
| A2 | /auth/me | 없음 | `GET /api/v1/auth/me` (현재 유저 정보) | 코드에만 존재 | 명세서에 추가 필요 |
| A3 | /documents CRUD | `/api/documents`, `/api/documents/{id}` (GET/POST/PUT) | 존재하지 않음 | 명세서에만 존재 | Sprint 3에서 구현 예정인지 확인 필요. 현재는 conversations 모델만 존재 |
| A4 | /conversations CRUD | 없음 | `POST/GET /api/v1/conversations`, `GET /api/v1/conversations/{id}` | 코드에만 존재 | 명세서에 추가 필요 |
| A5 | /ws/voice | 없음 | `WebSocket /ws/voice` | 코드에만 존재 | 명세서에 추가 필요 |
| A6 | /health | 없음 | `GET /health` | 코드에만 존재 | 명세서에 추가 (낮은 우선순위) |
| A7 | 명세서 상태 | 모든 항목이 "설계중" | Sprint 1~2에서 auth/chat은 이미 구현 완료 | 상태 미갱신 | auth/google, ws/chat의 상태를 "구현완료"로 업데이트 |
| A8 | 명세서 상세 정보 | 설명/요청/응답 필드가 모두 비어있음 | 코드에 스키마 정의 완료 | 상세 정보 누락 | 요청/응답 스키마 정보 채워야 함 |

### 1-4. 스키마 불일치 상세

명세서의 documents 관련 엔드포인트는 실제 코드에 전혀 대응하는 구현이 없다. 현재 코드에는 `documents` 모델 자체가 없고, `conversations` + `messages` 모델로 대화를 관리하고 있다.

**핵심 문제**: 명세서는 "문서(documents)" 중심 CRUD를 설계했지만, 실제 구현은 "대화(conversations)" 중심으로 진행되었다. 이는 도메인 모델의 근본적 차이이며, 기능명세서의 "대화 내용 문서화" 기능이 아직 미구현이기 때문으로 보인다.

---

## 2. FE 화면 라우팅 대조

### 2-1. Stitch 디자인에 존재하는 화면 (모바일 기준, 중복/변형 제외)

| # | Stitch 화면명 | 기능 |
|---|-------------|------|
| 1 | Login | Google OAuth 로그인 |
| 2 | Chat (Empty / Active) | 텍스트 채팅 (빈 상태 + 대화 진행 상태) |
| 3 | Voice Mode (Light) | 음성 대화 |
| 4 | 내 문서 (Menu) | 문서 목록 |
| 5 | 내 문서 (삭제 컨펌) / Doc Delete Confirm | 문서 삭제 확인 다이얼로그 |
| 6 | 문서 상세 | 문서 상세 보기 |
| 7 | 설정 (텍스트 제거) | 설정 화면 |
| 8 | Sidebar (Refined Footer) | 사이드바 네비게이션 |
| 9 | Knowledge Graph (Max Context) | 문서 간 관계 그래프 시각화 |
| 10 | Chat Home (Web) | 웹 채팅 홈 (대화 목록 + 새 대화) |
| 11 | Untitled Prototype | 미정의 프로토타입 |

### 2-2. 실제 FE 라우트

| # | 경로 | 컴포넌트 | 인증 필요 |
|---|------|---------|----------|
| 1 | /login | LoginPage | No |
| 2 | /chat | ChatRoom | Yes |
| 3 | /voice | VoicePage | Yes |
| 4 | /conversations | ConversationList | Yes |
| 5 | /conversations/:id | ConversationDetail | Yes |

### 2-3. 불일치 목록

| # | 항목 | Stitch 디자인 | 실제 FE | 불일치 유형 | 조치 필요 |
|---|------|-------------|---------|-----------|----------|
| F1 | 문서 목록 | "내 문서" 화면 있음 | 없음 (/conversations 목록은 "대화" 목록) | 디자인에만 존재 | documents 기능 구현 시 추가 필요 |
| F2 | 문서 상세 | "문서 상세" 화면 있음 | 없음 (/conversations/:id는 "대화" 상세) | 디자인에만 존재 | documents 기능 구현 시 추가 필요 |
| F3 | 문서 삭제 | 삭제 컨펌 다이얼로그 디자인 있음 | 없음 | 디자인에만 존재 | documents CRUD 구현 시 추가 필요 |
| F4 | 설정 화면 | 설정 화면 디자인 있음 (모바일+웹) | 없음 | 디자인에만 존재 | 별도 라우트 /settings 추가 필요 |
| F5 | 사이드바 | Sidebar 디자인 있음 | 없음 | 디자인에만 존재 | 웹 레이아웃에 사이드바 네비게이션 추가 필요 |
| F6 | Knowledge Graph | 그래프 시각화 화면 있음 | 없음 | 디자인에만 존재 | P1 기능, Graph RAG 구현 후 추가 |
| F7 | Chat Home (웹) | 대화 목록 + 새 대화 시작이 한 화면 | /conversations와 /chat이 별도 라우트 | 화면 구조 차이 | 웹 버전에서는 Chat Home 통합 레이아웃 고려 필요 |
| F8 | ConversationList | 디자인에 명시적 대응 없음 | /conversations 라우트 존재 | 코드에만 존재 | Stitch "Chat Home (Web)"이 이에 대응할 가능성 있음, 확인 필요 |
| F9 | ConversationDetail | 디자인에 명시적 대응 없음 | /conversations/:id 라우트 존재 | 코드에만 존재 | 디자인의 "문서 상세"와 다른 개념 (대화 히스토리 보기) |

---

## 3. DB 모델 대조

### 3-1. 실제 DB 모델

**User** (`users` 테이블)
- id (UUID, PK), email, name, provider, provider_id, created_at, last_login

**Conversation** (`conversations` 테이블)
- id (UUID, PK), user_id (FK → users), mode (text/voice), title, created_at, ended_at

**Message** (`messages` 테이블)
- id (UUID, PK), conversation_id (FK → conversations), role (user/ai), content, audio_url, created_at

### 3-2. 기능명세서에서 요구하는 데이터 구조

| 기능 | 필요 데이터 | 현재 DB 상태 |
|------|-----------|------------|
| Google OAuth 로그인 | user profile (email, name) | User 모델로 충족 |
| 텍스트 입력/AI 응답 | 대화 세션, 메시지 | Conversation + Message 모델로 충족 |
| 음성 대화 | 오디오 스트림, 트랜스크립트 | Message.audio_url 필드 있으나 실제 저장 로직 미구현 |
| 대화 내용 문서화 | 문서 {title, content, keywords[], embedding} | **Document 모델 없음** |
| 본문 열람 | 문서 상세 {title, content, keywords[], related_docs[]} | **Document 모델 없음** |
| 문서 목록 보기 | 문서 리스트 [{id, title, keywords[], created_at}] | **Document 모델 없음** |
| 문서 간 관계 시각화 | 그래프 {nodes[], edges[]} + pgvector 유사도 | **Document 모델 없음, pgvector 미활용** |

### 3-3. 불일치 목록

| # | 항목 | 기능명세서 | 실제 코드 | 조치 필요 |
|---|------|----------|----------|----------|
| D1 | Document 모델 | title, content, keywords[], embedding, created_at | 존재하지 않음 | Sprint 3에서 Document 모델 + CRUD 구현 필요 |
| D2 | pgvector 활용 | 문서 임베딩 저장 + 유사도 검색 | Docker에 pgvector 설정만 존재, 실제 벡터 컬럼 없음 | Document 모델에 embedding 컬럼 추가 필요 |
| D3 | keywords | 문서별 키워드 배열 | 없음 | Document에 keywords JSONB 또는 별도 테이블 필요 |
| D4 | related_docs | 문서 간 관계 | 없음 | pgvector 유사도 기반 관계 또는 별도 관계 테이블 필요 |
| D5 | audio_url 저장 | 음성 대화 원본 오디오 파일 URL | Message.audio_url 컬럼은 있으나, voice.py에서 저장 로직 없음 | 오디오 파일 저장 서비스 구현 필요 |

---

## 4. 종합 요약

### 심각도별 분류

#### [Critical] 도메인 모델 불일치
기능명세서와 디자인은 **"문서(Document)"** 를 핵심 도메인 객체로 설계했지만, 현재 코드에는 Document 모델이 전혀 없다. 이는 Sprint 1~2가 "대화(Conversation)" 파이프라인 구축에 집중했기 때문이며, Sprint 3에서 해결해야 할 가장 큰 갭이다.

영향:
- API 명세서의 /api/documents/* 엔드포인트 5개 미구현
- Stitch 디자인의 "내 문서", "문서 상세", "삭제 컨펌" 화면 미구현
- pgvector 기반 Graph RAG 실험의 기반 데이터 구조 부재

#### [High] 명세서 업데이트 부재
Notion API 명세서가 Sprint 1~2 구현 결과를 반영하지 못하고 있다:
- 구현 완료된 엔드포인트 상태가 여전히 "설계중"
- /api/v1 prefix 미반영
- conversations CRUD, /auth/me, /ws/voice가 명세서에 없음
- 요청/응답 스키마 정보가 모두 비어있음

#### [Medium] 화면-라우트 불일치
- 설정 화면, 사이드바, Knowledge Graph 등 디자인은 있으나 FE 코드 없음
- "대화 목록"과 "문서 목록"이 별개 개념인데 현재 혼용 가능성

#### [Low] 기타
- /health 엔드포인트 명세서 미등록
- audio_url 저장 로직 미구현 (스키마는 준비됨)

---

## 5. Sprint 3 제안 우선순위

1. **Notion API 명세서 업데이트** — 현재 코드 상태를 명세서에 반영 (Wave 0)
2. **Document 모델 + CRUD API 설계/구현** — 핵심 갭 해소
3. **"대화 내용 문서화" 서비스** — Conversation -> Document 변환 파이프라인
4. **FE 문서 관련 화면 구현** — 내 문서, 문서 상세
5. **설정 화면, 사이드바 네비게이션** — UX 기반 인프라
6. **Knowledge Graph** — P1, pgvector 실험과 연동
