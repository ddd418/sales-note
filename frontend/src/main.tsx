import React, { Suspense, useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';
import { CRM_CLIENT_NAVIGATION_EVENT } from './navigationEvents';

const root = ReactDOM.createRoot(document.getElementById('root')!);

const DashboardApp = React.lazy(async () => ({
  default: (await import('./DashboardApp')).DashboardApp,
}));
const CrmApp = React.lazy(async () => ({
  default: (await import('./App')).App,
}));

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

  const RootComponent = isDashboardRoute() ? DashboardApp : CrmApp;
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
