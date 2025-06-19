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
# 슈퍼유저 생성 (여러 방법 시도)
python manage.py create_admin || echo "create_admin failed, trying alternative method"
python create_user_debug.py || echo "create_user_debug failed, trying shell method"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='ddd418').exists():
    User.objects.create_superuser('ddd418', 'admin@company.com', '1676079051aA@!@')
    print('Superuser ddd418 created!')
else:
    print('User ddd418 already exists')
" || echo "All superuser creation methods failed"

echo "Deployment completed successfully!"
