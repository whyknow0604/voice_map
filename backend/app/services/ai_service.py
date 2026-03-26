"""
AI 서비스 — 프롬프트 버전 관리 및 조회

향후 A/B 테스트를 위해 버전 기반으로 프롬프트를 선택할 수 있도록 설계.
"""

from app.prompts.system_chat_v1 import SYSTEM_PROMPT_V1

# 버전 → 프롬프트 매핑 레지스트리
# 새 버전 추가 시 이 딕셔너리에 등록하고 CURRENT_VERSION을 업데이트
_PROMPT_REGISTRY: dict[str, str] = {
    "v1": SYSTEM_PROMPT_V1,
}

CURRENT_VERSION: str = "v1"


def get_system_prompt(version: str = CURRENT_VERSION) -> str:
    """지정한 버전의 시스템 프롬프트를 반환한다.

    Args:
        version: 프롬프트 버전 식별자 (예: "v1"). 기본값은 현재 활성 버전.

    Returns:
        시스템 프롬프트 문자열.

    Raises:
        ValueError: 존재하지 않는 버전을 요청한 경우.
    """
    if version not in _PROMPT_REGISTRY:
        available = ", ".join(_PROMPT_REGISTRY.keys())
        raise ValueError(f"알 수 없는 프롬프트 버전: '{version}'. 사용 가능한 버전: {available}")
    return _PROMPT_REGISTRY[version]


def list_prompt_versions() -> list[str]:
    """등록된 모든 프롬프트 버전 목록을 반환한다."""
    return list(_PROMPT_REGISTRY.keys())
