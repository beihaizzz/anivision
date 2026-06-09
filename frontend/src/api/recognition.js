import apiClient from './client';

/**
 * 图像识别相关 API
 * 所有路径相对于 baseURL (/api)，不带前导 /
 */

/**
 * 上传图片进行动漫角色识别
 * @param {File} file - 要识别的图片文件
 * @returns {Promise<Object>} 识别任务信息
 */
export const uploadImage = (file) => {
  const formData = new FormData();
  formData.append('file', file);

  return apiClient.post('recognition/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    // 上传超时时间延长到 60 秒
    timeout: 60000,
  });
};

/**
 * 获取识别任务结果
 * @param {string|number} id - 识别任务 ID
 * @returns {Promise<Object>} 识别结果，包含 Top-K 匹配角色
 */
export const getRecognition = (id) => {
  return apiClient.get(`recognition/${id}`);
};

/**
 * 获取用户识别历史记录
 * @param {number} [page=1] - 页码
 * @param {number} [size=10] - 每页条数
 * @returns {Promise<Object>} 分页的历史记录 { items, total, page, size }
 */
export const getHistory = (page = 1, size = 10) => {
  return apiClient.get('recognition/history', {
    params: { page, size },
  });
};