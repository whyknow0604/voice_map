# Voice Map — Agent Team Workflow 정의

## 4-Agent 구조 개요

```
민호 (Tech Lead / PM)
  ├── Frontend Agent   — React + Capacitor UI 구현
  ├── Backend Agent    — FastAPI + DB + 인증
  └── AI Knowledge Agent — Gemini API, 프롬프트, Graph RAG
```

Tech Lead(민호)가 아키텍처 의사결정, 코드 리뷰, 스프린트 관리를 겸임한다.

## 워크플로우 흐름

### 1. 태스크 할당 (Tech Lead)
```
Notion 06.서브태스크 → 담당 Agent 배정 → 상태: "대기" → "진행중"
```

### 2. 개발 사이클 (각 Agent)
```
① Notion에서 태스크 확인 (완료 기준 / 실패 기준)
② 브랜치 생성: sprint-N/agent/feature-name
③ 코드 구현
④ 자체 테스트
⑤ PR 생성 → 상태: "리뷰중"
```

### 3. 리뷰 & 통합 (Tech Lead)
```
① PR 코드 리뷰
② 통합 테스트 (E2E)
③ 머지 승인 → main 브랜치
④ Notion 상태 업데이트: "완료"
```

### 4. 블로커 처리
```
블로커 발생 → Notion 상태: "블로커" + 비고에 원인
→ Tech Lead가 판단 → 우회 / 재설계 / 의존성 해소
→ 05.의사결정 로그에 기록
```

## Agent별 워크플로우 상세

### Frontend Agent
- **입력:** 기능 명세서 UI 스펙, API 명세서
- **출력:** React 컴포넌트, 페이지, 라우팅
- **테스트:** 브라우저 렌더링 확인, 반응형 체크
- **핸드오프:** PR 생성 후 Tech Lead 리뷰 요청

### Backend Agent
- **입력:** API 명세서, DB 스키마 설계
- **출력:** FastAPI 엔드포인트, DB 모델, 마이그레이션
- **테스트:** pytest 단위/통합 테스트, API 문서 자동 생성
- **핸드오프:** PR 생성 후 Tech Lead 리뷰 요청, API 명세서 업데이트

### AI Knowledge Agent
- **입력:** 서비스 기획서 (대화 톤, 소크라테스식 질문 방식)
- **출력:** 시스템 프롬프트, Gemini 연동 코드, RAG 파이프라인
- **테스트:** 프롬프트 품질 검증, 응답 일관성 체크
- **핸드오프:** 프롬프트는 `backend/app/prompts/`에 저장, PR 생성

### Tech Lead
- **입력:** 모든 Agent의 PR, 통합 이슈
- **출력:** 코드 리뷰 코멘트, 아키텍처 결정, 스프린트 회고
- **테스트:** E2E 파이프라인 테스트
- **기록:** 의사결정 로그, 버전 관리 업데이트

## 브랜치 전략

```
main                          ← 안정 브랜치 (스프린트 종료 시 태그)
 └── sprint-1/be/users-schema ← 서브태스크 단위 브랜치
 └── sprint-1/fe/login-ui
 └── sprint-1/ai/system-prompt
 └── sprint-1/be/google-oauth
```

## 의사결정 프로세스
1. Agent가 구현 중 설계 선택지가 생기면 → Tech Lead에게 문의
2. Tech Lead가 판단 후 → 05.의사결정 로그에 기록
3. 결정 사항은 CLAUDE.md 또는 해당 Skill에 반영

## 스프린트 종료 체크리스트
- [ ] 모든 서브태스크 "완료" 상태
- [ ] E2E 테스트 통과
- [ ] 04.버전 관리 업데이트
- [ ] 회고 기록
- [ ] 다음 스프린트 태스크 확인
