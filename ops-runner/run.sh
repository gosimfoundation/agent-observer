#!/usr/bin/env bash
# Runs the task named in ops-runner/TASK. Tasks print results only; they never
# print credentials (GitHub also masks every secret passed through env).
set -euo pipefail
cd "$(dirname "$0")/.."
task="$(tr -d '[:space:]' < ops-runner/TASK)"
case "$task" in
  ''|*/*|*..*) echo "invalid task name" >&2; exit 2 ;;
esac
echo "task: $task (commit $(git rev-parse --short HEAD))"
exec bash "ops-runner/tasks/$task.sh"
