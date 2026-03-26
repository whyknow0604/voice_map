# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요
Voice Map은 지식 근로자가 머릿속 아이디어를 말로 뱉으면, AI가 구조화하고 문서로 쌓아주는 "사고 외장 하드" 서비스다.

- **표면적 목적:** 일반 지식 근로자의 아이디어 손실 문제 해결
- **실험적 목적:** Graph RAG 유효성 검증 → 그린메이트(코지메이커스 메인 서비스) 이식
- **배포 전략:** GitHub 오픈소스

## 개발 환경 설정 및 실행

### 사전 요구사항
- Node.js, Python 3.11+, Docker

### DB 시작 (PostgreSQL + pgvector)
```bash
docker compose up -d
```

### Backend
```bash
cd backend
pip install -r requirements.txt
# DB 마이그레이션
alembic upgrade head
# 새 마이그레이션 생성
alembic revision --autogenerate -m "설명"
# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # Vite dev server (localhost:5173)
npm run build        # tsc + vite build
npm run lint         # ESLint
npm run type-check   # tsc --noEmit
```

### Backend 테스트
```bash
cd backend
pytest                      # 전체 테스트
pytest tests/test_auth.py   # 단일 파일
pytest -k "test_name"       # 단일 테스트
```
- `asyncio_mode = "auto"` 설정됨 — async 테스트에 `@pytest.mark.asyncio` 불필요
- httpx AsyncClient로 API 테스트

### Backend 린트
```bash
cd backend
ruff check .         # 린트
ruff check . --fix   # 자동 수정
```
- ruff 설정: line-length 100, select `["E", "F", "I", "W"]` (pyproject.toml)

### 환경변수
루트의 `.env` 파일 사용 (`.env.example` 참고). Backend config가 `../.env`를 읽으므로 반드시 프로젝트 루트에 위치해야 함.
- Notion Hook용: `NOTION_API_KEY`, `NOTION_DB_SUBTASK`, `NOTION_DB_DECISION_LOG` 등 (`scripts/hooks/notion/config.py`가 참조)
- Hook Python 의존성: `pip install -r scripts/hooks/notion/requirements.txt`

## 아키텍처

### 기술 스택
- Frontend: React 18 + TypeScript + Vite + Capacitor (모바일 하이브리드)
- Backend: Python 3.11+ FastAPI (비동기)
- AI: Gemini API (텍스트: 소크라테스식 대화) + Gemini Live API (양방향 음성)
- DB: PostgreSQL 16 + pgvector (Graph RAG 실험), async SQLAlchemy 2.0 + Alembic

### Backend 구조 (`backend/app/`)
- `main.py` — FastAPI 앱 생성, CORS, 라우터 등록
- `core/config.py` — pydantic-settings 기반 설정 (`Settings` 싱글톤)
- `db/session.py` — async SQLAlchemy 엔진 + `get_db()` dependency
- `db/base.py` — SQLAlchemy `DeclarativeBase`
- `models/` — DB 모델 (Alembic이 `app.models` import하여 자동 감지)
- `schemas/` — Pydantic v2 요청/응답 스키마
- `services/` — 비즈니스 로직
- `api/v1/endpoints/` — API 라우터 (`/api/v1/` prefix)

### Frontend 구조 (`frontend/src/`)
- `App.tsx` — BrowserRouter 기반 라우팅
- `services/api.ts` — axios 인스턴스 (토큰 자동 첨부, 401 시 리디렉션)
- Vite가 `/api` → `localhost:8000`, `/ws` → `ws://localhost:8000` 프록시 처리
- `@` alias = `./src`

### Agent Teams (실험적 기능)

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 환경변수로 활성화. `.claude/settings.local.json`에 설정됨.

**에이전트 구성 (`.claude/agents/`)**
- `tech-lead` (opus) — 오케스트레이터. Notion MCP 독점, 팀원 spawn, merge 관리
- `frontend` (sonnet) — React + Capacitor UI 구현
- `backend` (sonnet) — FastAPI API/DB/인증 구현, `shared/types/` 소유
- `ai-knowledge` (sonnet) — Gemini API 연동, 프롬프트 설계
- `qa` (sonnet) — 통합 테스트 시점에만 spawn

