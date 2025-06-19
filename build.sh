#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting Railway deployment..."

pip install -r requirements.txt

echo "Running collectstatic..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Creating superuser..."
# 슈퍼유저 생성 (Django 관리 명령어 사용)
python manage.py create_admin

echo "Deployment completed successfully!"
