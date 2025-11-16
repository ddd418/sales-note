# Bootstrap 모달 클릭 불가 문제 해결 프롬프트

## 증상

- 모달을 열면 옅은 회색 배경(modal-backdrop)만 보임
- 모달 컨텐츠가 보이지 않거나 클릭할 수 없음
- 개발자 도구에서 `<div class="modal-backdrop fade show"></div>`만 선택됨
- 모달 뒤에 있는 페이지 요소들도 클릭 불가

## 해결 프롬프트

```
Bootstrap 모달에서 backdrop이 모달 컨텐츠를 가려서 클릭할 수 없는 문제가 발생했습니다.

증상:
- 모달을 열면 회색 배경만 보이고 모달 내용을 클릭할 수 없음
- 개발자 도구에서 modal-backdrop만 선택됨

다음과 같이 수정해주세요:

1. modal-backdrop을 display: none으로 완전히 숨김
2. .modal에 pointer-events: none 적용 (컨테이너 투명화)
3. .modal-dialog에 pointer-events: auto 적용 (다이얼로그만 클릭 가능)
4. .modal-content와 내부 요소들에 pointer-events: auto 적용
5. 모달에 box-shadow 추가 (배경 없이도 돋보이게)

CSS 위치: [파일명] 파일의 상단 <style> 태그 내부
```

## 실제 적용된 CSS 코드 예시

```css
/* ============================================
   모달 Z-INDEX 및 오버레이 수정 (CRITICAL FIX)
   ============================================ */

/* backdrop을 완전히 투명하게 (배경 없음) */
.modal-backdrop {
  display: none !important; /* backdrop 자체를 숨김 */
}

/* 모달 자체는 backdrop보다 높게 */
.modal {
  z-index: 1055 !important;
  pointer-events: none !important; /* 모달 컨테이너도 투명하게 */
}

/* 모달 다이얼로그만 클릭 가능하게 */
.modal-dialog {
  z-index: 1056 !important;
  pointer-events: auto !important; /* 다이얼로그는 클릭 가능 */
}

/* 모달 컨텐츠를 확실히 클릭 가능하게 */
.modal-content {
  position: relative;
  z-index: 1057 !important;
  pointer-events: auto !important; /* 컨텐츠 클릭 가능 */
  background-color: #fff;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 0.3rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15); /* 모달에 그림자 추가 */
}

/* 모달 내부의 모든 요소가 클릭 가능하도록 */
.modal-header,
.modal-body,
.modal-footer,
.modal-header *,
.modal-body *,
.modal-footer * {
  pointer-events: auto !important;
}
```

## 적용 후 확인사항

1. **Ctrl+F5** (강력 새로고침)으로 캐시 클리어
2. 모달 열기 테스트
3. 개발자 도구(F12)로 확인:
   - `.modal-backdrop`이 `display: none`인지
   - `.modal-content`가 클릭 가능한지
   - 모달 내부 버튼들이 작동하는지

## 대안 (backdrop을 유지하고 싶은 경우)

```css
/* backdrop을 반투명하게 유지하면서 클릭만 불가능하게 */
.modal-backdrop {
  z-index: 1040 !important;
  pointer-events: none !important;
  opacity: 0.5 !important; /* 원하는 투명도 */
  background-color: rgba(0, 0, 0, 0.5) !important;
}
```

## 주의사항

- `!important`는 Bootstrap 기본 스타일을 덮어쓰기 위해 필요
- z-index 순서: backdrop(1040) < modal(1055) < dialog(1056) < content(1057)
- pointer-events 설정이 핵심: backdrop과 modal은 none, 나머지는 auto
