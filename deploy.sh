#!/bin/bash
set -e
cd /opt/poisv
git pull origin main
/opt/poisv/venv/bin/pip install -q fastapi uvicorn pydantic python-dateutil
systemctl restart poisv-api
echo "Deploy OK $(date -u)"
