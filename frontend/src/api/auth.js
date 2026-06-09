import apiClient from './client';

/**
 * 认证相关 API
 * 处理用户注册、登录、获取当前用户和更新资料等操作
 * 所有路径相对于 baseURL (/api)，不带前导 /
 */

/**
 * 用户注册
 * @param {Object} data - 注册信息 { username, email, password }
 * @returns {Promise<Object>} 注册成功的用户信息
 */
export const register = (data) => {
  return apiClient.post('auth/register', data);
};

/**
 * 用户登录
 * @param {Object} data - 登录凭证 { username, password }
 * @returns {Promise<Object>} 登录成功返回 { access_token, token_type, expires_in, user }
 */
export const login = (data) => {
  return apiClient.post('auth/login', data);
};

/**
 * 获取当前登录用户信息
 * 需要 Bearer Token 认证
 * @returns {Promise<Object>} 当前用户信息
 */
export const getCurrentUser = () => {
  return apiClient.get('auth/me');
};

/**
 * 更新用户资料
 * @param {Object} data - 要更新的用户字段 { bio, avatar_url }
 * @returns {Promise<Object>} 更新后的用户信息
 */
export const updateProfile = (data) => {
  return apiClient.put('auth/me', data);
};