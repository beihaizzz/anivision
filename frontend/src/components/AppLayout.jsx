import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import AppHeader from './AppHeader';
import AppFooter from './AppFooter';

const { Content } = Layout;

/**
 * AniVision 主布局组件
 *
 * 使用 Ant Design Layout 构建统一的页面框架：
 * - 顶部固定导航头 (AppHeader)
 * - 中间内容区域 (<Outlet />)
 * - 底部版权信息 (AppFooter)
 */
const AppLayout = () => {
  return (
    <Layout className="app-layout" style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* 固定顶部导航 */}
      <AppHeader />

      {/* 主内容区 - 使用 React Router Outlet 渲染子路由页面 */}
      <Content
        style={{
          marginTop: 64,       // 补偿固定 Header 的高度
          padding: '24px',
          minHeight: 'calc(100vh - 64px - 70px)', // 减去 Header 和 Footer
        }}
      >
        <Outlet />
      </Content>

      {/* 底部版权信息 */}
      <AppFooter />
    </Layout>
  );
};

export default AppLayout;
