"""
Voice Map - Notion API 설정
.env에서 환경변수를 로드하고, DB ID 및 프로퍼티 매핑을 제공한다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# Notion API
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Notion DB IDs
DB_SUBTASK = os.getenv("NOTION_DB_SUBTASK", "")
DB_DECISION_LOG = os.getenv("NOTION_DB_DECISION_LOG", "")
DB_VERSION = os.getenv("NOTION_DB_VERSION", "")
DB_FEATURE_SPEC = os.getenv("NOTION_DB_FEATURE_SPEC", "")
DB_API_SPEC = os.getenv("NOTION_DB_API_SPEC", "")

# Notion Page IDs
PAGE_DASHBOARD = os.getenv("NOTION_PAGE_DASHBOARD", "")
PAGE_SERVICE_PLAN = os.getenv("NOTION_PAGE_SERVICE_PLAN", "")
PAGE_PROJECT_ROOT = os.getenv("NOTION_PAGE_PROJECT_ROOT", "")

# Git Remote URL (커밋 참조 링크 생성용)
GIT_REMOTE_URL = os.getenv("GIT_REMOTE_URL", "")

# 공통 헤더
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# 서브태스크 상태 매핑
TASK_STATUS = {
    "pending": "대기",
    "in_progress": "진행중",
    "review": "리뷰중",
    "completed": "완료",
    "blocked": "블로커",
}

# 에이전트 이름 매핑
AGENT_NAMES = {
    "tech-lead": "Tech Lead",
    "frontend": "Frontend",
    "backend": "Backend",
    "ai-knowledge": "AI Knowledge",
    "qa": "QA",
}
