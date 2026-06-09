import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

/**
 * 路由守卫 - 受保护路由组件
 *
 * 功能：
 * - 检查用户认证状态
 * - 未登录用户自动重定向到登录页，并在 URL 参数中保存目标路径
 * - 已登录用户正常渲染子组件
 *
 * 使用方式：
 *   <ProtectedRoute>
 *     <YourProtectedPage />
 *   </ProtectedRoute>
 */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  // 未登录 → 重定向到登录页，带上 redirect 参数方便登录后跳回
  if (!isAuthenticated) {
    return (
      <Navigate
        to={`/login?redirect=${encodeURIComponent(location.pathname)}`}
        replace
      />
    );
  }

  // 已登录 → 正常渲染子组件
  return children;
};

export default ProtectedRoute;
