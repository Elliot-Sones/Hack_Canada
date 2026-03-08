import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import ModelViewerHarness from './dev/ModelViewerHarness.jsx';
import './index.css';
import { Auth0Provider } from "@auth0/auth0-react";

const isViewerHarness = new URLSearchParams(window.location.search).get('viewerHarness') === '1';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isViewerHarness ? (
      <ModelViewerHarness />
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
