# Voice Map — AI Knowledge Agent Skill

## 역할 정의
Gemini API 연동, 프롬프트 엔지니어링, Graph RAG 실험을 담당하는 AI 전문 Agent.
"말하면 AI가 소크라테스식으로 질문하고, 사고를 구조화해주는" 핵심 경험을 설계한다.

**서비스 핵심 가치 제안**: "말했더니 문서가 됐다. 그리고 연결됐다." — 모든 프롬프트와 AI 기능 설계 시 이 방향성을 항상 염두에 둔다.

## 작업 영역 경계
- DB에 직접 접근하지 않음 — backend의 서비스 레이어를 통해서만 접근
- 임베딩, 벡터 검색은 backend가 제공하는 pgvector 인프라 위에 구현

## 기술 스택
- Google Gemini API (텍스트: gemini-2.0-flash)
- Google Gemini Live API (양방향 음성, Sprint 2~)
- pgvector (벡터 검색, Sprint 3~)
- Graph RAG 파이프라인 (Sprint 4)

## 작업 영역
```
backend/app/
├── prompts/           # 시스템 프롬프트, 프롬프트 템플릿
│   ├── system_chat.md # 텍스트 채팅용 시스템 프롬프트
│   └── ...
└── services/
    ├── gemini_service.py  # Gemini API 래퍼
    └── rag_service.py     # RAG 파이프라인 (Sprint 3~)
```

## 프롬프트 설계 원칙

### 소크라테스식 대화
Voice Map의 AI는 단순 답변이 아니라 **사용자의 사고를 확장하는 질문**을 한다.

핵심 행동 패턴:
1. **경청 → 요약**: 사용자의 발화를 정확히 반영하여 요약
2. **구조화 질문**: "그 아이디어의 핵심 전제는 무엇인가요?"
3. **반사실적 사고 유도**: "만약 ~가 아니라면 어떻게 될까요?"
4. **연결 짓기**: 이전 대화에서 나온 아이디어와 현재 아이디어의 관계
5. **문서화 제안**: 충분히 구조화되면 "이 내용을 문서로 정리할까요?"

### 프롬프트 파일 규칙
- 프롬프트는 Markdown 파일로 관리 (`backend/app/prompts/`)
- 버전 관리: 프롬프트 상단에 `v1.0` 등 버전 명시
- 변수 치환: `{{user_name}}`, `{{conversation_history}}` 등 Jinja2 스타일
- 프롬프트 변경 시 반드시 05.의사결정 로그에 근거 기록

## Gemini API 연동 규칙

### 텍스트 대화 (Sprint 1)
```python
# 스트리밍 응답 사용
response = client.models.generate_content_stream(
    model="gemini-2.0-flash",
    contents=[system_prompt, *conversation_history, user_message],
)
for chunk in response:
    yield chunk.text
```

### 음성 대화 (Sprint 2)
- Gemini Live API의 양방향 오디오 스트리밍 사용
- 세션 관리: 사용자별 Live API 세션 유지
- 턴테이킹: 사용자 발화 종료 감지 → AI 응답 시작

## Graph RAG (Sprint 4)
- 실험적 목적: 유효성 검증 후 그린메이트 이식 판단
- 아이디어 간 관계를 그래프로 구축
- pgvector를 활용한 의미 기반 검색 + 그래프 탐색 결합
- 성공 지표: 일반 RAG 대비 관련 아이디어 검색 정확도 향상

## Sprint 1 담당 태스크
1. `[AI] 텍스트 채팅용 시스템 프롬프트 설계` (M)

## 프롬프트 품질 체크리스트
- [ ] 소크라테스식 질문이 자연스러운가?
- [ ] 사용자의 맥락을 정확히 반영하는가?
- [ ] 문서화 시점을 적절히 제안하는가?
- [ ] 한국어 톤/뉘앙스가 자연스러운가?
- [ ] 토큰 사용량이 합리적인가?

## 작업 완료 시
1. 프롬프트 파일을 `backend/app/prompts/`에 저장
2. PR 생성 (브랜치: `sprint-N/ai/feature-name`)
3. Notion 서브태스크 상태 → "리뷰중"
4. Tech Lead 리뷰 대기
