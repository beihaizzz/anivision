import { useEffect, useState } from 'react';
import { Card, Descriptions, Avatar, Spin, message, Typography } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import useAuthStore from '../store/useAuthStore';
import * as authApi from '../api/auth';

const { Title } = Typography;

/**
 * 个人主页
 *
 * 展示当前登录用户的信息：用户名、邮箱、角色、注册时间
 * Phase 1 基础实现，后续阶段扩展为完整个人主页
 */
const ProfilePage = () => {
  const { user } = useAuthStore();
  const [profile, setProfile] = useState(user);
  const [loading, setLoading] = useState(!user);

  useEffect(() => {
    if (!user) {
      // 如果 store 中没有用户信息，重新获取
      authApi
        .getCurrentUser()
        .then((data) => {
          setProfile(data);
        })
        .catch(() => {
          message.error('获取用户信息失败');
        })
        .finally(() => setLoading(false));
    }
  }, [user]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Title level={4}>无法加载用户信息</Title>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 600, margin: '40px auto' }}>
      <Card>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Avatar
            size={80}
            src={profile.avatar_url}
            icon={<UserOutlined />}
          />
          <Title level={3} style={{ marginTop: 12, marginBottom: 0 }}>
            {profile.username}
          </Title>
        </div>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="用户ID">{profile.id}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{profile.email}</Descriptions.Item>
          <Descriptions.Item label="角色">
            {profile.role === 'admin' ? '管理员' : '普通用户'}
          </Descriptions.Item>
          <Descriptions.Item label="简介">
            {profile.bio || '这个人很懒，什么都没写'}
          </Descriptions.Item>
          <Descriptions.Item label="注册时间">
            {profile.created_at
              ? new Date(profile.created_at).toLocaleString('zh-CN')
              : '—'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
};

export default ProfilePage;
