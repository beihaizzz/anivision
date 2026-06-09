import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import router from './router';
import useAuthStore from './store/useAuthStore';

/**
 * AniVision 根应用组件
 *
 * 功能：
 * - 应用启动时自动恢复用户认证状态（从 localStorage 读取 token 并获取用户信息）
 * - 配置 Ant Design 全局主题和中文国际化
 * - 提供路由渲染
 */
const App = () => {
  const { token, fetchCurrentUser } = useAuthStore();

  // 应用启动时：如果存在 token，则异步获取用户信息恢复登录态
  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, []); // 仅在挂载时执行一次

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          // Ant Design 全局主题定制
          colorPrimary: '#FF6B6B',
          colorSuccess: '#4ECDC4',
          colorWarning: '#FFE66D',
          borderRadius: 8,
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        },
      }}
    >
      <RouterProvider router={router} />
    </ConfigProvider>
  );
};

export default App;
