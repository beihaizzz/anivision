import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography } from 'antd';
import {
  HomeOutlined,
  ScanOutlined,
  TeamOutlined,
  UserOutlined,
  LoginOutlined,
  LogoutOutlined,
  HistoryOutlined,
  ProfileOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const { Header } = Layout;
const { Text } = Typography;

/**
 * AniVision 顶部导航头部组件
 *
 * 功能：
 * - 品牌 Logo "AniVision"
 * - 导航菜单：首页、识别、角色
 * - 右侧用户区域：
 *   - 未登录：显示登录/注册按钮
 *   - 已登录：头像 + 下拉菜单（个人主页、识别历史、退出登录）
 */
const AppHeader = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuthStore();

  // 导航菜单项
  const navItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/recognize',
      icon: <ScanOutlined />,
      label: '识别',
    },
    {
      key: '#',
      icon: <TeamOutlined />,
      label: '角色',
      disabled: true, // Phase 2 启用
    },
  ];

  // 根据当前路径确定选中的菜单项
  const selectedKey = '/' + (location.pathname.split('/')[1] || '');

  // 用户下拉菜单项
  const userMenuItems = [
    {
      key: 'profile',
      icon: <ProfileOutlined />,
      label: '我的主页',
    },
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: '识别历史',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ];

  // 处理下拉菜单点击
  const handleUserMenuClick = ({ key }) => {
    switch (key) {
      case 'profile':
        navigate('/profile');
        break;
      case 'history':
        navigate('/recognize');
        break;
      case 'logout':
        logout();
        break;
    }
  };

  return (
    <Header
      className="app-header"
      style={{
        position: 'fixed',
        top: 0,
        zIndex: 1000,
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 40px',
        background: '#fff',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}
    >
      {/* 左侧：Logo + 导航菜单 */}
      <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
        {/* Logo */}
        <div
          onClick={() => navigate('/')}
          style={{
            cursor: 'pointer',
            marginRight: 40,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <Text
            strong
            style={{
              fontSize: 22,
              background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AniVision 🎯
          </Text>
        </div>

        {/* 导航菜单 */}
        <Menu
          mode="horizontal"
          selectedKeys={[selectedKey]}
          items={navItems}
          onClick={({ key }) => {
            if (key !== '#') navigate(key);
          }}
          style={{
            flex: 1,
            border: 'none',
            background: 'transparent',
            fontSize: 15,
          }}
        />
      </div>

      {/* 右侧：用户区域 */}
      <Space size="middle">
        {isAuthenticated && user ? (
          /* 已登录 - 用户头像 + 下拉菜单 */
          <Dropdown
            menu={{
              items: userMenuItems,
              onClick: handleUserMenuClick,
            }}
            placement="bottomRight"
            trigger={['click']}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar
                size="small"
                icon={<UserOutlined />}
                src={user.avatar}
                style={{ backgroundColor: '#FF6B6B' }}
              />
              <Text style={{ color: '#333' }}>{user.username}</Text>
            </Space>
          </Dropdown>
        ) : (
          /* 未登录 - 登录/注册按钮 */
          <>
            <Button
              type="text"
              icon={<LoginOutlined />}
              onClick={() => navigate('/login')}
            >
              登录
            </Button>
            <Button
              type="primary"
              onClick={() => navigate('/register')}
              style={{
                background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
                border: 'none',
                borderRadius: 6,
              }}
            >
              注册
            </Button>
          </>
        )}
      </Space>
    </Header>
  );
};

export default AppHeader;
