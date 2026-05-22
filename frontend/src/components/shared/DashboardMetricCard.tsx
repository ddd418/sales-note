import type { LucideIcon } from 'lucide-react';

type DashboardMetricCardProps = {
  detail: string;
  href?: string;
  icon: LucideIcon;
  label: string;
  tone: 'blue' | 'green' | 'amber' | 'red' | 'teal';
  value: string;
};

export function DashboardMetricCard({
  detail,
  href,
  icon: Icon,
  label,
  tone,
  value,
}: DashboardMetricCardProps) {
  const content = (
    <>
      <div className="dashboard-metric-icon">
        <Icon size={19} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </>
  );

  if (href) {
    return (
      <a className={`dashboard-metric-card ${tone}`} href={href}>
        {content}
      </a>
    );
  }

  return <article className={`dashboard-metric-card ${tone}`}>{content}</article>;
}
