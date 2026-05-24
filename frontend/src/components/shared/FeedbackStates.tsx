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

export function DashboardApiAlert({
  actionHref = '/reporting/login/',
  actionLabel = '로그인',
  message,
  title,
}: {
  actionHref?: string;
  actionLabel?: string;
  message: string;
  title: string;
}) {
  return (
    <div className="dashboard-api-alert">
      <AlertTriangle size={18} />
      <div>
        <strong>{title}</strong>
        <span>{message}</span>
      </div>
      <a href={actionHref}>{actionLabel}</a>
    </div>
  );
}

export function InlineErrorState({ message }: { message: string }) {
  return <div className="empty-state error">{message}</div>;
}

export function InlineEmptyState({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>;
}

