import { useState } from 'react';
import { Card, Form, Input, Button, Typography, message, Divider, Progress } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const { Title, Text } = Typography;

/**
 * AniVision 注册页
 *
 * 功能：
 * - 用户名 / 邮箱 / 密码 / 确认密码 表单
 * - 实时密码强度检测（简单 / 中等 / 强）
 * - 表单校验（用户名格式、邮箱格式、密码复杂度）
 * - 注册成功后跳转到登录页
 */
const RegisterPage = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { register, loading } = useAuthStore();
  const [passwordStrength, setPasswordStrength] = useState(0);

  /**
   * 评估密码强度
   * @param {string} password - 密码
   * @returns {number} 0-100 的强度分数
   */
  const evaluatePasswordStrength = (password) => {
    if (!password) return 0;

    let score = 0;

    // 长度至少 8 位
    if (password.length >= 8) score += 25;
    // 长度至少 12 位
    if (password.length >= 12) score += 10;

    // 包含大写字母
    if (/[A-Z]/.test(password)) score += 20;
    // 包含小写字母
    if (/[a-z]/.test(password)) score += 15;
    // 包含数字
    if (/\d/.test(password)) score += 15;
    // 包含特殊字符
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 15;

    return Math.min(score, 100);
  };

  /**
   * 获取密码强度文本和颜色
   */
  const getStrengthInfo = (score) => {
    if (score >= 80) return { text: '强', color: '#52c41a', percent: score };
    if (score >= 50) return { text: '中等', color: '#faad14', percent: score };
    return { text: '简单', color: '#ff4d4f', percent: Math.max(score, 20) };
  };

  /**
   * 密码变更处理
   */
  const handlePasswordChange = (e) => {
    const value = e.target.value;
    setPasswordStrength(evaluatePasswordStrength(value));
  };

  /**
   * 提交注册表单
   */
  const handleSubmit = async (values) => {
    try {
      // 去除 confirmPassword 字段，API 不需要
      const { confirmPassword, ...registerData } = values;
      await register(registerData);
      message.success('注册成功！请登录您的账号 🎉');
      navigate('/login', { replace: true });
    } catch (error) {
      const errorMsg =
        error.response?.data?.detail || error.message || '注册失败，请重试';
      message.error(errorMsg);
    }
  };

  return (
    <div
      className="register-page"
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 'calc(100vh - 64px - 70px - 48px)',
        padding: '40px 20px',
      }}
    >
      <Card
        style={{
          width: 440,
          borderRadius: 12,
          boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
        }}
        bodyStyle={{ padding: '40px 32px' }}
      >
        {/* 标题 */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title
            level={2}
            style={{
              marginBottom: 8,
              background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            创建账号
          </Title>
          <Text type="secondary">加入 AniVision，探索动漫角色识别</Text>
        </div>

        {/* 注册表单 */}
        <Form
          form={form}
          name="register"
          onFinish={handleSubmit}
          autoComplete="off"
          size="large"
          layout="vertical"
        >
          {/* 用户名 */}
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少 3 个字符' },
              { max: 50, message: '用户名最多 50 个字符' },
              {
                pattern: /^[a-zA-Z0-9_]+$/,
                message: '用户名只能包含字母、数字和下划线',
              },
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="用户名（3-50位字母/数字/下划线）"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          {/* 邮箱 */}
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<MailOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="邮箱地址"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          {/* 密码 */}
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 8, message: '密码至少 8 个字符' },
              {
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                message: '密码必须包含大写字母、小写字母和数字',
              },
            ]}
            extra={
              passwordStrength > 0 ? (
                <div style={{ marginTop: 8 }}>
                  <Progress
                    percent={getStrengthInfo(passwordStrength).percent}
                    strokeColor={getStrengthInfo(passwordStrength).color}
                    size="small"
                    showInfo={false}
                  />
                  <Text style={{ fontSize: 12, color: getStrengthInfo(passwordStrength).color }}>
                    密码强度：{getStrengthInfo(passwordStrength).text}
                  </Text>
                </div>
              ) : null
            }
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="密码（8位以上，含大小写字母+数字）"
              onChange={handlePasswordChange}
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          {/* 确认密码 */}
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="确认密码"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          {/* 提交按钮 */}
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: 44,
                borderRadius: 8,
                fontSize: 16,
                background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
                border: 'none',
                marginTop: 8,
              }}
            >
              注册
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>
          <Text type="secondary" style={{ fontSize: 13 }}>
            已有账号？
          </Text>
        </Divider>

        {/* 登录链接 */}
        <div style={{ textAlign: 'center' }}>
          <Link to="/login">
            <Button
              type="link"
              size="large"
              style={{ fontSize: 15 }}
            >
              立即登录
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default RegisterPage;
