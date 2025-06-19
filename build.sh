#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# 슈퍼유저 자동 생성 (없을 경우에만)
python create_superuser.py
