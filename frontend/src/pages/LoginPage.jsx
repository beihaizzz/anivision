import { Card, Form, Input, Button, Typography, message, Divider } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const { Title, Text } = Typography;

/**
 * AniVision 登录页
 *
 * 功能：
 * - 用户名 + 密码登录表单
 * - 表单校验
 * - 登录成功后自动跳转（优先跳 redirect 参数，否则首页）
 * - 提供注册页跳转链接
 */
const LoginPage = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, loading } = useAuthStore();

  // 跳转目标：登录成功后重定向到此路径
  const redirectTo = searchParams.get('redirect') || '/';

  /**
   * 提交登录表单
   */
  const handleSubmit = async (values) => {
    try {
      await login(values);
      message.success('登录成功！欢迎回来 👋');
      // 登录成功后跳转到目标页面
      navigate(redirectTo, { replace: true });
    } catch (error) {
      // 错误已在 store 中处理，此处展示错误消息
      const errorMsg =
        error.response?.data?.detail || error.message || '登录失败，请检查用户名和密码';
      message.error(errorMsg);
    }
  };

  return (
    <div
      className="login-page"
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
          width: 400,
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
            欢迎回来
          </Title>
          <Text type="secondary">登录您的 AniVision 账号</Text>
        </div>

        {/* 登录表单 */}
        <Form
          form={form}
          name="login"
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
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="用户名"
              style={{ borderRadius: 8 }}
            />
          </Form.Item>

          {/* 密码 */}
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="密码"
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
              登录
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>
          <Text type="secondary" style={{ fontSize: 13 }}>
            还没有账号？
          </Text>
        </Divider>

        {/* 注册链接 */}
        <div style={{ textAlign: 'center' }}>
          <Link to="/register">
            <Button
              type="link"
              size="large"
              style={{ fontSize: 15 }}
            >
              立即注册
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
