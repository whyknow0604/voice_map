"""
대화 요약/문서화 프롬프트 PoC 검증 스크립트

목적:
    summarize_v1.py 프롬프트의 품질을 3개 이상의 샘플 대화로 검증한다.
    각 샘플은 서로 다른 주제(기술 아이디어, 일상 고민, 업무 계획)를 다룬다.

실행 방법:
    cd backend
    python experiments/test_summarize_prompt.py

사전 요구사항:
    - 프로젝트 루트의 .env에 GEMINI_API_KEY 설정 필요
    - google-genai 패키지 설치 필요 (requirements.txt에 포함)

검증 결과 (v1.1, 2026-03-27):
    모델: gemini-2.0-flash
    샘플 수: 4 (기술 아이디어, 일상 고민, 업무 계획, 연구 아이디어)
    최종: 전체 PASS

    v1.0 → v1.1 변경 사유:
        v1.0에서 샘플 3 (업무 계획) title이 23자로 20자 제한 초과.
        원인: 프롬프트에 "20자를 초과하지 말 것"이라는 규칙이 있었으나,
              글자 수 검증 예시와 강조 문구가 없어 모델이 준수하지 않음.
        해결: title 규칙에 좋은 예/나쁜 예 추가 + 자기 검증 지시 추가.

    개선 방향 (Sprint 3 서비스 구현 시 고려):
        1. JSON 파싱 안정성: 모델이 마크다운 코드 블록으로 감싸는 경우가 있어
           후처리 로직 필요 (현재 스크립트에 구현됨).
        2. content 길이: 샘플 대화 길이에 따라 200~350자 범위로 일관성 확인됨.
           긴 대화에서 핵심만 압축하는 품질 추가 검증 권장.
        3. keywords 품질: 동의어/중복 키워드 방지 로직 고려.
           예: '알림 엔진'과 '알림'이 동시에 포함되는 경우 발생.
        4. 후처리 필요성: title 글자 수 초과는 v1.1에서 프롬프트 수준 해결.
           규칙 기반 후처리 없이도 일관된 품질 달성 — 실패 기준 해당 없음.
"""

import json
import sys
from pathlib import Path

# backend/ 를 sys.path에 추가하여 app 패키지 임포트 허용
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.prompts.summarize_v1 import SUMMARIZE_PROMPT_V1, SUMMARIZE_USER_TEMPLATE  # noqa: E402

# ---------------------------------------------------------------------------
# 샘플 대화 정의
# ---------------------------------------------------------------------------

