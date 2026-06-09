import { create } from 'zustand';
import * as authApi from '../api/auth';

/**
 * AniVision 认证状态管理 (Zustand)
 *
 * 管理用户认证状态：登录、注册、登出、获取当前用户信息
 * Token 持久化到 localStorage，刷新页面后自动恢复
 */

const useAuthStore = create((set, get) => ({
  // ===== 状态 =====
  /** 当前登录用户信息 */
  user: null,
  /** JWT Token */
  token: localStorage.getItem('token') || null,
  /** 是否已认证 */
  isAuthenticated: !!localStorage.getItem('token'),
  /** 加载状态 */
  loading: false,
  /** 错误信息 */
  error: null,

  // ===== 计算属性辅助 =====
  /** 用户是否已登录 */
  getIsLoggedIn: () => get().isAuthenticated,

  // ===== 操作 =====

  /**
   * 用户登录
   * @param {Object} credentials - { username, password }
   */
  login: async (credentials) => {
    set({ loading: true, error: null });
    try {
      const response = await authApi.login(credentials);
      // 后端返回 access_token，映射为内部 token 字段
      const { access_token, user } = response;

      // 持久化 token 到 localStorage
      localStorage.setItem('token', access_token);

      set({
        user,
        token: access_token,
        isAuthenticated: true,
        loading: false,
        error: null,
      });

      return response;
    } catch (error) {
      const message =
        error.response?.data?.detail || error.message || '登录失败，请重试';
      set({ loading: false, error: message });
      throw error;
    }
  },

  /**
   * 用户注册
   * @param {Object} data - { username, email, password }
   */
  register: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await authApi.register(data);
      set({ loading: false, error: null });
      return response;
    } catch (error) {
      const message =
        error.response?.data?.detail || error.message || '注册失败，请重试';
      set({ loading: false, error: message });
      throw error;
    }
  },

  /**
   * 退出登录
   * 清除本地 token 和用户状态，跳转到首页
   */
  logout: () => {
    localStorage.removeItem('token');

    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    });

    // 跳转到首页
    window.location.href = '/';
  },

  /**
   * 获取当前登录用户信息
   * 用于页面刷新后恢复用户状态
   */
  fetchCurrentUser: async () => {
    const { token } = get();
    if (!token) return;

    set({ loading: true });
    try {
      const user = await authApi.getCurrentUser();
      set({ user, loading: false });
    } catch (error) {
      // Token 无效时清除认证状态
      localStorage.removeItem('token');
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
      });
    }
  },

  /**
   * 更新用户资料
   * @param {Object} data - 更新的字段
   */
  updateProfile: async (data) => {
    set({ loading: true, error: null });
    try {
      const user = await authApi.updateProfile(data);
      set({ user, loading: false });
      return user;
    } catch (error) {
      const message =
        error.response?.data?.detail || error.message || '更新失败';
      set({ loading: false, error: message });
      throw error;
    }
  },

  /**
   * 清除错误信息
   */
  clearError: () => set({ error: null }),
}));

export default useAuthStore;
