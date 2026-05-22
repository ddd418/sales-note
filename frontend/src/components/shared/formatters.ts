export const formatWon = (value: number) =>
  new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);

export const formatSignedWon = (value: number) => {
  if (value > 0) return `+${formatWon(value)}`;
  if (value < 0) return `-${formatWon(Math.abs(value))}`;
  return formatWon(0);
};

export const formatNumber = (value: number) => new Intl.NumberFormat('ko-KR').format(value);

export const formatSignedNumber = (value: number) => `${value > 0 ? '+' : ''}${formatNumber(value)}`;

export const formatDateLabel = (value?: string | null) => {
  if (!value) return '';
  const datePart = /^\d{4}-\d{2}-\d{2}/.test(value) ? value.slice(0, 10) : value;
  const [year, month, day] = datePart.split('-');
  if (!year || !month || !day) return value;
  return `${Number(month)}월 ${Number(day)}일`;
};

export const formatDateTimeLabel = (value?: string | null) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};
