import { Button, Result } from 'antd';
import { useNavigate } from 'react-router-dom';

/**
 * AniVision 404 页面
 *
 * 当用户访问不存在的路由时显示此页面，
 * 提供返回首页的快捷操作。
 */
const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 'calc(100vh - 64px - 70px - 48px)',
      }}
    >
      <Result
        status="404"
        title="404 - 页面未找到"
        subTitle="抱歉，您访问的页面不存在或已被移除。"
        extra={
          <Button
            type="primary"
            size="large"
            onClick={() => navigate('/')}
            style={{
              borderRadius: 8,
              background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
              border: 'none',
            }}
          >
            返回首页
          </Button>
        }
        style={{ padding: '40px 20px' }}
      />
    </div>
  );
};

export default NotFoundPage;
