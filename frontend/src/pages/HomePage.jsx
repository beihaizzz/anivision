import { Row, Col, Card, Button, Typography, Space } from 'antd';
import {
  ScanOutlined,
  ThunderboltOutlined,
  BulbOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

/**
 * AniVision 首页
 *
 * 展示系统介绍、核心功能和引导用户开始使用的 CTA 按钮
 */
const HomePage = () => {
  const navigate = useNavigate();

  // 核心功能卡片数据
  const features = [
    {
      icon: <ScanOutlined style={{ fontSize: 36, color: '#FF6B6B' }} />,
      title: '图像识别',
      description: '上传任意动漫角色图片，AI 自动识别角色身份和作品来源',
    },
    {
      icon: <ThunderboltOutlined style={{ fontSize: 36, color: '#4ECDC4' }} />,
      title: '毫秒响应',
      description: '优化的深度学习模型，快速返回 Top-5 匹配结果',
    },
    {
      icon: <BulbOutlined style={{ fontSize: 36, color: '#FFE66D' }} />,
      title: '智能匹配',
      description: '多维度特征提取，准确率业界领先的角色识别引擎',
    },
  ];

  return (
    <div className="home-page" style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* ========== Hero 区域 ========== */}
      <div
        style={{
          textAlign: 'center',
          padding: '80px 20px 60px',
          borderRadius: 16,
          background: 'linear-gradient(135deg, rgba(255,107,107,0.08), rgba(78,205,196,0.08))',
          marginBottom: 60,
        }}
      >
        <Title
          level={1}
          style={{
            fontSize: 48,
            fontWeight: 800,
            background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 24,
          }}
        >
          动漫角色图像识别
        </Title>

        <Paragraph
          style={{
            fontSize: 18,
            color: '#666',
            maxWidth: 600,
            margin: '0 auto 40px',
            lineHeight: 1.8,
          }}
        >
          基于深度学习的智能识别系统，上传任意动漫角色图片，
          AI 即刻告诉你角色身份、作品来源与置信度分析。
        </Paragraph>

        <Space size="middle">
          <Button
            type="primary"
            size="large"
            icon={<ArrowRightOutlined />}
            onClick={() => navigate('/recognize')}
            style={{
              height: 48,
              paddingInline: 36,
              fontSize: 16,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
              border: 'none',
            }}
          >
            开始识别
          </Button>
          <Button
            size="large"
            onClick={() => navigate('/login')}
            style={{
              height: 48,
              paddingInline: 28,
              fontSize: 16,
              borderRadius: 8,
            }}
          >
            了解更多
          </Button>
        </Space>
      </div>

      {/* ========== 功能介绍卡片 ========== */}
      <Row gutter={[24, 24]} style={{ marginBottom: 60 }}>
        {features.map((feature, index) => (
          <Col xs={24} sm={8} key={index}>
            <Card
              hoverable
              style={{
                borderRadius: 12,
                textAlign: 'center',
                height: '100%',
                border: '1px solid #f0f0f0',
                transition: 'all 0.3s ease',
              }}
              bodyStyle={{ padding: '32px 24px' }}
            >
              <div style={{ marginBottom: 16 }}>{feature.icon}</div>
              <Title level={4} style={{ marginBottom: 12 }}>
                {feature.title}
              </Title>
              <Paragraph type="secondary" style={{ fontSize: 14 }}>
                {feature.description}
              </Paragraph>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default HomePage;
