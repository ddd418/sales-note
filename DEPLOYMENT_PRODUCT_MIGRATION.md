# 제품 마이그레이션 배포 가이드

## 📋 개요

이 문서는 서버에 제품(Product) 기능을 배포하고 기존 데이터를 마이그레이션하는 절차를 설명합니다.

## ⚠️ 주의사항

- **반드시 순서대로 진행하세요**
- 서버 백업을 먼저 수행하세요
- 작업 전 Railway 데이터베이스 백업 필수

## 🔄 배포 절차

### 1단계: 서버 백업 (Railway)

```bash
# Railway 백업 수행 (로컬에서 실행)
cd backup
python railway_django_backup.py
```

### 2단계: 코드 배포

```bash
# Git에 변경사항 커밋 및 푸시
git add .
git commit -m "feat: 제품 마스터 기능 추가 및 DeliveryItem 연동"
git push origin main
```

### 3단계: Railway에서 마이그레이션 실행

Railway 대시보드 → 프로젝트 → Variables 탭에서 다음 명령 실행:

```bash
python manage.py migrate
```

또는 Railway CLI 사용:

```bash
railway run python manage.py migrate
```

### 4단계: 데이터 마이그레이션 스크립트 실행

마이그레이션 스크립트를 서버에 업로드하고 실행:

```bash
# Railway CLI로 스크립트 실행
railway run python migrate_delivery_items_to_products.py
```

스크립트가 수행하는 작업:

- ✅ Product가 없는 모든 DeliveryItem 조회
- ✅ item_name을 기준으로 Product 자동 생성
  - product_code = item_name
  - description = item_name (나중에 수동으로 수정 가능)
  - list_price/current_price = 평균 단가
- ✅ DeliveryItem과 Product 자동 연결

### 5단계: 검증

Railway 대시보드 또는 Admin 페이지에서 확인:

1. **Product 목록 확인**

   - URL: `/admin/reporting/product/`
   - 자동 생성된 제품들이 보이는지 확인

2. **DeliveryItem 확인**

   - URL: `/admin/reporting/deliveryitem/`
   - product 필드가 모두 채워졌는지 확인

3. **제품 관리 페이지 테스트**

   - URL: `/reporting/products/`
   - 견적/판매 횟수가 정상 표시되는지 확인

4. **대시보드 테스트**
   - URL: `/reporting/dashboard/`
   - 제품별 매출 비중이 정상 표시되는지 확인

### 6단계: 제품 정보 수정 (선택사항)

Admin 페이지에서 자동 생성된 제품의 설명(description)을 사람이 읽기 쉬운 형태로 수정:

예시:

- `SO825.0100` → 설명: "스마트 마이크로 피펫 100μL"
- `SO825.0200` → 설명: "스마트 마이크로 피펫 200μL"

## 🐛 문제 해결

### Q1: 마이그레이션 실패 시

```bash
# 마이그레이션 상태 확인
railway run python manage.py showmigrations

# 특정 앱만 마이그레이션
railway run python manage.py migrate reporting
```

### Q2: Product가 생성되지 않음

```bash
# 수동으로 확인
railway run python manage.py shell
>>> from reporting.models import DeliveryItem
>>> DeliveryItem.objects.filter(product__isnull=True).count()
```

### Q3: 스크립트 실행 오류

- Railway 로그 확인: Railway 대시보드 → Deployments → Logs
- 로컬에서 먼저 테스트: `python migrate_delivery_items_to_products.py`

## 📊 예상 결과

### 마이그레이션 전

```
DeliveryItem:
- item_name: "SO825.0100"
- product: null
- unit_price: 425000
```

### 마이그레이션 후

```
Product:
- product_code: "SO825.0100"
- description: "SO825.0100"
- current_price: 425000

DeliveryItem:
- item_name: "SO825.0100"
- product: Product(SO825.0100)
- unit_price: 425000
```

## ✅ 체크리스트

배포 완료 후 확인:

- [ ] Railway 데이터베이스 백업 완료
- [ ] 마이그레이션 성공
- [ ] 데이터 마이그레이션 스크립트 실행 완료
- [ ] Product 생성 확인
- [ ] DeliveryItem-Product 연결 확인
- [ ] 제품 관리 페이지 정상 작동
- [ ] 대시보드 제품 매출 비중 정상 표시
- [ ] 견적/납품 일정에서 품목 정상 표시

## 🔙 롤백 방법

문제 발생 시:

1. Railway에서 이전 배포로 롤백
2. 백업 파일에서 데이터베이스 복원:
   ```bash
   # backup/ 폴더의 최신 백업 파일 사용
   railway run python manage.py loaddata backup/railway_backup_YYYYMMDD_HHMM.json
   ```

## 📝 추가 노트

- 제품 마스터는 Admin 페이지(`/admin/reporting/product/`)에서 관리 가능
- CSV 대량 업로드는 향후 구현 예정
- 제품별 견적/판매 통계는 `status='completed'` 일정 기준으로 계산됨
