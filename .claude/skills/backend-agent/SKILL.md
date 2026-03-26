# Voice Map — Backend Agent Skill

## 역할 정의
FastAPI로 Voice Map의 서버 사이드를 구현하는 Backend 전담 Agent.
REST API, WebSocket, DB, 인증을 담당한다.

## 기술 스택
- Python 3.11+ / FastAPI
- SQLAlchemy 2.0 (async) + Alembic
- PostgreSQL 16 + pgvector
- Pydantic v2 (스키마 검증)
- python-jose (JWT)
- httpx (외부 API 호출)
- websockets (실시간 통신)

## 소유 디렉토리
- `backend/` 하위 전체
- `shared/types/`, `shared/constants/` (공유 타입 정의 — 이 에이전트만 쓰기 권한 보유)

## 디렉토리 구조
```
backend/
├── app/
│   ├── api/v1/endpoints/  # 라우터 (auth.py, chat.py 등)
│   ├── core/              # 설정, 보안, 의존성
│   ├── models/            # SQLAlchemy ORM 모델
│   ├── schemas/           # Pydantic 요청/응답 스키마
│   ├── services/          # 비즈니스 로직 레이어
│   ├── db/                # DB 세션, Base
│   ├── prompts/           # AI 프롬프트 파일 (AI Agent와 공유)
│   └── main.py            # FastAPI 앱 팩토리
├── tests/                 # pytest 테스트
├── alembic/               # DB 마이그레이션
└── requirements.txt
```

## 코딩 컨벤션

### API 엔드포인트
- RESTful 원칙 준수
- 버전 프리픽스: `/api/v1/`
- 응답 스키마는 Pydantic 모델로 정의
- Dependency Injection으로 DB 세션, 현재 유저 등 주입
```python
@router.post("/auth/google", response_model=TokenResponse)
async def google_login(
    payload: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    ...
```

### DB 모델
- SQLAlchemy 2.0 Mapped 스타일 사용
- 테이블명: snake_case 복수형 (`users`, `conversations`, `messages`)
- `created_at`, `updated_at` 컬럼 필수
```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### 마이그레이션
- 모델 변경 시 Alembic revision 자동 생성
- 마이그레이션 파일에 설명적 메시지 포함
```bash
alembic revision --autogenerate -m "create users table"
alembic upgrade head
```

### WebSocket
- `/ws/chat/{session_id}` 경로 사용
- 인증: 쿼리 파라미터로 JWT 토큰 전달
- 메시지 포맷: JSON `{ "type": "message" | "error" | "status", "data": ... }`
- Gemini API 스트리밍 응답을 청크 단위로 전달

### 에러 처리
- HTTPException으로 일관된 에러 응답
```python
raise HTTPException(
    status_code=401,
    detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."}
)
```

## Sprint 1 담당 태스크
1. `[BE] users 테이블 스키마 + 마이그레이션` (S)
2. `[BE] Google OAuth 2.0 인증 엔드포인트 구현` (M)
3. `[BE] WebSocket 서버 + Gemini API 스트리밍 연동` (L)

## 테스트 기준
- pytest + httpx AsyncClient 사용
- 각 엔드포인트별 성공/실패 케이스 테스트
- DB 관련 테스트는 테스트용 DB 사용

## 작업 완료 시
1. PR 생성 (브랜치: `sprint-N/be/feature-name`)
2. API 명세서 (Notion 03번) 업데이트
3. Notion 서브태스크 상태 → "리뷰중"
4. Tech Lead 리뷰 대기
