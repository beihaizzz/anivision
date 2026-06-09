# AniVision 开发计划

> **版本**: v1.0  
> **日期**: 2026-06-09  
> **前置文档**: [需求分析](requirements_analysis.md) · [技术选型](tech_selection.md) · [详细设计](detailed_design.md)  
> **定位**: 基于设计文档的阶段化开发路线图

---

## 目录

1. [开发总览](#1-开发总览)
2. [团队分工建议](#2-团队分工建议)
3. [阶段一：基础设施与核心骨架](#3-阶段一基础设施与核心骨架)
4. [阶段二：AI引擎开发](#4-阶段二ai引擎开发)
5. [阶段三：社交功能完善](#5-阶段三社交功能完善)
6. [阶段四：数据分析与可视化](#6-阶段四数据分析与可视化)
7. [阶段五：集成测试与优化](#7-阶段五集成测试与优化)
8. [阶段六：答辩准备](#8-阶段六答辩准备)
9. [风险与应对](#9-风险与应对)
10. [里程碑检查清单](#10-里程碑检查清单)

---

## 1. 开发总览

### 1.1 阶段划分

```
阶段一: 基础设施与核心骨架    ████████  (Day 1-5)
  ├── 项目初始化 + 开发环境
  ├── 数据库建表 + ORM模型
  ├── 后端认证模块 (注册/登录/JWT)
  ├── 前端项目骨架 + 路由 + 布局
  └── 前后端联调: 注册/登录

阶段二: AI引擎开发            ████████  (Day 3-9, 与阶段一后半重叠)
  ├── 数据集下载 + 清洗 + 标注
  ├── EfficientNet-B3 识别模型训练
  ├── DCGAN 数据增强训练
  ├── 模型推理API封装
  └── 前端识别页面对接

阶段三: 社交功能完善          ████████  (Day 6-11)
  ├── 动态CRUD + 信息流
  ├── 评论/回复系统
  ├── 点赞/关注系统
  ├── 角色与作品资源页
  └── 搜索功能

阶段四: 数据分析与可视化       ████████  (Day 10-14)
  ├── 行为日志中间件
  ├── 分析统计API
  ├── ECharts 仪表盘页面
  └── 推荐算法(协同过滤)

阶段五: 集成测试与优化         ████  (Day 14-16)
  ├── 端到端功能测试
  ├── 性能优化
  ├── Bug修复
  └── 部署演练

阶段六: 答辩准备              ████  (Day 16-18)
  ├── 演示数据填充
  ├── 演示视频录制
  ├── PPT制作
  └── 设计说明书定稿
```

### 1.2 关键路径

```
数据集准备 ──→ 模型训练 ──→ 识别API ──→ 前端识别页面 ──→ 社交发布 ──→ 行为分析
     (最长)      (GPU)      (依赖模型)    (依赖API)       (依赖识别)    (依赖数据)
```

**关键路径上的任务不能延迟，否则整体交付风险大。**

### 1.3 开发原则

| 原则 | 说明 |
|------|------|
| **P0优先** | 所有P0需求必须在阶段三前完成，P1在阶段四前完成，P2可裁剪 |
| **前后端分离并行** | 后端先定义API契约，前端用Mock数据先行开发，接口就绪后联调 |
| **模型先行** | 数据集准备和模型训练是最长路径，必须最早启动 |
| **可演示优先** | 每个阶段结束都要有可演示的成果，不堆砌到最后 |
| **最小可用(MVP)** | 先做核心链路(上传→识别→展示)，再扩展社交功能 |

---

## 2. 团队分工建议

### 2.1 角色分配（4人团队）

| 角色 | 主要职责 | 负责模块 |
|------|---------|---------|
| **成员A - AI/后端** | 数据集、模型训练、推理服务 | 任务一+二的AI部分 |
| **成员B - 后端开发** | FastAPI后端全部API | 认证、识别、社交、分析API |
| **成员C - 前端开发** | React SPA 全部页面 | 全部前端组件和页面 |
| **成员D - 全栈/分析** | 数据分析、推荐、部署、文档 | 任务四 + 辅助联调 + 设计说明书 |

> **注意**: 成员A的模型训练需要GPU资源（Colab免费即可），在模型训练期间可兼做数据集清洗脚本。

### 2.2 协作模式

```
成员A(AI)              成员B(后端)           成员C(前端)           成员D(分析)
   │                       │                      │                     │
   │  数据集准备            │  后端骨架             │  前端骨架            │  文档框架
   │  模型训练              │  认证API              │  登录/注册页         │  行为日志设计
   │  推理封装              │  识别API              │  识别页面            │  分析API
   │  模型调优              │  社交API              │  社交页面            │  仪表盘页面
   │  GAN增强               │  分析API              │  前后端联调          │  推荐算法
   │                       │  Bug修复              │  Bug修复            │  部署+文档
```

---

## 3. 阶段一：基础设施与核心骨架

> **目标**: 项目可运行，注册登录可走通，数据库结构就绪  
> **时长**: 4-5天  
> **交付物**: 可运行的空壳项目，认证流程完整

### 3.1 后端任务（成员B主导）

#### Day 1: 项目初始化

- [ ] **T1.1.1** 创建项目结构
  ```
  anivision/
  ├── backend/
  │   ├── app/
  │   │   ├── __init__.py
  │   │   ├── main.py              # FastAPI入口
  │   │   ├── config.py            # 配置管理
  │   │   ├── database.py          # 数据库连接
  │   │   ├── models/              # SQLAlchemy ORM模型
  │   │   │   ├── __init__.py
  │   │   │   ├── user.py
  │   │   │   ├── character.py
  │   │   │   ├── post.py
  │   │   │   └── ...
  │   │   ├── schemas/             # Pydantic请求/响应模型
  │   │   ├── routers/             # API路由
  │   │   │   ├── auth.py
  │   │   │   ├── recognition.py
  │   │   │   ├── posts.py
  │   │   │   ├── users.py
  │   │   │   ├── characters.py
  │   │   │   ├── search.py
  │   │   │   └── analytics.py
  │   │   ├── services/            # 业务逻辑层
  │   │   ├── middleware/           # CORS、JWT、日志
  │   │   └── utils/
  │   ├── alembic/                 # 数据库迁移
  │   ├── requirements.txt
  │   └── .env
  ├── frontend/
  │   ├── src/
  │   │   ├── api/                 # API封装
  │   │   ├── components/          # 通用组件
  │   │   ├── pages/               # 页面组件
  │   │   ├── store/               # Zustand状态管理
  │   │   ├── router/              # 路由配置
  │   │   └── App.jsx
  │   ├── package.json
  │   └── vite.config.js
  ├── ai_engine/
  │   ├── recognition/
  │   │   ├── model.py
  │   │   ├── predictor.py
  │   │   ├── preprocess.py
  │   │   └── train.py
  │   ├── gan/
  │   │   ├── dcgan.py
  │   │   ├── generator.py
  │   │   └── train.py
  │   ├── models/
  │   │   └── label_map.json
  │   └── scripts/
  ├── data/
  │   ├── datasets/
  │   ├── uploads/
  │   └── generated/
  └── docs/
  ```

- [ ] **T1.1.2** 配置开发环境
  - Python 虚拟环境 + requirements.txt (FastAPI, SQLAlchemy, Alembic, PyJWT, python-multipart, asyncpg, etc.)
  - PostgreSQL 数据库创建 + 连接配置
  - `.env` 配置模板 (数据库URL、密钥、上传路径等)
  - CORS配置（允许前端localhost:5173）

- [ ] **T1.1.3** FastAPI 应用骨架
  - `main.py`: 创建FastAPI实例，注册路由、中间件
  - 健康检查端点 `GET /api/health`
  - 全局异常处理器

#### Day 2: 数据库 + ORM模型

- [ ] **T1.2.1** 创建所有数据库表（按详细设计 §3.2）
  - `users` 表（含角色: user/admin）
  - `works` 表
  - `characters` 表（含别名 aliases JSONB）
  - `recognition_logs` 表
  - `posts` 表（含 tags JSONB）
  - `comments` 表（parent_id 自引用）
  - `likes` 表（联合唯一约束）
  - `follows` 表（联合唯一约束）
  - `behavior_logs` 表（JSONB context + 月分区）
  - `tags` 表

- [ ] **T1.2.2** SQLAlchemy ORM 模型
  - 每张表对应一个ORM类
  - 关系定义: User→Posts, Post→Comments, User→Follows, Character→Work, etc.
  - Alembic 初始迁移脚本

- [ ] **T1.2.3** Pydantic Schema 定义
  - Auth: RegisterRequest, LoginRequest, UserResponse, TokenResponse
  - Recognition: UploadResponse, RecognitionResult, HistoryResponse
  - Posts: PostCreate, PostResponse, PostListResponse, CommentCreate, CommentResponse
  - Users: UserProfileResponse
  - Characters: CharacterListResponse, CharacterDetailResponse
  - Analytics: OverviewResponse, TrendingResponse
  - 通用: PaginationParams, PaginatedResponse

#### Day 3-4: 认证模块

- [ ] **T1.3.1** 用户注册 `POST /api/auth/register`
  - 密码加密 (bcrypt)
  - 输入验证 (Pydantic: username 3-50字符, email格式, password ≥8字符含大小写+数字)
  - 唯一性校验 (username + email)
  - 返回 201 + UserResponse

- [ ] **T1.3.2** 用户登录 `POST /api/auth/login`
  - JWT token 生成 (access_token, expires_in: 86400)
  - 返回 TokenResponse + UserResponse

- [ ] **T1.3.3** JWT认证中间件
  - `GET /api/auth/me` 获取当前用户
  - `PUT /api/auth/me` 更新用户资料
  - `get_current_user` 依赖注入函数

- [ ] **T1.3.4** 频率限制 (SlowAPI)
  - 注册: 5次/分钟/IP
  - 登录: 10次/分钟/IP
  - 识别上传: 30次/分钟/user

#### Day 4-5: 文件上传 + 识别API骨架

- [ ] **T1.4.1** 文件上传基础设施
  - 上传目录结构: `data/uploads/YYYY/MM/<uuid>.<ext>`
  - 文件校验: 类型白名单(JPG/PNG/WebP)、大小限制(≤10MB)
  - 静态文件服务配置

- [ ] **T1.4.2** 识别API骨架（Mock模式）
  - `POST /api/recognition/upload`: 先返回Mock数据，等AI模型训练完成后替换
  - `GET /api/recognition/{id}`: 返回Mock识别记录
  - `GET /api/recognition/history`: 返回Mock历史列表

### 3.2 前端任务（成员C主导）

#### Day 1: 前端项目初始化

- [ ] **T1.5.1** React + Vite 项目搭建
  - `npm create vite@latest frontend -- --template react`
  - 安装依赖: antd, @ant-design/icons, zustand, axios, react-router-dom, echarts, echarts-for-react
  - 配置代理: vite.config.js 中 proxy `/api` → `http://localhost:8000`

- [ ] **T1.5.2** 项目结构搭建
  - 路由配置 (React Router v6)
  - 布局组件: AppLayout, AppHeader, AppFooter
  - API封装: axios实例 + 请求拦截器(JWT token注入) + 响应拦截器(401处理)

#### Day 2-3: 认证相关页面

- [ ] **T1.6.1** 登录/注册页面
  - LoginPage: Ant Design Form + 表单验证
  - RegisterPage: 多字段表单 + 密码强度提示
  - Auth状态管理 (Zustand useAuthStore + localStorage持久化)

- [ ] **T1.6.2** 用户菜单
  - 未登录: 显示登录/注册按钮
  - 已登录: 显示头像 + 下拉菜单(我的主页/识别历史/退出)

#### Day 4-5: 识别页面骨架

- [ ] **T1.7.1** 识别页面框架 (RecognizePage)
  - ImageUploader组件: 拖拽/点击上传区域
  - 上传状态: 上传中 → 推理中 → 结果展示
  - 结果展示区骨架 (先Mock数据)

- [ ] **T1.7.2** 首页框架 (HomePage)
  - AppLayout 布局
  - 首页占位 + 导航菜单

### 3.3 AI引擎任务（成员A主导）

#### Day 1-3: 数据集准备

- [ ] **T1.8.1** 数据集下载
  - `scripts/download_datasets.py`: 从Danbooru/iCartoonFace下载数据
  - 数据完整性校验
  - 目标: 至少20个角色，每个角色100+张图像

- [ ] **T1.8.2** 数据清洗
  - `scripts/clean_data.py`: 去重、低分辨率过滤(≥112×112)、破损检测、非动漫过滤
  - `scripts/map_labels.py`: 统一中/日/英标签格式，建立character→work映射

- [ ] **T1.8.3** 数据集划分
  - `scripts/split_dataset.py`: 7:2:1 分层随机划分
  - `scripts/generate_dataset_csv.py`: 生成dataset.csv索引

### 3.4 阶段一验证标准

| 验证项 | 通过标准 |
|--------|---------|
| 后端启动 | `uvicorn app.main:app` 正常启动，Swagger UI 可访问 |
| 数据库 | 所有表创建成功，Alembic迁移无报错 |
| 注册API | POST /api/auth/register 可创建用户 |
| 登录API | POST /api/auth/login 返回JWT token |
| 认证保护 | GET /api/auth/me 无token返回401，有token返回用户信息 |
| 前端启动 | `npm run dev` 正常启动，页面可访问 |
| 前端登录 | 登录/注册流程可完整走通 |
| 上传接口 | POST /api/recognition/upload 接受文件并保存（Mock返回）|

---

## 4. 阶段二：AI引擎开发

> **目标**: 识别模型训练完成，推理API可用，前端识别功能完整  
> **时长**: 5-7天（与阶段一后半重叠）  
> **交付物**: 上传图片→识别角色→展示Top-5结果

### 4.1 模型训练（成员A主导）

#### Day 3-5: EfficientNet-B3 基线模型

- [ ] **T2.1.1** 训练脚本编写
  - `ai_engine/recognition/train.py`: 完整训练流程
  - 数据增强: RandomHorizontalFlip, ColorJitter, RandomRotation(15°), RandomErasing
  - 冻结策略: 冻结 stem + blocks[0:5], 训练 blocks[5:] + head
  - 学习率: 1e-4 (head层), 1e-5 (fine-tune层)
  - 损失函数: CrossEntropyLoss + LabelSmoothing(0.1)
  - 优化器: AdamW + CosineAnnealingLR

- [ ] **T2.1.2** 模型训练（Colab GPU）
  - Epoch 1-10: 只训练分类头（冻结backbone）
  - Epoch 11-30: 解冻后几层，降低学习率微调
  - 训练目标: Top-1 ≥ 85%, Top-5 ≥ 95%

- [ ] **T2.1.3** 模型评估
  - 分类报告: Accuracy, Precision, Recall, F1 (per-class + macro)
  - 混淆矩阵可视化
  - 推理速度测试: 单张 < 3秒(GPU) / < 10秒(CPU)

#### Day 5-7: DCGAN 数据增强

- [ ] **T2.2.1** 条件DCGAN实现
  - `ai_engine/gan/dcgan.py`: cDCGANGenerator + cDCGANDiscriminator
  - 条件标签嵌入: nn.Embedding(n_classes, embed_dim)
  - 图像尺寸: 128×128 → 3通道

- [ ] **T2.2.2** GAN训练
  - 训练目标: 每个角色生成50张变体图像
  - 质量筛选: 人工抽查 + FID分数参考
  - 生成数据加入训练集，重新训练识别模型

- [ ] **T2.2.3** 对比评估
  - 基线模型（无GAN）vs 增强模型（有GAN）
  - 记录准确率提升数据（用于答辩演示）

### 4.2 推理服务（成员A + 成员B协作）

#### Day 7-8: 推理API

- [ ] **T2.3.1** 推理封装
  - `ai_engine/recognition/predictor.py`: RecognitionPredictor类
  - 单例模式，全局加载模型一次
  - `predict(image_path) → RecognitionResult`
  - 返回Top-5: [(character_id, character_name, confidence), ...]

- [ ] **T2.3.2** 模型加载器
  - 冷启动: FastAPI启动事件中加载模型到内存
  - 模型路径配置: `.env` 中 `MODEL_PATH`, `LABEL_MAP_PATH`
  - 异常处理: 模型文件缺失时优雅降级（返回503）

- [ ] **T2.3.3** 替换Mock识别API
  - `POST /api/recognition/upload`: 实际调用RecognitionPredictor
  - 推理结果写入recognition_logs表
  - 同步行处理（<3秒）或异步任务队列（>3秒时考虑）

### 4.3 前端识别功能（成员C）

#### Day 7-9: 识别功能完整闭环

- [ ] **T2.4.1** 识别页面完善
  - 图片上传: 拖拽/点击，格式校验(JPG/PNG/WebP)，大小限制(10MB)
  - 上传进度条
  - 推理中状态: Loading动画 + 提示文字
  - 结果展示: Top-5卡片，角色名+作品+置信度+角色图

- [ ] **T2.4.2** 识别结果页 (ResultPage)
  - 结果详情: 角色名、作品、置信度、角色简介
  - "发布到社区"按钮
  - "再识别"按钮
  - 相关动态推荐区域(可Mock)

- [ ] **T2.4.3** 识别历史
  - 用户识别历史列表页面
  - 缩略图 + 角色名 + 时间

### 4.4 阶段二验证标准

| 验证项 | 通过标准 |
|--------|---------|
| 数据集 | ≥20个角色，每角色≥100张图片，清洗后无破损/低质量 |
| 模型训练 | EfficientNet-B3 Top-1 ≥ 85%, Top-5 ≥ 95% |
| GAN增强 | 每角色50张生成图，肉眼可接受质量 |
| 增强对比 | 增强后模型准确率有可见提升（≥2%） |
| 推理API | POST /api/recognition/upload 返回真实识别结果，延迟 < 3秒 |
| 前端识别 | 上传图片→展示Top-5结果，完整闭环 |

---

## 5. 阶段三：社交功能完善

> **目标**: 社交平台核心功能完整可用  
> **时长**: 5-6天  
> **交付物**: 可浏览、发布、互动的社交平台

### 5.1 后端社交API（成员B主导）

#### Day 6-8: 动态/评论/点赞

- [ ] **T3.1.1** 动态CRUD
  - `GET /api/posts`: 分页 + 排序(latest/hot/trending) + 筛选(tag/char_id/work_id/feed)
  - `POST /api/posts`: 发布动态（含tags、image_urls、recognition_id）
  - `GET /api/posts/{id}`: 动态详情
  - `DELETE /api/posts/{id}`: 删除动态（仅本人或管理员）

- [ ] **T3.1.2** 评论系统
  - `GET /api/posts/{id}/comments`: 带嵌套回复的评论列表
  - `POST /api/posts/{id}/comments`: 发表评论（支持parent_id嵌套，最多2层）
  - `DELETE /api/comments/{id}`: 删除评论

- [ ] **T3.1.3** 点赞系统
  - `POST /api/posts/{id}/like`: 点赞（幂等）
  - `DELETE /api/posts/{id}/like`: 取消点赞
  - like_count 冗余字段更新

- [ ] **T3.1.4** 关注系统
  - `POST /api/users/{id}/follow`: 关注
  - `DELETE /api/users/{id}/follow`: 取消关注
  - follower_count/following_count 冗余字段更新

#### Day 8-9: 角色/作品/搜索

- [ ] **T3.2.1** 角色与作品资源
  - `GET /api/characters`: 角色列表（分页+筛选+搜索+排序）
  - `GET /api/characters/{id}`: 角色详情（含别名、描述、相关动态）
  - `GET /api/works`: 作品列表
  - `GET /api/works/{id}`: 作品详情（含下属角色列表）
  - 数据初始化: 从label_map.json 导入角色和作品到数据库

- [ ] **T3.2.2** 全局搜索
  - `GET /api/search`: 全局搜索（角色/作品/用户/动态）
  - pg_trgm GIN索引 + 模糊搜索
  - 搜索结果分Tab返回

- [ ] **T3.2.3** 用户资料
  - `GET /api/users/{id}`: 用户公开资料（含stats）
  - `GET /api/users/{id}/posts`: 用户发布的动态
  - 头像上传: `POST /api/auth/me/avatar`

### 5.2 前端社交页面（成员C主导）

#### Day 8-11: 社交功能页面

- [ ] **T3.3.1** 首页信息流 (HomePage)
  - FeedTabs: 最新/热门/关注
  - PostCard: 封面图 + 标题/内容 + 点赞数 + 评论数 + 时间
  - InfiniteScrollList: 无限滚动加载 + 骨架屏

- [ ] **T3.3.2** 动态详情页 (PostDetailPage)
  - 大图模式展示
  - 评论列表 + 嵌套回复展开
  - 评论输入框
  - 点赞按钮

- [ ] **T3.3.3** 发布动态
  - 从识别结果页一键发布
  - 独立的发布动态页面
  - 图片选择 + Tag输入 + 文字描述

- [ ] **T3.3.4** 个人主页 (ProfilePage)
  - 头像/用户名/简介/统计数据
  - 关注/取消关注按钮
  - Tab切换: 动态 | 识别记录 | 收藏

- [ ] **T3.3.5** 角色浏览页 (CharacterListPage + CharacterDetailPage)
  - 角色列表: 卡片布局 + 作品筛选
  - 角色详情: 简介 + 别名 + 相关动态

- [ ] **T3.3.6** 搜索页 (SearchPage)
  - 全局搜索框
  - 分Tab: 角色/作品/用户/动态

### 5.3 阶段三验证标准

| 验证项 | 通过标准 |
|--------|---------|
| 动态发布 | 可发布带图片和标签的动态，出现在信息流 |
| 评论 | 可发表评论和2层嵌套回复 |
| 点赞 | 可点赞/取消点赞，计数正确 |
| 关注 | 可关注/取消关注，个人主页显示正确关注数 |
| 搜索 | 搜索角色名/作品名可返回结果 |
| 角色页 | 角色列表可按作品筛选，详情页展示相关信息 |
| 信息流 | 无限滚动加载，排序(latest/hot)切换正常 |

---

## 6. 阶段四：数据分析与可视化

> **目标**: 行为数据采集完整，分析仪表盘可视化  
> **时长**: 4-5天  
> **交付物**: 管理员仪表盘 + 推荐功能

### 6.1 行为日志中间件（成员B + 成员D协作）

#### Day 10-11: 行为数据采集

- [ ] **T4.1.1** 行为日志中间件
  - 自动记录: upload, recognize, like, comment, follow, browse, search, post
  - 记录上下文: 时间戳、设备类型、来源页面
  - 异步写入behavior_logs表（不阻塞请求）

- [ ] **T4.1.2** 数据匿名化处理
  - IP地址哈希存储
  - User-Agent只保留浏览器/操作系统大类

### 6.2 分析API（成员B + 成员D）

#### Day 11-12: 统计接口

- [ ] **T4.2.1** 仪表盘概览API
  - `GET /api/analytics/overview`: 总用户、总识别数、总动态数、DAU、平均置信度
  - 趋势数据: 30天用户增长、识别量变化

- [ ] **T4.2.2** 热门排行API
  - `GET /api/analytics/trending`: 按周/月/全部排行榜
  - 角色排行 + 作品排行

- [ ] **T4.2.3** 行为统计API
  - `GET /api/analytics/behaviors`: 行为类型分布、时间热力图、设备分布

### 6.3 推荐算法（成员D主导）

#### Day 12-13: 协同过滤推荐

- [ ] **T4.3.1** 基于协同过滤的内容推荐
  - 用户-角色交互矩阵
  - 使用scikit-learn的cosine_similarity计算用户相似度
  - 推荐逻辑: 相似用户喜欢的角色→推荐给当前用户

- [ ] **T4.3.2** 基于内容的推荐
  - 用户喜欢某作品→推荐同类型作品的其他角色
  - 热度排序: 新用户推荐热门角色

- [ ] **T4.3.3** 推荐API
  - `GET /api/posts?feed=recommended`: 个性化推荐信息流

### 6.4 仪表盘前端（成员C + 成员D）

#### Day 12-14: 仪表盘可视化

- [ ] **T4.4.1** 仪表盘页面 (DashboardPage)
  - OverviewCards: 总用户数、日活、识别次数、热门角色TOP10
  - TrendChart: 用户增长曲线 + 识别量变化曲线（ECharts）
  - TopCharactersChart: 热门角色TOP10柱状图
  - BehaviorHeatmap: 用户行为时间热力图
  - ActionPieChart: 行为类型占比饼图

- [ ] **T4.4.2** 时间筛选
  - 7天/30天/90天切换

### 6.5 阶段四验证标准

| 验证项 | 通过标准 |
|--------|---------|
| 行为日志 | 每次关键操作正确记录，可查询 |
| 概览数据 | 总用户、识别数、DAU等指标正确 |
| 趋势图表 | ECharts渲染正确，数据准确 |
| 热力图 | 时间×星期热力图可交互 |
| 推荐 | 新用户看到热门推荐，活跃用户看到个性化推荐 |

---

## 7. 阶段五：集成测试与优化

> **目标**: 全链路可走通，性能达标，无明显Bug  
> **时长**: 2-3天  
> **交付物**: 可完整演示的系统

### 7.1 集成测试

- [ ] **T5.1.1** 核心链路测试
  - 注册 → 登录 → 上传识别 → 查看结果 → 发布动态 → 点赞评论
  - 搜索角色 → 查看角色详情 → 关注用户 → 查看个人主页

- [ ] **T5.1.2** 边界条件测试
  - 未登录访问保护API → 401
  - 上传非图片文件 → 400
  - 重复点赞 → 409
  - 删除他人动态 → 403
  - 超长评论 → 422

- [ ] **T5.1.3** 性能测试
  - 识别API: P95 < 500ms (不含模型推理)
  - 信息流API: P95 < 200ms
  - 50并发用户: 无明显错误

### 7.2 性能优化

- [ ] **T5.2.1** 后端优化
  - 数据库查询优化: 添加必要索引（已在设计文档中定义）
  - N+1查询检查: 使用joinedload/selectinload
  - 图片压缩: 上传时生成缩略图

- [ ] **T5.2.2** 前端优化
  - 图片懒加载
  - 路由懒加载
  - 列表虚拟滚动（长列表）
  - 接口请求防抖/节流

### 7.3 Bug修复与细节优化

- [ ] **T5.3.1** UI细节
  - 空状态页面设计
  - Loading状态完善
  - 错误提示友好化
  - 响应式适配（至少PC端完整）

- [ ] **T5.3.2** 安全加固
  - XSS防护: 输入转义
  - CSRF防护: SameSite Cookie
  - 文件上传: 严格类型白名单
  - SQL注入: ORM参数化查询（已使用SQLAlchemy）

### 7.4 数据填充

- [ ] **T5.4.1** 演示数据准备
  - 创建10+测试用户
  - 测试用户互相关注
  - 每个用户3-5条动态
  - 多条评论和点赞
  - 30+次识别记录
  - 行为日志数据（至少7天）

---

## 8. 阶段六：答辩准备

> **目标**: 答辩PPT、演示视频、设计说明书完整  
> **时长**: 2-3天

### 8.1 PPT制作（成员D主导，全员协作）

- [ ] **T6.1.1** PPT结构
  1. 项目背景与需求分析 (2页)
  2. 系统架构设计 (2页)
  3. 技术选型说明 (1页)
  4. 数据采集与标注 (2页)
  5. GAN数据增强 (2页)
  6. 识别模型与效果 (3页) — **重点**
  7. 社交媒体平台功能 (3页)
  8. 用户行为分析 (2页)
  9. 创新点与难点 (1页)
  10. 总结与展望 (1页)

- [ ] **T6.1.2** 关键演示内容
  - 实时识别演示（重点！）
  - GAN生成效果对比
  - 社交互动流程
  - 数据分析仪表盘
  - 模型准确率对比图表

### 8.2 演示视频

- [ ] **T6.2.1** 录制5分钟演示视频
  - 配音或字幕解说
  - 完整演示核心功能流程
  - 包含AI识别实时演示

### 8.3 设计说明书

- [ ] **T6.3.1** 说明书定稿
  - 需求分析 → 已有文档
  - 技术选型 → 已有文档
  - 详细设计 → 已有文档
  - 实现说明 → 补充关键实现细节
  - 测试分析 → 补充测试报告
  - 创新点与总结 → 每人负责自己的模块

### 8.4 归档材料

- [ ] **T6.4.1** 按[归档要求](archive_notice.md)打包
  - 任务书（每人一份）
  - 说明书（每人一份）
  - 答辩PPT（一组一份）
  - 项目工程文件夹（一组一份）
  - 演示视频（一组一份）

---

## 9. 风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|---------|
| **模型准确率不达标** | 中 | 高 | ① 降低角色数量(20→10) ② 增加数据增强 ③ 切换ResNet50微调 |
| **GAN训练不稳定** | 中 | 中 | ① 使用WGAN-GP替代DCGAN ② 减少生成数量 ③ 仅作辅助演示 |
| **GPU训练时间不足** | 低 | 高 | ① 使用Colab Pro ② 减少训练epoch ③ 使用更小模型(EfficientNet-B0) |
| **前后端联调问题** | 中 | 中 | ① 提前定义API Schema ② 使用Mock数据先行开发 ③ 每日同步 |
| **PostgreSQL部署问题** | 低 | 低 | ① 开发环境用SQLite替代 ② Docker Compose统一部署 |
| **功能裁剪需求** | 低 | 中 | 优先裁剪P2功能: URL识别、批量识别、A/B测试、数据版本管理、热门榜单 |

---

## 10. 里程碑检查清单

| 里程碑 | 日期 | 检查标准 | 负责人 |
|--------|------|---------|--------|
| **M1: 项目骨架** | Day 5 | 后端启动+认证可走通+前端骨架 | 成员B/C |
| **M2: 识别闭环** | Day 9 | 上传图片→识别角色→展示结果 | 成员A/B/C |
| **M3: 社交闭环** | Day 13 | 发布动态→浏览信息流→评论互动 | 成员B/C |
| **M4: 分析完成** | Day 16 | 仪表盘数据正确+推荐可见 | 成员D |
| **M5: 系统可用** | Day 18 | 全功能可演示+Bug修复完毕 | 全员 |
| **M6: 答辩就绪** | Day 20 | PPT+视频+说明书+归档完成 | 全员 |

---

## 附录：P2功能裁剪清单

以下功能为P2优先级，在时间不足时可裁剪：

| 功能 | 模块 | 裁剪影响 |
|------|------|---------|
| 爬虫数据采集 | 任务一 | 使用公开数据集替代，无影响 |
| URL识别 | 任务三 | 仅支持文件上传，影响极小 |
| 批量识别 | 任务三 | 单张识别足够演示 |
| 分享卡片 | 任务三 | 不影响核心功能 |
| 热门榜单 | 任务三 | 首页时间排序替代 |
| 用户留存分析 | 任务四 | 核心指标已有，影响小 |
| 行为热力图 | 任务四 | 简化为柱状图即可 |
| A/B测试 | 任务四 | 演示不需要 |
| 模型版本管理 | 任务二 | 单模型版本足够 |
| 数据版本管理 | 任务一 | 单数据集版本足够 |