**Skill 구성 (`.claude/skills/`)**
- 공통: `common` (Git 컨벤션, 디렉토리 규칙, 코드 품질)
- Agent별: `frontend-agent`, `backend-agent`, `ai-knowledge-agent`, `tech-lead-agent`
- Notion: `notion-sprint-sync`, `notion-spec-reader`, `notion-decision-logger` (tech-lead 전용)

**역할 분리 원칙**: Agent 파일 = 팀 내 커뮤니케이션/오케스트레이션만, Skill 파일 = 도메인 지식/코딩 컨벤션. 중복 금지.

**Merge 순서**: ai-knowledge → backend → frontend (의존 방향)

## 코드 컨벤션

### Git
- 커밋: `[Agent] type: 설명` (예: `[BE] feat: Google OAuth 엔드포인트 구현`)
  - Agent 태그: `[FE]`, `[BE]`, `[AI]`, `[TL]`
  - type: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- 브랜치: `sprint-N/agent/feature-name` (예: `sprint-1/be/google-oauth`)
- PR 단위: 서브태스크 1개 = PR 1개

### Frontend (TypeScript)
- 함수형 컴포넌트 + Hooks
- 컴포넌트 파일명: PascalCase (예: `ChatRoom.tsx`)
- 상태 관리: React Context (규모 확장 시 Zustand 검토)
- API 통신: `services/api.ts`의 axios 인스턴스 사용

### Backend (Python)
- 타입 힌트 필수
- FastAPI dependency injection 패턴
- Pydantic v2 스키마 검증
- 비동기 처리: async/await 기본
- 에러 응답: HTTPException으로 일관된 에러 처리

## Notion 연동
모든 기획/관리 문서는 Notion에 있다. 작업 전 반드시 확인할 것. Notion MCP는 tech-lead 에이전트만 직접 사용한다.

| 문서 | URL |
|---|---|
| 00. 대시보드 | https://www.notion.so/32cb1ba6f418812ea315f5ed56a0ed58 |
| 01. 서비스 기획서 | https://www.notion.so/32cb1ba6f41881888710ef66f3858426 |
| 02. 기능 명세서 | https://www.notion.so/fae77560a88140b3b54652a2e208fabf |
| 03. API 명세서 | https://www.notion.so/4deb7187a03e419f8a60710301bf7349 |
| 04. 버전 관리 | https://www.notion.so/ea48cbc1387b43f9a2c43a6f048cbf4b |
| 05. 의사결정 로그 | https://www.notion.so/c0a23822df13405eb318b4c42079479a |
| 06. 서브태스크 | https://www.notion.so/aa3e485d3c7d4a19a6dd2fe7e8d1d492 |

## 작업 규칙
1. 작업 전: Notion 06.서브태스크 DB에서 완료 기준/실패 기준 확인
2. 작업 시작: 서브태스크 상태를 "진행중"으로 업데이트
3. 작업 완료: 서브태스크 상태를 "리뷰중" 또는 "완료"로 업데이트
4. 의사결정 발생 시: 05.의사결정 로그 DB에 즉시 기록
5. API 설계 확정 시: 03.API 명세서 DB 업데이트

## Hooks (자동화)

`scripts/hooks/` 디렉토리. `.claude/settings.local.json`의 `hooks` 필드에 등록됨.

- **TaskCompleted** → `on-task-completed.sh` → `notion/update_kanban.py`
  - 태스크 완료 시 Notion 06.서브태스크의 상태/구현요약/커밋참조를 자동 업데이트
  - 환경변수: `CLAUDE_TASK_NAME`, `CLAUDE_TASK_AGENT`, `CLAUDE_TASK_SUMMARY`
  - Notion API 직접 호출 (MCP 아님) → `.env`에 `NOTION_API_KEY` 필요
- **TeammateIdle** → `on-teammate-idle.sh` (현재 pass-through, 향후 자동 태스크 배정 확장)

Hook은 에이전트 컨텍스트 밖에서 실행되므로 토큰을 소비하지 않는다.