SAMPLE_CONVERSATIONS = [
    {
        "name": "기술 아이디어 — 앱 알림 개선",
        "conversation": """\
[User]: 앱 알림 기능을 개선하면 좋겠어. 사람들이 알림을 너무 많이 받아서 무시하는 것 같아.
[AI]: 사용자들이 알림 과부하로 인해 정작 중요한 알림마저 놓치는 문제를 발견하셨군요. 이 문제에서 '너무 많다'는 게 핵심일까요, 아니면 '관련성이 낮다'는 게 더 근본적인 원인일까요?
[User]: 둘 다인 것 같아. 하지만 가장 큰 문제는 관련성이야. 내가 관심 없는 알림이 너무 많아. 사용자 행동 패턴을 학습해서 알림을 개인화하면 좋을 것 같아.
[AI]: 사용자 행동 기반 개인화가 핵심 방향이군요. 그렇다면 어떤 행동 데이터를 학습에 활용할 수 있을까요? 클릭률인지, 앱 체류 시간인지, 명시적 피드백인지에 따라 구현 방향이 달라질 것 같습니다.
[User]: 클릭률과 무시 횟수를 기반으로 하면 좋을 것 같아. 그리고 시간대별 패턴도 중요해. 사람마다 알림을 확인하는 시간이 다르니까.
[AI]: 행동 기반 데이터(클릭률, 무시 횟수)와 시간대 패턴을 결합한 개인화 알림 엔진이군요. 이 아이디어를 문서로 정리할까요?""",
    },
    {
        "name": "일상 고민 — 집중력 저하 문제",
        "conversation": """\
[User]: 요즘 집중이 너무 안 돼. 책상에 앉으면 30분도 못 버티고 핸드폰을 들여다보게 돼.
[AI]: 집중하려는 의지는 있지만 핸드폰 확인이 습관처럼 반복되는 상황이군요. 핸드폰을 들여다볼 때 주로 어떤 앱을 열게 되나요? 특정 트리거가 있는지 궁금합니다.
[User]: 주로 인스타그램이랑 유튜브. 알림이 오면 확인하게 되는데 알림이 없어도 그냥 습관적으로 열어.
[AI]: 알림 유무와 관계없이 습관적으로 열게 되는 거라면, 이건 외부 자극보다 내면의 루틴 문제에 가깝네요. 집중이 잘 됐던 때와 안 됐던 때를 비교하면 어떤 차이가 있었나요?
[User]: 마감이 있거나 완전히 몰입할 수 있는 주제면 잘 됐던 것 같아. 그리고 카페에서는 이상하게 더 잘 됨.
[AI]: 마감 압박, 흥미로운 주제, 환경 변화(카페)가 집중을 도왔다는 패턴이 보이네요. 이 세 가지 조건을 인위적으로 만들 수 있는 방법을 찾는 게 핵심 과제가 될 것 같습니다. 지금까지 나온 내용을 문서로 정리할까요?""",
    },
    {
        "name": "업무 계획 — 팀 온보딩 프로세스 개선",
        "conversation": """\
[User]: 새로운 팀원이 들어올 때마다 온보딩이 너무 오래 걸려. 3개월은 지나야 제대로 업무를 할 수 있는 것 같아.
[AI]: 온보딩에 3개월이 걸린다는 건 상당히 긴 시간이네요. 그 3개월 중 어느 단계에서 가장 많이 막히는 것 같나요? 기술적인 이해인지, 도메인 지식인지, 팀 문화인지 구분해보면 어떨까요?
[User]: 도메인 지식이 제일 큰 문제야. 우리 서비스가 복잡해서 전체 그림을 파악하는 데만 한 달이 걸려. 그리고 암묵지가 많아서 문서로 안 남아있는 게 많아.
[AI]: 암묵지가 문서화되지 않아 온보딩 병목이 생기는 상황이군요. 그 암묵지 중에 가장 중요한데 문서화가 안 된 것을 꼽는다면 어떤 것들이 있나요?
[User]: 의사결정 히스토리가 가장 큰 문제야. 왜 이렇게 설계했는지 아무도 모르는 경우가 많아. 그리고 팀 내 커뮤니케이션 규칙이나 암묵적인 기대치도.
[AI]: 의사결정 히스토리와 커뮤니케이션 규칙의 부재가 온보딩 병목의 핵심이군요. Architecture Decision Record(ADR)나 팀 노름 문서화를 고려해볼 수 있겠습니다. 이 내용을 온보딩 개선 계획으로 문서화할까요?""",
    },
    {
        "name": "연구 아이디어 — Graph RAG 활용",
        "conversation": """\
[User]: 일반 RAG는 단순 유사도 검색이라 맥락이 끊기는 문제가 있어. 아이디어들이 서로 연결되어 있는데 그 관계를 무시하고 각각 검색하는 거잖아.
[AI]: 일반 RAG가 개별 청크의 유사도만 보기 때문에 아이디어 간 관계와 맥락이 손실된다는 문제 인식이시군요. 어떤 종류의 관계가 특히 중요하게 보존되어야 할 것 같나요?
[User]: 인과관계가 제일 중요해. A가 B를 야기했다, 또는 A 때문에 B를 결정했다 이런 관계들. 그리고 시간적 선후 관계도 중요하고.
[AI]: 인과 관계와 시간적 선후 관계를 그래프로 모델링하면 단순 유사도 검색보다 훨씬 풍부한 맥락을 제공할 수 있겠군요. Graph RAG에서 노드는 아이디어/문서, 엣지는 관계 유형이 될 텐데, 어떤 방식으로 관계를 추출하고 엣지를 생성할 계획인가요?
[User]: LLM으로 대화에서 관계를 자동 추출하는 방식을 생각하고 있어. 그리고 검색 시 그래프 탐색을 벡터 검색과 결합해서 더 관련성 높은 결과를 뽑는 거지.
[AI]: LLM 기반 관계 추출 + 그래프 탐색 + 벡터 검색의 하이브리드 접근이군요. 성능 측정 지표는 어떻게 설정할 계획인가요? 일반 RAG 대비 어떤 기준으로 개선을 측정할지가 중요할 것 같습니다.""",
    },
]


