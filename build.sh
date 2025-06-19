#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# 슈퍼유저 생성 (Django 관리 명령어 사용)
python manage.py create_admin
