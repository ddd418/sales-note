#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Railway deployment..."

pip install -r requirements.txt

echo "Running collectstatic..."
python manage.py collectstatic --no-input --clear
# 정적 파일 권한 설정
find staticfiles -type f -name "*.css" -exec chmod 644 {} \;
find staticfiles -type f -name "*.js" -exec chmod 644 {} \;

echo "Running migrations..."
python manage.py migrate

echo "Skipping superuser creation. Create or rotate admin users through an environment-specific runbook."

echo "Deployment completed successfully!"
