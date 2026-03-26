#!/usr/bin/env bash
# ============================================
# Voice Map - TeammateIdle Hook
# ============================================
# Agent Teams의 TeammateIdle 이벤트 시 실행된다.
# 팀원이 할당된 태스크를 모두 끝내고 idle 상태에 진입할 때 호출된다.
#
# exit code:
#   0 - idle 허용 (더 이상 할 일 없음)
#   2 - idle 거부 (계속 작업하도록 유도)
#
# 현재는 단순히 idle을 허용한다.
# 추후 unblocked 태스크 자동 배정 로직을 추가할 수 있다.

set -euo pipefail

# 현재는 idle 허용
# TODO: shared task list에서 unblocked + unassigned 태스크가 있으면
#       exit 2를 반환하여 팀원이 자동으로 다음 태스크를 claim하도록 유도
exit 0
