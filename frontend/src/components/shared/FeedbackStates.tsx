import { AlertTriangle, Loader2 } from 'lucide-react';

export function DashboardLoading({ label }: { label: string }) {
  return (
    <section className="dashboard-loading">
      <Loader2 className="spin-icon" size={24} />
      <span>{label}</span>
    </section>
  );
}

export function DashboardEmpty({ label }: { label: string }) {
  return <div className="dashboard-empty">{label}</div>;
}

// 서버/네트워크 오류 원문("Customers API unavailable: 502", "Failed to fetch")은 사용자가
// 읽을 수 없다. 한글 메시지(서버가 준 업무 메시지)는 그대로 두고 기술 문구만 바꾼다.
export function humanizeApiError(message?: string | null): string {
  const raw = (message || '').trim();
  if (!raw || raw === 'login_required') return '로그인이 필요합니다.';
  if (/[가-힣]/.test(raw)) return raw;
  const status = Number(raw.match(/\b(\d{3})\b/)?.[1] || 0);
  if (status === 401 || status === 403) return '로그인이 만료됐습니다. 다시 로그인해 주세요.';
  if (status >= 500) return '서버가 잠시 응답하지 않습니다. 잠시 후 새로고침해 주세요.';
  if (/failed to fetch|networkerror|load failed/i.test(raw)) return '네트워크 연결을 확인한 뒤 다시 시도해 주세요.';
  return status ? `데이터를 불러오지 못했습니다. (코드 ${status})` : '데이터를 불러오지 못했습니다.';
}

export function DashboardApiAlert({
  actionHref = '/reporting/login/',
  actionLabel = '로그인',
  message,
  title,
}: {
  actionHref?: string;
  actionLabel?: string;
  message?: string | null;
  title: string;
}) {
  return (
    <div className="dashboard-api-alert">
      <AlertTriangle size={18} />
      <div>
        <strong>{title}</strong>
        <span>{humanizeApiError(message)}</span>
      </div>
      <a href={actionHref}>{actionLabel}</a>
    </div>
  );
}

