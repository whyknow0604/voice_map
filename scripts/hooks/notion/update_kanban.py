"""
Voice Map - Notion 칸반 보드 업데이트
TaskCompleted Hook에서 호출되어 서브태스크 상태를 업데이트한다.

사용법:
    python update_kanban.py --task-name "태스크명" --status "완료" \
        --agent "frontend" --summary "구현 요약 내용" \
        [--commit-url "https://github.com/..."]
"""

import argparse
import re
import sys
from datetime import datetime

import requests

from config import (
    DB_SUBTASK,
    GIT_REMOTE_URL,
    HEADERS,
    NOTION_BASE_URL,
    AGENT_NAMES,
    TASK_STATUS,
)


def normalize_task_name(name: str) -> str:
    """태스크명을 정규화: [BE] 등 접두사 제거, 공백 통일, 소문자 변환."""
    name = re.sub(r"^\[(?:FE|BE|AI|TL)\]\s*", "", name.strip())
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name


def find_task_page(task_name: str, agent: str) -> str | None:
    """서브태스크 DB에서 태스크명과 담당 Agent로 페이지를 찾는다.

    4단계 폴백 매칭:
    1. exact title + agent select (기존)
    2. exact title만 (agent 무시)
    3. 접두사 제거 후 contains + 정규화 비교
    4. 정규화된 이름으로 contains 검색
    """
    url = f"{NOTION_BASE_URL}/databases/{DB_SUBTASK}/query"
    agent_name = AGENT_NAMES.get(agent, agent)

    # 1단계: exact title + agent
    payload = {
        "filter": {
            "and": [
                {"property": "태스크명", "title": {"equals": task_name}},
                {"property": "담당 Agent", "select": {"equals": agent_name}},
            ]
        }
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    results = response.json().get("results", [])
    if results:
        print(f"[DEBUG] 1단계 매칭 성공: exact + agent")
        return results[0]["id"]

    # 2단계: exact title만
    payload = {
        "filter": {"property": "태스크명", "title": {"equals": task_name}}
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    results = response.json().get("results", [])
    if results:
        print(f"[DEBUG] 2단계 매칭 성공: exact title (agent 무시)")
        return results[0]["id"]

    # 3단계: 접두사 제거 후 contains
    cleaned = normalize_task_name(task_name)
    if cleaned != task_name.strip().lower():
        payload = {
            "filter": {"property": "태스크명", "title": {"contains": cleaned}}
        }
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        results = response.json().get("results", [])
        for r in results:
            title_parts = r["properties"]["태스크명"]["title"]
            notion_title = "".join(t["plain_text"] for t in title_parts)
            if normalize_task_name(notion_title) == cleaned:
                print(f"[DEBUG] 3단계 매칭 성공: 정규화 비교 '{notion_title}'")
                return r["id"]

    # 4단계: 정규화된 이름의 핵심 키워드로 contains 검색
    keywords = cleaned.split()
    if len(keywords) >= 2:
        search_term = " ".join(keywords[:3])
        payload = {
            "filter": {"property": "태스크명", "title": {"contains": search_term}}
        }
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        results = response.json().get("results", [])
        if len(results) == 1:
            title_parts = results[0]["properties"]["태스크명"]["title"]
            notion_title = "".join(t["plain_text"] for t in title_parts)
            print(f"[DEBUG] 4단계 매칭 성공: 키워드 '{search_term}' → '{notion_title}'")
            return results[0]["id"]

    print(f"[DEBUG] 모든 매칭 단계 실패: '{task_name}' (정규화: '{cleaned}')")
    return None


def update_task(
    page_id: str,
    status: str,
    summary: str = "",
    commit_url: str = "",
) -> bool:
    """서브태스크 페이지의 상태, 구현 요약, 커밋 참조를 업데이트한다."""
    url = f"{NOTION_BASE_URL}/pages/{page_id}"
    properties: dict = {}

    # 상태 업데이트
    if status:
        notion_status = TASK_STATUS.get(status, status)
        properties["상태"] = {"select": {"name": notion_status}}

    # 구현 요약 업데이트
    if summary:
        properties["구현 요약"] = {
            "rich_text": [{"text": {"content": summary[:2000]}}]
        }

    # 커밋 참조 업데이트
    if commit_url:
        properties["커밋 참조"] = {"url": commit_url}

    if not properties:
        return True

    response = requests.patch(url, headers=HEADERS, json={"properties": properties})
    response.raise_for_status()
    return True


def get_latest_commit_url() -> str:
    """git log에서 최신 커밋의 URL을 생성한다."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()
        if commit_hash and GIT_REMOTE_URL:
            return f"{GIT_REMOTE_URL}/commit/{commit_hash}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return ""


def main():
    parser = argparse.ArgumentParser(description="Notion 칸반 보드 업데이트")
    parser.add_argument("--task-name", required=True, help="태스크명")
    parser.add_argument("--status", default="completed", help="상태 (completed/review/blocked)")
    parser.add_argument("--agent", required=True, help="담당 에이전트 (frontend/backend/ai-knowledge)")
    parser.add_argument("--summary", default="", help="구현 요약")
    parser.add_argument("--commit-url", default="", help="커밋 URL (비어있으면 자동 추출)")
    args = parser.parse_args()

    # 커밋 URL 자동 추출
    commit_url = args.commit_url or get_latest_commit_url()

    # 태스크 찾기
    page_id = find_task_page(args.task_name, args.agent)
    if not page_id:
        print(f"[WARN] 태스크를 찾을 수 없음: '{args.task_name}' (agent: {args.agent})")
        sys.exit(0)  # Hook은 실패해도 전체 흐름을 막지 않음

    # 업데이트
    try:
        update_task(page_id, args.status, args.summary, commit_url)
        print(f"[OK] Notion 업데이트 완료: '{args.task_name}' → {args.status}")
    except requests.HTTPError as e:
        print(f"[ERROR] Notion API 오류: {e}")
        sys.exit(0)  # Hook 실패가 개발 흐름을 막지 않도록


if __name__ == "__main__":
    main()
