import { createBrowserRouter } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import ProtectedRoute from '../components/ProtectedRoute';

// 页面组件
import HomePage from '../pages/HomePage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import RecognizePage from '../pages/RecognizePage';
import NotFoundPage from '../pages/NotFoundPage';

/**
 * AniVision 路由配置
 *
 * 路由结构:
 *   /              - 首页
 *   /login         - 登录页
 *   /register      - 注册页
 *   /recognize     - 识别页（需登录）
 *   *              - 404 页面
 *
 * 所有页面包裹在 AppLayout 中，共享统一的布局（Header + Footer）
 */
const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      {
        path: 'recognize',
        element: (
          <ProtectedRoute>
            <RecognizePage />
          </ProtectedRoute>
        ),
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);

export default router;
