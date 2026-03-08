import React, { lazy, Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';
import { Auth0Provider } from "@auth0/auth0-react";

const ModelViewerHarness = lazy(() => import('./dev/ModelViewerHarness.jsx'));
const isViewerHarness = new URLSearchParams(window.location.search).get('viewerHarness') === '1';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isViewerHarness ? (
      <Suspense fallback={<div>Loading...</div>}>
        <ModelViewerHarness />
      </Suspense>
    ) : (
      <Auth0Provider
        domain="dev-bygng1g0yro4tu2l.us.auth0.com"
        clientId="GlSAoYOOhldQR3IWURDQ9INEmZ5PXbt8"
        authorizationParams={{
          redirect_uri: window.location.origin,
        }}
        cacheLocation="localstorage"
        useRefreshTokens={true}
      >
        <App />
      </Auth0Provider>
    )}
  </React.StrictMode>
);
