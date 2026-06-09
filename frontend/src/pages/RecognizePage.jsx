import { useState } from 'react';
import {
  Card,
  Upload,
  Spin,
  Typography,
  message,
  Row,
  Col,
  Tag,
  Button,
  Space,
} from 'antd';
import {
  InboxOutlined,
  ScanOutlined,
  DeleteOutlined,
  PictureOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';
import * as recognitionApi from '../api/recognition';

const { Dragger } = Upload;
const { Title, Text, Paragraph } = Typography;

/**
 * AniVision 图像识别页面
 *
 * 功能：
 * - 拖拽/点击上传图片
 * - 状态管理：idle → uploading → processing → result
 * - 上传成功后显示处理动画
 * - 识别结果展示区域（Phase 2 将展示 Top-5 角色匹配结果）
 */
const RecognizePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  // 页面状态
  const [status, setStatus] = useState('idle'); // idle | uploading | processing | result
  const [uploadedFile, setUploadedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [recognitionResult, setRecognitionResult] = useState(null);

  /**
   * 处理图片上传
   * 支持拖拽或点击选择，限制图片格式和大小
   */
  const handleUpload = async (file) => {
    // 文件类型校验
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('请上传图片文件（JPG、PNG、WebP 等）');
      return Upload.LIST_IGNORE;
    }

    // 文件大小校验（最大 10MB）
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('图片大小不能超过 10MB');
      return Upload.LIST_IGNORE;
    }

    // 生成预览 URL
    const preview = URL.createObjectURL(file);
    setUploadedFile(file);
    setPreviewUrl(preview);
    setStatus('uploading');

    try {
      // 调用 API 上传图片
      const response = await recognitionApi.uploadImage(file);
      setStatus('processing');

      // 模拟处理中状态（Phase 2 替换为轮询任务状态）
      await new Promise((resolve) => setTimeout(resolve, 1500));

      setStatus('result');
      setRecognitionResult(response);
      message.success('识别完成！');
    } catch (error) {
      setStatus('idle');
      message.error('上传失败，请重试');
      console.error('Upload error:', error);
    }

    // 阻止默认上传行为
    return false;
  };

  /**
   * 重置页面状态，准备新识别
   */
  const handleReset = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setUploadedFile(null);
    setPreviewUrl(null);
    setRecognitionResult(null);
    setStatus('idle');
  };

  // 未登录提示
  if (!isAuthenticated) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 20px' }}>
        <Card style={{ maxWidth: 500, margin: '0 auto', borderRadius: 12 }}>
          <Title level={3}>请先登录</Title>
          <Paragraph type="secondary">
            登录后即可使用图像识别功能，上传动漫角色图片立即识别
          </Paragraph>
          <Space>
            <Button
              type="primary"
              onClick={() => navigate(`/login?redirect=/recognize`)}
              style={{
                borderRadius: 8,
                background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
                border: 'none',
              }}
            >
              去登录
            </Button>
            <Button onClick={() => navigate('/register')} style={{ borderRadius: 8 }}>
              注册账号
            </Button>
          </Space>
        </Card>
      </div>
    );
  }

  return (
    <div className="recognize-page" style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* 页面标题 */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title
          level={2}
          style={{
            background: 'linear-gradient(135deg, #FF6B6B, #4ECDC4)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          <ScanOutlined style={{ marginRight: 12 }} />
          图像识别
        </Title>
        <Text type="secondary">上传动漫角色图片，AI 即刻识别角色身份</Text>
      </div>

      <Row gutter={[24, 24]}>
        {/* 左侧：上传区域 + 预览 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <PictureOutlined />
                <span>图片上传</span>
              </Space>
            }
            style={{ borderRadius: 12, height: '100%' }}
            extra={
              status !== 'idle' && (
                <Button
                  type="text"
                  icon={<DeleteOutlined />}
                  onClick={handleReset}
                  danger
                >
                  重新上传
                </Button>
              )
            }
          >
            {/* 状态：空闲 - 显示上传拖拽区 */}
            {status === 'idle' && (
              <Dragger
                accept="image/*"
                beforeUpload={handleUpload}
                showUploadList={false}
                style={{ borderRadius: 12 }}
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ fontSize: 48, color: '#FF6B6B' }} />
                </p>
                <p className="ant-upload-text" style={{ fontSize: 16 }}>
                  点击或拖拽图片到此处上传
                </p>
                <p className="ant-upload-hint" style={{ fontSize: 13 }}>
                  支持 JPG、PNG、WebP 格式，单张最大 10MB
                </p>
              </Dragger>
            )}

            {/* 状态：上传中 - 显示预览 + 加载 */}
            {status === 'uploading' && (
              <div style={{ textAlign: 'center', padding: 40 }}>
                {previewUrl && (
                  <img
                    src={previewUrl}
                    alt="上传预览"
                    style={{
                      maxWidth: '100%',
                      maxHeight: 250,
                      borderRadius: 8,
                      marginBottom: 24,
                    }}
                  />
                )}
                <Spin tip="正在上传图片..." size="large">
                  <div style={{ height: 60 }} />
                </Spin>
              </div>
            )}

            {/* 状态：处理中 */}
            {status === 'processing' && (
              <div style={{ textAlign: 'center', padding: 40 }}>
                {previewUrl && (
                  <img
                    src={previewUrl}
                    alt="识别中"
                    style={{
                      maxWidth: '100%',
                      maxHeight: 250,
                      borderRadius: 8,
                      marginBottom: 24,
                    }}
                  />
                )}
                <Spin tip="AI 正在分析图片..." size="large">
                  <div style={{ height: 60 }} />
                </Spin>
              </div>
            )}

            {/* 状态：完成 - 显示识别图片 */}
            {status === 'result' && previewUrl && (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <img
                  src={previewUrl}
                  alt="识别结果图片"
                  style={{
                    maxWidth: '100%',
                    maxHeight: 300,
                    borderRadius: 8,
                  }}
                />
                <div style={{ marginTop: 16 }}>
                  <Tag color="success" style={{ fontSize: 14, padding: '4px 12px' }}>
                    识别完成
                  </Tag>
                </div>
              </div>
            )}
          </Card>
        </Col>

        {/* 右侧：识别结果 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <ScanOutlined />
                <span>识别结果</span>
              </Space>
            }
            style={{ borderRadius: 12, height: '100%' }}
          >
            {/* 尚未识别 - 提示信息 */}
            {status === 'idle' && (
              <div
                style={{
                  textAlign: 'center',
                  padding: 60,
                  color: '#bfbfbf',
                }}
              >
                <InboxOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <p style={{ fontSize: 15 }}>请在左侧上传图片开始识别</p>
              </div>
            )}

            {/* 正在处理 - 等待提示 */}
            {(status === 'uploading' || status === 'processing') && (
              <div
                style={{
                  textAlign: 'center',
                  padding: 60,
                }}
              >
                <Spin size="default" />
                <p style={{ marginTop: 16, color: '#999' }}>
                  {status === 'uploading' ? '正在上传...' : 'AI 处理中...'}
                </p>
              </div>
            )}

            {/* 识别完成 - 结果占位（Phase 2 将展示 Top-5 角色） */}
            {status === 'result' && (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Title level={4} style={{ color: '#52c41a' }}>
                  识别成功！
                </Title>
                <Paragraph type="secondary" style={{ marginTop: 12 }}>
                  Top-5 匹配结果将在 Phase 2 中展示
                </Paragraph>
                <div
                  style={{
                    marginTop: 24,
                    padding: 24,
                    background: '#fafafa',
                    borderRadius: 8,
                    border: '1px dashed #d9d9d9',
                  }}
                >
                  <Text type="secondary" style={{ fontSize: 13 }}>
                    识别结果详情将在后续版本中呈现，
                    <br />
                    包括角色名称、作品来源、置信度评分等信息。
                  </Text>
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RecognizePage;
