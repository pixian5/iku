#!/usr/bin/env bash
set -euo pipefail
cd /home/x/fuwu/ikuuu

# 加载环境变量（如果存在 .env 文件）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

exec .venv/bin/python -u ikuuu自动签到.py
