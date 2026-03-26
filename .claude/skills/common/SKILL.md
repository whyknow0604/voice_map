# Voice Map — 공통 Skill (모든 Agent 적용)

## 역할
이 Skill은 모든 Agent가 공통으로 따르는 규칙과 컨벤션을 정의한다.

## Notion 연동 규칙
1. **작업 시작 전**: 06.서브태스크 DB에서 해당 태스크의 완료 기준/실패 기준을 반드시 확인
2. **작업 시작**: 서브태스크 상태를 "진행중"으로 업데이트
3. **작업 완료**: 서브태스크 상태를 "리뷰중" 또는 "완료"로 업데이트
4. **블로커 발생**: 상태를 "블로커"로 변경 + 비고에 원인 기록
5. **의사결정 발생**: 05.의사결정 로그 DB에 즉시 기록

## Git 컨벤션
### 커밋 메시지
```
[Agent] type: 설명

예시:
[BE] feat: Google OAuth 인증 엔드포인트 구현
[FE] fix: 로그인 페이지 리다이렉트 오류 수정
[AI] docs: 시스템 프롬프트 v1 문서화
[TL] refactor: API 응답 스키마 통일
```
- Agent 태그: `[FE]`, `[BE]`, `[AI]`, `[TL]`
- type: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### 브랜치
```
sprint-{N}/{agent}/{feature-name}
예: sprint-1/be/google-oauth
```

### PR 규칙
- 서브태스크 1개 = PR 1개
- PR 제목: 서브태스크명과 동일
- PR 설명: 완료 기준 체크리스트 포함
- 리뷰어: Tech Lead

## 코드 품질
- 새 코드에는 반드시 타입 정의 (TypeScript / Python type hints)
- 핵심 비즈니스 로직에는 테스트 작성
- 주석은 "왜(why)"를 설명, "무엇(what)"은 코드로 표현
- 매직 넘버, 하드코딩 금지 → 설정으로 분리

## 파일/디렉토리 규칙
- Frontend 코드는 `frontend/` 하위에서만 작업
- Backend 코드는 `backend/` 하위에서만 작업
- 공유 타입은 `shared/types/`에 정의
- 환경변수는 `.env`에만 저장, 절대 코드에 하드코딩하지 않을 것

## 에러 처리 표준
- Backend: HTTPException으로 일관된 에러 응답
- Frontend: try-catch + 사용자 친화적 에러 메시지
- WebSocket: 재연결 로직 필수, 에러 시 graceful degradation
