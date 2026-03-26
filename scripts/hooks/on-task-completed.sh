#!/usr/bin/env bash
# ============================================
# Voice Map - TaskCompleted Hook
# ============================================
# Agent Teams의 TaskCompleted 이벤트 시 실행된다.
# 팀원이 태스크를 완료하면 Notion 칸반 보드를 자동 업데이트한다.
#
# 환경변수 (Hook이 자동으로 제공):
#   CLAUDE_TASK_NAME     - 완료된 태스크명
#   CLAUDE_TASK_AGENT    - 태스크를 완료한 에이전트명
#   CLAUDE_TASK_SUMMARY  - 완료 메모/요약
#
# exit code:
#   0 - 완료 허용
#   2 - 완료 거부 (품질 게이트로 사용 가능)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTION_DIR="${SCRIPT_DIR}/notion"

# 환경변수에서 태스크 정보 읽기
TASK_NAME="${CLAUDE_TASK_NAME:-}"
TASK_AGENT="${CLAUDE_TASK_AGENT:-}"
TASK_SUMMARY="${CLAUDE_TASK_SUMMARY:-}"

# 태스크 정보가 없으면 조용히 종료
if [ -z "$TASK_NAME" ]; then
    exit 0
fi

# Notion 칸반 업데이트 실행
python3 "${NOTION_DIR}/update_kanban.py" \
    --task-name "$TASK_NAME" \
    --status "completed" \
    --agent "$TASK_AGENT" \
    --summary "$TASK_SUMMARY" \
    2>&1 || true

# exit 0 = 완료 허용
exit 0
