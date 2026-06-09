import axios from 'axios';

/**
 * AniVision API 客户端
 * Axios 实例，配置基础URL、JWT拦截器、错误处理
 */

// 创建 Axios 实例
// 开发环境: baseURL = '/api'，由 Vite proxy 转发到 http://localhost:8000
// 生产环境: 通过环境变量 VITE_API_BASE_URL 设置后端地址
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 请求拦截器 - 自动附加 JWT Token
 * 从 localStorage 读取 token 并添加到 Authorization 请求头
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器 - 统一错误处理
 * - 401/403: Token 过期或无效，清除认证状态并跳转登录页
 * - 其他错误: 直接抛出，由调用方处理
 */
apiClient.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response) {
      const { status } = error.response;

      // Token 过期或未授权 - 清除本地认证信息并重定向到登录页
      if (status === 401 || status === 403) {
        localStorage.removeItem('token');
        // 如果页面不在登录页，则跳转（避免无限重定向）
        if (window.location.pathname !== '/login') {
          window.location.href = `/login?redirect=${encodeURIComponent(
            window.location.pathname
          )}`;
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
