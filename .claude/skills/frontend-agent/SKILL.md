# Voice Map — Frontend Agent Skill

## 역할 정의
React + Capacitor로 Voice Map의 UI를 구현하는 Frontend 전담 Agent.
모바일 하이브리드 앱을 목표로, 반응형 + 네이티브 호환 UI를 만든다.

## 기술 스택
- React 18 + TypeScript
- Vite (빌드 도구)
- React Router v7 (라우팅)
- Axios (API 통신)
- Capacitor 6 (모바일 하이브리드)
- CSS Modules (스타일링)

## 디렉토리 구조
```
frontend/src/
├── components/    # 재사용 가능한 UI 컴포넌트
├── pages/         # 라우트 단위 페이지 컴포넌트
├── hooks/         # 커스텀 React Hooks
├── services/      # API 통신 레이어
├── styles/        # 글로벌 스타일, CSS 변수
└── utils/         # 유틸리티 함수
```

## 코딩 컨벤션

### 컴포넌트
- 함수형 컴포넌트 + Hooks만 사용 (class 컴포넌트 금지)
- 파일명: PascalCase (`ChatRoom.tsx`, `LoginPage.tsx`)
- 컴포넌트 하나당 파일 하나
- Props 타입은 컴포넌트 파일 내 상단에 정의
```tsx
interface ChatRoomProps {
  sessionId: string;
}

export default function ChatRoom({ sessionId }: ChatRoomProps) { ... }
```

### 상태 관리
- 로컬 상태: `useState`, `useReducer`
- 전역 상태: React Context (AuthContext, ChatContext 등)
- 서버 상태: 커스텀 Hook (`useAuth`, `useChat`)

### API 통신
- `frontend/src/services/api.ts`의 axios 인스턴스 사용
- API 호출은 반드시 커스텀 Hook으로 래핑
- API 응답 타입은 backend가 정의한 Pydantic 스키마(`shared/types/`)와 일치시킴
```tsx
// hooks/useAuth.ts
export function useAuth() {
  const login = async () => { ... };
  const logout = async () => { ... };
  return { login, logout, user };
}
```

### WebSocket
- WebSocket 연결은 전용 Hook으로 관리
- 재연결 로직 필수 (exponential backoff)
- 연결 상태를 UI에 반영 (연결중/연결됨/끊김)

## 모바일 고려사항 (Capacitor)
- Safe area 대응: `env(safe-area-inset-*)`
- 터치 타겟 최소 44px
- 키보드 올라올 때 레이아웃 대응
- 네이티브 뒤로가기 버튼 핸들링

## Sprint 1 담당 태스크
1. `[FE] 로그인 화면 UI + Google 로그인 버튼`
2. `[FE] ChatRoom UI + 스트리밍 응답 렌더링`

## 테스트 기준
- 컴포넌트 렌더링 확인
- 주요 사용자 인터랙션 동작 확인
- 에러 상태 UI 렌더링 확인

## 작업 완료 시
1. PR 생성 (브랜치: `sprint-N/fe/feature-name`)
2. Notion 서브태스크 상태 → "리뷰중"
3. Tech Lead 리뷰 대기
