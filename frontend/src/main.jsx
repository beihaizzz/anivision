import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

/**
 * AniVision 应用入口
 *
 * 使用 React 18 createRoot API 渲染应用
 * Ant Design 组件已在 App 中通过 ConfigProvider 全局配置
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