# ---------------------------------------------------------------------------
# 검증 유틸리티
# ---------------------------------------------------------------------------


def format_conversation(conversation: str) -> str:
    """SUMMARIZE_USER_TEMPLATE에 대화를 삽입한다."""
    return SUMMARIZE_USER_TEMPLATE.format(conversation_history=conversation)


def validate_output(result: dict) -> list[str]:
    """추출 결과의 품질 기준 충족 여부를 검사하여 경고 목록을 반환한다."""
    warnings = []

    title = result.get("title", "")
    content = result.get("content", "")
    keywords = result.get("keywords", [])

    if len(title) > 20:
        warnings.append(f"title이 20자 초과: {len(title)}자 ({title!r})")
    if not title:
        warnings.append("title이 비어 있음")

    if not content:
        warnings.append("content가 비어 있음")
    if "핵심 문제" not in content and "핵심 아이디어" not in content and "##" not in content:
        warnings.append("content에 마크다운 구조가 없거나 예상 섹션 헤더 미포함")

    if not isinstance(keywords, list):
        warnings.append("keywords가 리스트가 아님")
    elif not (3 <= len(keywords) <= 7):
        warnings.append(f"keywords 개수가 범위 벗어남: {len(keywords)}개 (3~7 기대)")

    return warnings


# ---------------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------------


def run() -> None:
    """샘플 대화 전체를 순차적으로 실행하고 결과를 출력한다."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model = "gemini-2.0-flash"

    print("=" * 70)
    print("대화 요약/문서화 프롬프트 PoC 검증 (summarize_v1)")
    print("=" * 70)

    all_passed = True

    for i, sample in enumerate(SAMPLE_CONVERSATIONS, 1):
        name = sample["name"]
        conversation = sample["conversation"]

        print(f"\n[{i}/{len(SAMPLE_CONVERSATIONS)}] {name}")
        print("-" * 50)

        user_message = format_conversation(conversation)

        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=user_message)],
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SUMMARIZE_PROMPT_V1,
                ),
            )

            raw_text = response.text.strip()

            # JSON 파싱 시도
            try:
                # 모델이 마크다운 코드 블록으로 감싸는 경우 처리
                if raw_text.startswith("```"):
                    lines = raw_text.split("\n")
                    raw_text = "\n".join(lines[1:-1])

                result = json.loads(raw_text)
            except json.JSONDecodeError as e:
                print(f"  [FAIL] JSON 파싱 실패: {e}")
                print(f"  원본 응답:\n{response.text[:300]}")
                all_passed = False
                continue

            # 품질 검증
            warnings = validate_output(result)

            print(f"  title   : {result.get('title', '(없음)')}")
            print(f"  keywords: {result.get('keywords', [])}")
            print(f"  content 길이: {len(result.get('content', ''))}자")
            print()
            print("  [content 미리보기]")
            content_preview = result.get("content", "")[:300]
            for line in content_preview.split("\n"):
                print(f"    {line}")

            if warnings:
                print()
                print("  [경고]")
                for w in warnings:
                    print(f"    - {w}")
                all_passed = False
            else:
                print()
                print("  [PASS] 모든 품질 기준 충족")

        except Exception as e:  # noqa: BLE001
            print(f"  [ERROR] API 호출 실패: {e}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("최종 결과: 전체 PASS — 프롬프트 품질 기준 충족")
    else:
        print("최종 결과: 일부 FAIL — 위 경고/오류 확인 후 프롬프트 조정 필요")
    print("=" * 70)


if __name__ == "__main__":
    run()
