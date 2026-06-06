import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import { LoggerProvider } from '@/context/logger-context';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LoggerProvider>
      <App />
    </LoggerProvider>
  </React.StrictMode>,
);
