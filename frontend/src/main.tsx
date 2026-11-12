import React, { Suspense, useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css';
import './styles.css';
import { CRM_CLIENT_NAVIGATION_EVENT } from './navigationEvents';

const root = ReactDOM.createRoot(document.getElementById('root')!);

const DashboardApp = React.lazy(async () => ({
  default: (await import('./DashboardApp')).DashboardApp,
}));
const CrmApp = React.lazy(async () => ({
  default: (await import('./App')).App,
}));

const PipelineMeetingPage = React.lazy(async () => ({
  default: (await import('./pages/pipelineMeeting/PipelineMeetingPage')).PipelineMeetingPage,
}));

const ServiceReportPage = React.lazy(async () => ({
  default: (await import('./pages/services/ServiceReportPage')).ServiceReportPage,
}));

// 수리완료보고서는 인쇄용이라 메뉴(셸) 없이 띄운다
function isServiceReportRoute() {
  return /^\/services\/\d+\/report\/?$/.test(window.location.pathname);
}

function isMeetingRoute() {
  return window.location.pathname.startsWith('/pipeline-meeting');
}

function isDashboardRoute() {
  const pathname = window.location.pathname.replace(/\/+$/, '/') || '/';
  return pathname.startsWith('/dashboard/');
}

function RootRouter() {
  const [, setRouteChangeSignal] = useState(0);

  useEffect(() => {
    const refreshRoute = () => setRouteChangeSignal((value) => value + 1);
    window.addEventListener('popstate', refreshRoute);
    window.addEventListener(CRM_CLIENT_NAVIGATION_EVENT, refreshRoute);
    return () => {
      window.removeEventListener('popstate', refreshRoute);
      window.removeEventListener(CRM_CLIENT_NAVIGATION_EVENT, refreshRoute);
    };
  }, []);

  const RootComponent = isServiceReportRoute()
    ? ServiceReportPage
    : isMeetingRoute() ? PipelineMeetingPage : isDashboardRoute() ? DashboardApp : CrmApp;
  return (
    <Suspense fallback={null}>
      <RootComponent />
    </Suspense>
  );
}

root.render(
  <React.StrictMode>
    <RootRouter />
  </React.StrictMode>,
);
