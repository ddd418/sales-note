import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles.css';

const root = ReactDOM.createRoot(document.getElementById('root')!);
const pathname = window.location.pathname.replace(/\/+$/, '/') || '/';

async function renderApp() {
  if (pathname.startsWith('/dashboard/')) {
    const { DashboardApp } = await import('./DashboardApp');
    root.render(
      <React.StrictMode>
        <DashboardApp />
      </React.StrictMode>,
    );
    return;
  }

  const { App } = await import('./App');
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
}

void renderApp();
