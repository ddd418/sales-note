import { lazy, Suspense, type ComponentProps, type ComponentType, type ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

export function LazyPageBoundary({ children }: { children: ReactNode }) {
  return (
    <Suspense
      fallback={(
        <section className="dashboard-loading">
          <Loader2 className="spin-icon" size={24} />
          <span>화면을 불러오는 중입니다</span>
        </section>
      )}
    >
      {children}
    </Suspense>
  );
}

/**
 * 화면 컴포넌트를 "그 화면을 열 때만" 내려받게 감싼다.
 * props 타입은 원래 컴포넌트 그대로 유지되고, 로딩 중엔 공용 로딩 표시가 뜬다.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function lazyPage<T extends ComponentType<any>>(load: () => Promise<T>) {
  const LazyComponent = lazy(async () => ({ default: await load() }));
  function LazyPage(props: ComponentProps<T>) {
    return (
      <LazyPageBoundary>
        <LazyComponent {...props} />
      </LazyPageBoundary>
    );
  }
  return LazyPage;
}
