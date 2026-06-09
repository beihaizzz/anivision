import { Layout, Typography } from 'antd';
import { HeartFilled } from '@ant-design/icons';

const { Footer } = Layout;
const { Text, Link } = Typography;

/**
 * AniVision 页脚组件
 *
 * 显示版权信息，固定在页面底部
 */
const AppFooter = () => {
  const currentYear = new Date().getFullYear();

  return (
    <Footer
      style={{
        textAlign: 'center',
        background: '#fff',
        borderTop: '1px solid #f0f0f0',
        padding: '20px 50px',
      }}
    >
      <div>
        <Text type="secondary" style={{ fontSize: 14 }}>
          AniVision — 基于深度学习的动漫角色图像识别系统
        </Text>
      </div>
      <div style={{ marginTop: 4 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          &copy; {currentYear} AniVision. Made with{' '}
          <HeartFilled style={{ color: '#FF6B6B' }} /> by Team AniVision
        </Text>
      </div>
    </Footer>
  );
};

export default AppFooter;
