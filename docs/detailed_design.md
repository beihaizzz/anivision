# 动漫角色图像识别系统 — 详细系统设计

> **版本**: v1.0  
> **日期**: 2026-06-09  
> **前置文档**: [需求分析文档](requirements_analysis.md) · [技术选型方案](tech_selection.md)  
> **定位**: 详细系统设计（数据库、API、组件、模块内部设计）

---

## 目录

1. [设计概述与范围](#1-设计概述与范围)
2. [系统架构设计](#2-系统架构设计)
3. [数据库设计](#3-数据库设计)
4. [API接口设计](#4-api接口设计)
5. [前端设计](#5-前端设计)
6. [任务一：数据采集与标注](#6-任务一数据采集与标注)
7. [任务二：GAN增强与识别模型](#7-任务二gan增强与识别模型)
8. [任务三：社交媒体平台](#8-任务三社交媒体平台)
9. [任务四：用户行为分析](#9-任务四用户行为分析)
10. [关键流程时序图](#10-关键流程时序图)
11. [安全设计](#11-安全设计)
12. [错误处理策略](#12-错误处理策略)

---

## 1. 设计概述与范围

### 1.1 文档定位

本文档在[需求分析文档](requirements_analysis.md)和[技术选型方案](tech_selection.md)的基础上，对系统的**数据库结构**、**API接口**、**前端组件**、**AI模块内部设计**、**模块间交互**进行详细设计。

### 1.2 设计目标

| 维度 | 目标 |
|------|------|
| **可交付性** | 每个设计产出对应可编码的模块，组员可按文档直接开发 |
| **一致性** | 前后端接口、数据库Schema、AI模块输入输出均在本文件中明确定义 |
| **可测试性** | 每个模块定义清晰的输入/输出契约，便于独立测试 |
| **课程适配** | 复杂度匹配课程设计级别，不过度设计 |

### 1.3 与前置文档的关系

```
requirements_analysis.md          tech_selection.md
    (做什么)                          (用什么做)
         │                                  │
         └──────────┬───────────────────────┘
                    ▼
           detailed_design.md  ◄── 本文档
              (怎么做)
                    │
                    ▼
              编码实现 + 答辩PPT
```

---

## 2. 系统架构设计

### 2.1 分层架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         展示层 (Presentation Layer)                       │
│                                                                            │
│  ┌─────────────────────────────┐    ┌──────────────────────────────────┐  │
│  │     React 18 SPA (前端)       │    │   FastAPI Swagger UI (API文档)    │  │
│  │  Ant Design 5 + ECharts      │    │   开发/答辩时浏览器直接查看         │  │
│  │  Zustand 状态管理             │    │   http://localhost:8000/docs       │  │
│  │  React Router v6 路由         │    │                                    │  │
│  └───────────┬─────────────────┘    └──────────────────────────────────┘  │
│              │ REST API (JSON)                                             │
└──────────────┼───────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────────┐
│                         应用层 (Application Layer)                         │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                       FastAPI 应用服务器 (:8000)                       │ │
│  │                                                                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │ │
│  │  │ 认证模块   │ │ 识别模块   │ │ 社交模块   │ │ 用户模块   │ │ 分析模块    │  │ │
│  │  │ Auth     │ │Recog.    │ │ Social   │ │ User     │ │ Analytics  │  │ │
│  │  │ Module   │ │Module    │ │ Module   │ │ Module   │ │ Module     │  │ │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘  │ │
│  │       │            │            │            │             │          │ │
│  │  ┌────┴────────────┴────────────┴────────────┴─────────────┴──────┐  │ │
│  │  │                    中间件层 (Middleware)                         │  │ │
│  │  │  CORS中间件 | JWT认证中间件 | 请求日志 | 频率限制(SlowAPI)         │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────────┐
│                         业务逻辑层 (Service Layer)                          │
│                                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Auth     │ │Recog.    │ │ Post     │ │ Recom-   │ │ Analytics    │   │
│  │ Service  │ │Service   │ │ Service  │ │ mendation│ │ Service      │   │
│  │          │ │          │ │          │ │ Service  │ │              │   │
│  │ 注册/登录 │ │ 图像预处理 │ │ 动态CRUD  │ │ 协同过滤  │ │ 指标聚合      │   │
│  │ JWT签发  │ │ 模型推理  │ │ 评论管理  │ │ 内容推荐  │ │ 趋势计算      │   │
│  │ 密码加密  │ │ Top-K解析 │ │ 点赞逻辑  │ │ 热度排序  │ │ 报表生成      │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│       │            │            │            │             │             │
└───────┼────────────┼────────────┼────────────┼─────────────┼─────────────┘
        │            │            │            │             │
┌───────▼────────────▼────────────▼────────────▼─────────────▼─────────────┐
│                         数据访问层 (Data Access Layer)                      │
│                                                                            │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐  │
│  │  SQLAlchemy ORM       │  │  文件存储管理           │  │  AI模型管理       │  │
│  │  (asyncpg 异步驱动)    │  │  (本地文件系统)         │  │  (模型加载/缓存)   │  │
│  │                       │  │                       │  │                  │  │
│  │  User / Post /        │  │  uploads/             │  │  recognition/    │  │
│  │  Comment / Character  │  │    images/            │  │    efficientnet_ │  │
│  │  / BehaviorLog / etc  │  │    generated/         │  │    b3.pth        │  │
│  │                       │  │                       │  │  gan/            │  │
│  │                       │  │                       │  │    dcgan_g.pth   │  │
│  └──────────────────────┘  └──────────────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────────┐
│                         持久层 (Persistence Layer)                          │
│                                                                            │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐  │
│  │  PostgreSQL           │  │  文件存储 (本地)        │  │  Google Colab    │  │
│  │  (用户/内容/行为数据)   │  │  uploads/  uploaded/  │  │  (GPU训练环境)    │  │
│  │  :5432                │  │  models/  generated/  │  │  训练脚本同步     │  │
│  └──────────────────────┘  └──────────────────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 部署架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        开发/演示环境 (单机)                              │
│                                                                        │
│  ┌─────────────────────┐        ┌─────────────────────┐               │
│  │  React Dev Server    │        │  FastAPI Server      │               │
│  │  localhost:5173      │───────▶│  localhost:8000      │               │
│  │  (Vite HMR)          │  REST  │  (uvicorn --reload)  │               │
│  └─────────────────────┘        └──────────┬──────────┘               │
│                                            │                           │
│                       ┌────────────────────┼────────────────────┐      │
│                       │                    │                    │      │
│                 ┌─────▼─────┐      ┌──────▼──────┐      ┌─────▼─────┐│
│                 │ PostgreSQL │      │  文件存储     │      │ AI Engine ││
│                 │ :5432      │      │  ../data/    │      │ (同进程)   ││
│                 └────────────┘      └─────────────┘      └───────────┘│
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Google Colab (训练时使用)                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                       │  │
│  │  │ DCGAN训练Notebook │  │ EfficientNet     │                      │  │
│  │  │ → 产出dcgan_g.pth │  │ 训练Notebook      │                      │  │
│  │  └─────────────────┘  │ → 产出effnet.pth  │                      │  │
│  │                       └─────────────────┘                       │  │
│  │  数据源: Google Drive挂载 或 直接上传                              │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  注：模型训练在 Colab 完成，训练结果（.pth权重文件）下载到本地           │
│      ai_engine/models/ 目录，由 FastAPI 同进程加载推理。                │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.3 项目目录结构

```
E:\AniVision\
│
├── frontend/                          # React 18 前端项目
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── .env                           # VITE_API_BASE_URL=http://localhost:8000
│   └── src/
│       ├── main.jsx                   # React入口
│       ├── App.jsx                    # 根组件 + 路由配置
│       │
│       ├── api/                       # HTTP请求封装 (axios实例)
│       │   ├── client.js              #   基础配置 (baseURL, 拦截器, JWT注入)
│       │   ├── auth.js                #   登录/注册/获取当前用户
│       │   ├── recognition.js         #   上传图片/获取识别结果/历史
│       │   ├── posts.js               #   动态CRUD/信息流
│       │   ├── comments.js            #   评论列表/发表评论
│       │   ├── users.js               #   用户信息/用户动态
│       │   ├── characters.js          #   角色列表/角色详情
│       │   └── analytics.js           #   仪表盘数据 (管理员)
│       │
│       ├── store/                     # Zustand状态管理
│       │   ├── useAuthStore.js        #   用户认证状态
│       │   ├── usePostStore.js        #   动态列表/当前动态
│       │   └── useRecogStore.js       #   识别结果/识别历史
│       │
│       ├── router/                    # 路由配置
│       │   └── index.jsx              #   React Router v6 路由表
│       │
│       ├── hooks/                     # 自定义Hooks
│       │   ├── useAuth.js             #   认证相关逻辑
│       │   ├── useUpload.js           #   文件上传 + 拖拽
│       │   └── useInfiniteScroll.js   #   信息流无限滚动
│       │
│       ├── pages/                     # 页面级组件
│       │   ├── Home/                  #   首页（信息流）
│       │   ├── Recognize/             #   图像识别页
│       │   ├── Result/                #   识别结果页
│       │   ├── PostDetail/            #   动态详情页
│       │   ├── Profile/               #   个人主页
│       │   ├── Search/                #   搜索结果页
│       │   ├── Login/                 #   登录页
│       │   ├── Register/              #   注册页
│       │   ├── Dashboard/             #   数据分析仪表盘
│       │   └── Admin/                 #   管理后台
│       │
│       ├── components/                # 公共/业务组件
│       │   ├── layout/                #   布局组件
│       │   │   ├── AppHeader.jsx      #     顶部导航栏
│       │   │   ├── AppFooter.jsx      #     页脚
│       │   │   └── AppLayout.jsx      #     整体布局
│       │   ├── common/                #   通用组件
│       │   │   ├── Loading.jsx        #     加载状态
│       │   │   ├── ErrorBoundary.jsx  #     错误边界
│       │   │   ├── EmptyState.jsx     #     空状态引导
│       │   │   └── ProtectedRoute.jsx #     路由守卫（需登录）
│       │   ├── recognition/           #   识别相关组件
│       │   │   ├── ImageUploader.jsx  #     拖拽/点击上传
│       │   │   ├── ResultCard.jsx     #     识别结果卡片
│       │   │   └── HistoryList.jsx    #     识别历史列表
│       │   └── social/                #   社交相关组件
│       │       ├── PostCard.jsx       #     动态卡片
│       │       ├── PostForm.jsx       #     发布动态表单
│       │       ├── CommentList.jsx    #     评论列表
│       │       └── LikeButton.jsx     #     点赞按钮
│       │
│       └── styles/                    # 全局样式
│           └── global.css
│
├── backend/                           # FastAPI 后端项目
│   ├── requirements.txt               #   Python依赖
│   ├── alembic.ini                    #   Alembic配置
│   ├── alembic/                       #   Alembic迁移目录
│   │   ├── env.py
│   │   └── versions/                  #   迁移版本文件
│   └── app/
│       ├── main.py                    #   FastAPI应用入口 + CORS配置
│       ├── config.py                  #   配置管理 (Pydantic Settings)
│       │                                #   DB_URL / SECRET_KEY / UPLOAD_DIR
│       │
│       ├── api/                       #   路由层 (Router)
│       │   ├── __init__.py
│       │   ├── deps.py               #   依赖注入 (get_db, get_current_user)
│       │   ├── auth.py               #   /api/auth/*
│       │   ├── recognition.py        #   /api/recognition/*
│       │   ├── posts.py              #   /api/posts/*
│       │   ├── comments.py           #   /api/comments/*
│       │   ├── users.py              #   /api/users/*
│       │   ├── characters.py         #   /api/characters/*
│       │   └── analytics.py          #   /api/analytics/*
│       │
│       ├── models/                    #   SQLAlchemy ORM模型
│       │   ├── __init__.py
│       │   ├── user.py               #   User模型
│       │   ├── character.py          #   Character模型
│       │   ├── work.py               #   Work模型
│       │   ├── recognition.py        #   RecognitionLog模型
│       │   ├── post.py               #   Post模型
│       │   ├── comment.py            #   Comment模型
│       │   ├── like.py               #   Like模型
│       │   ├── follow.py             #   Follow模型
│       │   └── behavior.py           #   BehaviorLog模型
│       │
│       ├── schemas/                   #   Pydantic Schema (请求/响应)
│       │   ├── __init__.py
│       │   ├── auth.py               #   注册/登录/Token
│       │   ├── recognition.py        #   上传/识别结果
│       │   ├── post.py               #   动态/评论/点赞
│       │   ├── user.py               #   用户信息
│       │   ├── character.py          #   角色/作品
│       │   └── analytics.py          #   分析数据
│       │
│       ├── services/                  #   业务逻辑层
│       │   ├── __init__.py
│       │   ├── auth_service.py       #   注册/登录/JWT/密码加密
│       │   ├── recognition_service.py #  图像预处理→模型推理→结果解析
│       │   ├── post_service.py       #   动态CRUD/信息流排序
│       │   ├── comment_service.py    #   评论CRUD/嵌套查询
│       │   ├── recommendation_service.py # 协同过滤/内容推荐
│       │   └── analytics_service.py  #   指标聚合/趋势计算
│       │
│       ├── core/                      #   核心基础设施
│       │   ├── __init__.py
│       │   ├── database.py           #   SQLAlchemy引擎 + Session工厂
│       │   ├── security.py           #   JWT签发/验证, 密码hash
│       │   └── storage.py            #   文件上传/存储管理
│       │
│       └── middleware/                #   中间件
│           ├── __init__.py
│           ├── cors.py               #   CORS配置
│           └── logging.py            #   请求日志
│
├── ai_engine/                         # AI 引擎 (独立Python包)
│   ├── __init__.py
│   │
│   ├── recognition/                   # 角色识别
│   │   ├── __init__.py
│   │   ├── model.py                  #   EfficientNet模型定义
│   │   ├── predictor.py              #   模型加载 + 推理 + Top-K输出
│   │   └── preprocess.py             #   图像预处理 (resize/normalize)
│   │
│   ├── gan/                           # GAN生成
│   │   ├── __init__.py
│   │   ├── dcgan.py                  #   DCGAN生成器定义
│   │   └── generator.py              #   加载权重 + 生成图像
│   │
│   ├── training/                      # 训练脚本 (Colab上运行)
│   │   ├── train_efficientnet.ipynb  #   迁移学习训练
│   │   └── train_dcgan.ipynb          #   DCGAN训练
│   │
│   └── models/                        # 训练好的权重文件
│       ├── efficientnet_b3.pth
│       └── dcgan_generator.pth
│
├── data/                              # 数据目录
│   ├── datasets/                      #   公开数据集 (下载后存放)
│   │   ├── danbooru/                  #     Danbooru数据
│   │   └── iCartoonFace/              #     iCartoonFace数据
│   ├── uploads/                       #   用户上传的原始图像
│   ├── generated/                     #   GAN生成的图像
│   └── exports/                       #   数据导出 (CSV/JSON)
│
├── docs/                              # 项目文档
│   ├── requirements_analysis.md       #   需求分析
│   ├── tech_selection.md              #   技术选型
│   └── detailed_design.md             #   本文档
│
├── scripts/                           # 工具脚本
│   ├── init_db.py                     #   初始化数据库 + 种子数据
│   └── export_data.py                 #   数据导出工具
│
└── README.md                          # 项目说明
```

---

## 3. 数据库设计

### 3.1 ER 图

```
                    ┌──────────────────────┐
                    │        users          │
                    ├──────────────────────┤
                    │ PK  id         INT    │
                    │     username   VARCHAR│
                    │     email      VARCHAR│
                    │     password_hash VARCHAR│
                    │     avatar_url VARCHAR│
                    │     bio        TEXT   │
                    │     role       VARCHAR│──┐
                    │     created_at TIMESTAMP│ │
                    └──┬───────┬───────┬───┘ │
                       │       │       │     │ role ∈ ('user','creator','admin')
                       │       │       │     │
         ┌─────────────┘       │       └─────────────┐
         │ (关注)               │ (发布)               │ (识别)
         ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────────┐
│     follows       │  │    posts     │  │   recognition_logs    │
├──────────────────┤  ├──────────────┤  ├──────────────────────┤
│ PK id    INT     │  │ PK id  INT   │  │ PK id         INT    │
│ FK follower_id   │  │ FK user_id   │  │ FK user_id    INT    │─┐
│ FK followed_id   │  │     content  │  │     image_url VARCHAR │
│     created_at   │  │     tags     │  │     top_results JSONB │ │
└──────────────────┘  │     image_urls│  │ FK final_character_id │ │
         ┌─ ─ ─ ─ ─ ─ ┤       JSONB  │  │     confidence FLOAT  │ │
         │ (被关注者)   │ FK recog_id │  │     processing_time_ms│ │
         ▼             │     like_count│ │     created_at        │ │
      users            │     comment_  │  └──────────┬───────────┘ │
                       │       count   │             │              │
                       │     created_at│             │              │
                       └──┬────┬──────┘             │              │
                          │    │                    │              │
              ┌───────────┘    └──────────┐         │              │
              │ (评论)                    │ (点赞)   │              │
              ▼                          ▼         │              │
┌──────────────────┐          ┌──────────────┐     │              │
│    comments       │          │    likes      │     │              │
├──────────────────┤          ├──────────────┤     │              │
│ PK id    INT     │          │ PK id  INT   │     │              │
│ FK user_id       │          │ FK user_id   │     │              │
│ FK post_id       │          │ FK post_id   │     │              │
│ FK parent_id     │          │     created_at│     │              │
│     content TEXT │          └──────────────┘     │              │
│     created_at   │                               │              │
└──────────────────┘                               │              │
          parent_id → comments.id (自引用, 嵌套回复)  │              │
                                                   ▼              │
                                        ┌──────────────────┐      │
                                        │   characters      │◄─────┘
                                        ├──────────────────┤
                                        │ PK id    INT     │
                                        │     name  VARCHAR│
                                        │     name_jp VARCHAR│
                                        │     aliases JSONB │
                                        │ FK work_id  INT  │──┐
                                        │     description  │  │
                                        │     image_url    │  │
                                        │     created_at   │  │
                                        └──────────────────┘  │
                                                   ▲           │
                                                   │ (所属作品)  │
                                                   │           │
                                        ┌──────────┴───────┐  │
                                        │      works        │◄─┘
                                        ├──────────────────┤
                                        │ PK id    INT     │
                                        │     title VARCHAR│
                                        │     title_jp     │
                                        │     type  VARCHAR│
                                        │     description  │
                                        │     cover_url    │
                                        │     created_at   │
                                        └──────────────────┘

┌──────────────────────────┐
│     behavior_logs         │
├──────────────────────────┤
│ PK id          INT       │
│ FK user_id     INT       │──► users.id
│     action_type VARCHAR   │     枚举: upload/recognize/like/comment/
│     context      JSONB    │           follow/browse/search/post
│     ip_address   VARCHAR  │     context示例: {"character_id":5,
│     user_agent   VARCHAR  │                  "post_id":12,
│     created_at   TIMESTAMP│                  "duration_ms":3500}
└──────────────────────────┘
```

### 3.2 表结构详细定义

#### 3.2.1 users — 用户表

```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,              -- bcrypt($2b$...)
    avatar_url      VARCHAR(500),                       -- 头像图片路径
    bio             TEXT DEFAULT '',                     -- 个人简介
    role            VARCHAR(20)  NOT NULL DEFAULT 'user',-- user | creator | admin
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
```

| 字段 | 类型 | 说明 |
|------|------|------|
| username | VARCHAR(50) | 唯一用户名，用于展示和搜索 |
| email | VARCHAR(120) | 唯一邮箱，用于登录 |
| password_hash | VARCHAR(255) | bcrypt加密后的密码哈希 |
| avatar_url | VARCHAR(500) | 头像文件路径，可空 |
| bio | TEXT | 个人简介，最长500字 |
| role | VARCHAR(20) | 角色：user(普通用户)、creator(创作者)、admin(管理员) |
| is_active | BOOLEAN | 账号启用状态 |

---

#### 3.2.2 works — 作品表

```sql
CREATE TABLE works (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,              -- 作品中文名
    title_jp        VARCHAR(200),                       -- 日文原名
    type            VARCHAR(30)  NOT NULL DEFAULT 'anime', -- anime | manga | game | movie
    description     TEXT DEFAULT '',
    cover_url       VARCHAR(500),
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_works_title ON works(title);
CREATE INDEX idx_works_type ON works(type);
```

---

#### 3.2.3 characters — 角色信息表

```sql
CREATE TABLE characters (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,              -- 角色中文名
    name_jp         VARCHAR(200),                       -- 日文名/罗马音
    aliases         JSONB        DEFAULT '[]'::jsonb,   -- 别名列表 ["炭治郎","炭子"]
    work_id         INT          REFERENCES works(id) ON DELETE SET NULL,
    description     TEXT DEFAULT '',
    image_url       VARCHAR(500),                       -- 角色示例图片
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_characters_name ON characters(name);
CREATE INDEX idx_characters_work_id ON characters(work_id);
CREATE INDEX idx_characters_aliases ON characters USING GIN(aliases);
```

| 字段 | 类型 | 说明 |
|------|------|------|
| aliases | JSONB | 角色别名数组，如 `["炭治郎", "Tanjiro", "たんじろう"]` |
| work_id | FK→works.id | 所属作品，可空（未知作品时） |

---

#### 3.2.4 recognition_logs — 识别记录表

```sql
CREATE TABLE recognition_logs (
    id                  SERIAL PRIMARY KEY,
    user_id             INT          REFERENCES users(id) ON DELETE CASCADE,
    image_url           VARCHAR(500) NOT NULL,          -- 上传图片的存储路径
    top_results         JSONB        NOT NULL DEFAULT '[]'::jsonb,
    -- top_results结构:
    -- [{"rank":1, "character_id":5, "character_name":"灶门炭治郎",
    --   "work_title":"鬼灭之刃", "confidence":0.934},
    --  {"rank":2, ...}, ...]
    final_character_id  INT          REFERENCES characters(id) ON DELETE SET NULL,
    confidence          REAL,                            -- 最终确认置信度 (0.0~1.0)
    processing_time_ms  INT,                             -- 推理耗时 (ms)
    device_type         VARCHAR(20)  DEFAULT 'cpu',      -- cpu | gpu
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recog_user_id ON recognition_logs(user_id);
CREATE INDEX idx_recog_character_id ON recognition_logs(final_character_id);
CREATE INDEX idx_recog_created_at ON recognition_logs(created_at DESC);
```

| 字段 | 说明 |
|------|------|
| top_results | JSONB存储Top-K结果，避免多次JOIN，前端直接渲染 |
| final_character_id | 置信度最高的角色ID |
| confidence | 最高置信度分数 |
| processing_time_ms | 记录推理耗时，用于性能分析（任务4） |

---

#### 3.2.5 posts — 社区动态表

```sql
CREATE TABLE posts (
    id              SERIAL PRIMARY KEY,
    user_id         INT          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recognition_id  INT          REFERENCES recognition_logs(id) ON DELETE SET NULL,
    content         TEXT DEFAULT '',
    tags            JSONB        DEFAULT '[]'::jsonb,   -- ["鬼灭之刃","灶门炭治郎"]
    image_urls      JSONB        DEFAULT '[]'::jsonb,   -- 关联的图片列表
    like_count      INT          NOT NULL DEFAULT 0,     -- 冗余计数，避免COUNT查询
    comment_count   INT          NOT NULL DEFAULT 0,     -- 冗余计数
    is_pinned       BOOLEAN      NOT NULL DEFAULT FALSE, -- 置顶（管理用）
    is_hidden       BOOLEAN      NOT NULL DEFAULT FALSE, -- 隐藏（审核用）
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_recognition_id ON posts(recognition_id);
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);
```

| 字段 | 说明 |
|------|------|
| recognition_id | 可空；若发布自带识别结果则为对应的识别记录ID |
| like_count / comment_count | 冗余字段，触发式更新，避免频繁COUNT JOIN |
| is_hidden | 管理员可隐藏违规动态 |

---

#### 3.2.6 comments — 评论表

```sql
CREATE TABLE comments (
    id              SERIAL PRIMARY KEY,
    user_id         INT          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id         INT          NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    parent_id       INT          REFERENCES comments(id) ON DELETE CASCADE,
    content         TEXT         NOT NULL,
    is_hidden       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
```

| 字段 | 说明 |
|------|------|
| parent_id | 自引用外键：NULL=一级评论，非NULL=回复某条评论（最多2层嵌套） |
| is_hidden | 管理员可隐藏违规评论 |

---

#### 3.2.7 likes — 点赞表

```sql
CREATE TABLE likes (
    id              SERIAL PRIMARY KEY,
    user_id         INT          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id         INT          NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, post_id)                         -- 同一用户对同一动态只能点赞一次
);

CREATE INDEX idx_likes_post_id ON likes(post_id);
CREATE INDEX idx_likes_user_id ON likes(user_id);
```

---

#### 3.2.8 follows — 关注关系表

```sql
CREATE TABLE follows (
    id              SERIAL PRIMARY KEY,
    follower_id     INT          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    followed_id     INT          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE(follower_id, followed_id)                 -- 防止重复关注
);

CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_followed ON follows(followed_id);
```

---

#### 3.2.9 behavior_logs — 用户行为日志表

```sql
CREATE TABLE behavior_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INT          REFERENCES users(id) ON DELETE SET NULL, -- 未登录也可记录
    action_type     VARCHAR(30)  NOT NULL,             -- 行为类型枚举
    context         JSONB        DEFAULT '{}'::jsonb,  -- 行为上下文（灵活扩展）
    ip_address      VARCHAR(45),                       -- 支持IPv6
    user_agent      VARCHAR(500),                      -- 浏览器UA
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_behavior_user_id ON behavior_logs(user_id);
CREATE INDEX idx_behavior_action_type ON behavior_logs(action_type);
CREATE INDEX idx_behavior_created_at ON behavior_logs(created_at DESC);
-- 复合索引：按用户+时间查询行为序列
CREATE INDEX idx_behavior_user_time ON behavior_logs(user_id, created_at DESC);
```

| action_type 枚举值 | context 内容示例 |
|-------------------|-----------------|
| `upload` | `{"file_size": 245760, "format": "jpg"}` |
| `recognize` | `{"character_id": 5, "confidence": 0.934, "processing_ms": 1200}` |
| `like` | `{"post_id": 12, "post_author_id": 3}` |
| `comment` | `{"post_id": 12, "comment_id": 45}` |
| `follow` | `{"followed_id": 8}` |
| `browse` | `{"page": "home", "duration_ms": 3500}` |
| `search` | `{"query": "鬼灭", "type": "character", "results_count": 15}` |
| `post` | `{"post_id": 23, "has_image": true}` |

#### 数据增长管理策略

> behavior_logs 是写入最频繁的表（每次用户操作均记录），需预防数据膨胀。

| 策略 | 实现方式 | 触发条件 |
|------|---------|---------|
| **按月分区** | PostgreSQL 声明式分区 `PARTITION BY RANGE (created_at)` | 建表时即启用 |
| **定期归档** | Python 脚本将 >90 天的分区导出为 CSV 并 DROP | 每月定时执行 |
| **索引优化** | 仅对近 90 天分区创建索引 | 归档后自动释放 |

分区建表示例：
```sql
CREATE TABLE behavior_logs (
    id              SERIAL,
    user_id         INT REFERENCES users(id) ON DELETE SET NULL,
    action_type     VARCHAR(30) NOT NULL,
    context         JSONB DEFAULT '{}'::jsonb,
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(500),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 按月创建分区
CREATE TABLE behavior_logs_2026_06 PARTITION OF behavior_logs
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

---

### 3.3 关键索引策略

| 表 | 索引 | 用途 |
|----|------|------|
| users | email, username | 登录查找、搜索 |
| characters | name, work_id, aliases(GIN) | 角色搜索、按作品筛选、别名匹配 |
| posts | user_id, created_at DESC, tags(GIN) | 用户动态列表、信息流排序、按标签筛选 |
| comments | post_id, parent_id | 查询动态下的评论、嵌套回复 |
| likes | (user_id, post_id) UNIQUE | 去重+快速检查是否已点赞 |
| follows | (follower_id, followed_id) UNIQUE | 去重+快速查询关注关系 |
| recognition_logs | user_id, created_at DESC | 用户识别历史记录 |
| behavior_logs | user_id+created_at 复合索引 | 用户行为时间线查询 |
| 全局 | pg_trgm GIN 索引 | 模糊搜索加速（替代 LIKE %q%） |

---

## 4. API 接口设计

### 4.1 接口总览

> 基础URL: `http://localhost:8000/api`  
> 认证方式: `Authorization: Bearer <JWT>`  
> 自动文档: `http://localhost:8000/docs` (Swagger UI)

```
┌──────────────────────────────────────────────────────────────────────┐
│                            API 端点总览                               │
├────────────┬─────────────────────────────────────────────────────────┤
│ 认证 (Auth) │ POST /api/auth/register    注册                         │
│ (公开)      │ POST /api/auth/login        登录                         │
│ (需认证)     │ GET  /api/auth/me           获取当前用户信息              │
│            │ PUT  /api/auth/me           更新当前用户资料              │
├────────────┼─────────────────────────────────────────────────────────┤
│ 识别       │ POST /api/recognition/upload  上传图片→执行识别            │
│ (Recog.)   │ GET  /api/recognition/{id}    获取单条识别记录             │
│            │ GET  /api/recognition/history  查看个人识别历史             │
├────────────┼─────────────────────────────────────────────────────────┤
│ 社交       │ GET    /api/posts            获取信息流（分页+排序）        │
│ (Social)   │ POST   /api/posts            发布动态                      │
│            │ GET    /api/posts/{id}        获取动态详情                  │
│            │ DELETE /api/posts/{id}        删除自己的动态                │
│            │ GET    /api/posts/{id}/comments 获取动态评论列表            │
│            │ POST   /api/posts/{id}/comments 发表评论                   │
│            │ DELETE /api/comments/{id}     删除自己的评论                │
│            │ POST   /api/posts/{id}/like   点赞动态                      │
│            │ DELETE /api/posts/{id}/like   取消点赞                      │
├────────────┼─────────────────────────────────────────────────────────┤
│ 用户       │ GET  /api/users/{id}          获取用户公开信息              │
│ (User)     │ GET  /api/users/{id}/posts    获取用户发布的动态            │
│            │ POST /api/users/{id}/follow   关注用户                      │
│            │ DELETE /api/users/{id}/follow 取消关注                      │
├────────────┼─────────────────────────────────────────────────────────┤
│ 角色/作品   │ GET  /api/characters         角色列表（分页+筛选+搜索）     │
│ (Resource) │ GET  /api/characters/{id}     角色详情                      │
│            │ GET  /api/works              作品列表                       │
│            │ GET  /api/works/{id}          作品详情+下属角色列表           │
├────────────┼─────────────────────────────────────────────────────────┤
│ 搜索       │ GET  /api/search              全局搜索（角色/作品/用户/动态） │
├────────────┼─────────────────────────────────────────────────────────┤
│ 分析       │ GET  /api/analytics/overview  仪表盘概览（管理员）           │
│ (Analytics)│ GET  /api/analytics/trending  热门角色/作品排行              │
│            │ GET  /api/analytics/behaviors 用户行为统计（管理员）          │
└────────────┴─────────────────────────────────────────────────────────┘
```

### 4.2 认证模块详细设计

#### POST /api/auth/register — 用户注册

```
请求:
{
  "username": "xiaoming",
  "email": "xiaoming@example.com",
  "password": "SecurePass123!"
}

成功响应 (201):
{
  "id": 1,
  "username": "xiaoming",
  "email": "xiaoming@example.com",
  "role": "user",
  "created_at": "2026-06-09T10:30:00Z"
}

验证规则 (Pydantic):
- username: 3-50字符, 字母/数字/下划线
- email: 合法邮箱格式
- password: 最少8字符, 含大小写字母+数字

错误:
- 409: username或email已存在
- 422: 输入验证失败
```

#### POST /api/auth/login — 用户登录

```
请求:
{
  "username": "xiaoming",        // 或 email
  "password": "SecurePass123!"
}

成功响应 (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,           // 24小时
  "user": {
    "id": 1,
    "username": "xiaoming",
    "email": "xiaoming@example.com",
    "avatar_url": null,
    "role": "user"
  }
}

错误:
- 401: 用户名或密码错误
- 403: 账号已被禁用
```

#### GET /api/auth/me — 获取当前用户

```
Headers: Authorization: Bearer <token>

成功响应 (200):
{
  "id": 1,
  "username": "xiaoming",
  "email": "xiaoming@example.com",
  "avatar_url": "/uploads/avatars/1.jpg",
  "bio": "鬼灭之刃狂热粉",
  "role": "user",
  "created_at": "2026-06-09T10:30:00Z",
  "stats": {
    "post_count": 12,
    "follower_count": 45,
    "following_count": 30,
    "recognition_count": 89
  }
}
```

#### PUT /api/auth/me — 更新当前用户

```
Headers: Authorization: Bearer <token>

请求:
{
  "bio": "新简介文本",
  "avatar_url": "/uploads/avatars/1_new.jpg"
}

成功响应 (200): 返回更新后的用户对象
```

---

### 4.3 识别模块详细设计

#### POST /api/recognition/upload — 上传图像并识别

```
Headers: Authorization: Bearer <token>   (可选：未登录也能识别但不记录)
Content-Type: multipart/form-data

请求:
  file: <binary>           (必填, 支持 JPG/PNG/WebP, ≤10MB)

处理流程:
  1. 校验文件类型和大小
  2. 保存到 data/uploads/YYYY/MM/<uuid>.<ext>
  3. 调用 AI Engine 预处理 + 推理
  4. 解析 Top-5 结果
  5. 入库 recognition_logs
  6. 记录行为日志 (behavior_logs)

成功响应 (201):
{
  "id": 42,
  "image_url": "/uploads/2026/06/a1b2c3d4.jpg",
  "top_results": [
    {
      "rank": 1,
      "character_id": 5,
      "character_name": "灶门炭治郎",
      "character_name_jp": "Kamado Tanjirou",
      "work_title": "鬼灭之刃",
      "work_id": 1,
      "confidence": 0.934
    },
    {
      "rank": 2,
      "character_id": 12,
      "character_name": "我妻善逸",
      "character_name_jp": "Agatsuma Zenitsu",
      "work_title": "鬼灭之刃",
      "work_id": 1,
      "confidence": 0.034
    },
    // ... rank 3-5
  ],
  "processing_time_ms": 1234,
  "device_type": "cpu"
}

错误:
- 400: 文件类型不支持 / 文件过大
- 422: 未提供文件
- 500: 模型推理异常
```

#### GET /api/recognition/{id} — 获取识别记录

```
成功响应 (200):
{
  "id": 42,
  "image_url": "/uploads/2026/06/a1b2c3d4.jpg",
  "top_results": [ ... ],        // 同上传响应
  "processing_time_ms": 1234,
  "created_at": "2026-06-09T10:35:00Z"
}

错误:
- 404: 记录不存在
```

#### GET /api/recognition/history — 我的识别历史

```
Headers: Authorization: Bearer <token>

查询参数:
  page     int, 默认1
  size     int, 默认20, 最大50

成功响应 (200):
{
  "items": [ ... ],              // 识别记录列表
  "total": 89,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

---

### 4.4 社交模块详细设计

#### GET /api/posts — 获取信息流

```
查询参数:
  page     int,   默认1
  size     int,   默认20, 最大50
  sort     string, "latest"(默认) | "hot" | "trending"
  tag      string, 可选, 按标签筛选
  char_id  int,    可选, 按角色筛选
  work_id  int,    可选, 按作品筛选
  feed     string, 可选, "following" 关注用户动态

成功响应 (200):
{
  "items": [
    {
      "id": 10,
      "user": {
        "id": 1,
        "username": "xiaoming",
        "avatar_url": "/uploads/avatars/1.jpg"
      },
      "content": "终于找到这个角色了！",
      "tags": ["鬼灭之刃", "灶门炭治郎"],
      "image_urls": ["/uploads/2026/06/a1b2c3d4.jpg"],
      "recognition": {                          // 可空
        "character_id": 5,
        "character_name": "灶门炭治郎",
        "confidence": 0.934
      },
      "like_count": 15,
      "comment_count": 3,
      "is_liked": true,                         // 当前用户是否已点赞
      "created_at": "2026-06-09T10:40:00Z"
    },
    // ... 更多动态
  ],
  "total": 120,
  "page": 1,
  "size": 20,
  "pages": 6
}
```

#### POST /api/posts — 发布动态

```
Headers: Authorization: Bearer <token>

请求:
{
  "content": "今天又发现了一个冷门角色！",
  "tags": ["咒术回战", "狗卷棘"],
  "image_urls": ["/uploads/2026/06/uploaded_image.jpg"],
  "recognition_id": 42               // 可选，关联识别结果
}

成功响应 (201):
{
  "id": 11,
  "user": { ... },
  "content": "今天又发现了一个冷门角色！",
  "tags": ["咒术回战", "狗卷棘"],
  "image_urls": ["/uploads/2026/06/uploaded_image.jpg"],
  "recognition": { ... },
  "like_count": 0,
  "comment_count": 0,
  "created_at": "2026-06-09T10:45:00Z"
}
```

#### GET /api/posts/{id} — 获取动态详情

```
成功响应 (200):
{
  "id": 11,
  "user": { ... },
  "content": "...",
  "tags": [...],
  "image_urls": [...],
  "recognition": { ... },
  "like_count": 18,
  "comment_count": 5,
  "is_liked": false,
  "created_at": "2026-06-09T10:45:00Z"
}
```

#### DELETE /api/posts/{id} — 删除动态

```
Headers: Authorization: Bearer <token>
权限: 仅限发布者本人 或 管理员

成功响应 (204): No Content

错误:
- 403: 无权限
- 404: 动态不存在
```

#### GET /api/posts/{id}/comments — 获取评论

```
查询参数:
  page   int, 默认1
  size   int, 默认20

成功响应 (200):
{
  "items": [
    {
      "id": 30,
      "user": {
        "id": 2,
        "username": "artist_lan",
        "avatar_url": "/uploads/avatars/2.jpg"
      },
      "content": "这个角色我也很喜欢！",
      "parent_id": null,                       // null = 一级评论
      "replies": [                             // 嵌套回复（最多2层）
        {
          "id": 31,
          "user": { ... },
          "content": "对啊！超可爱的",
          "parent_id": 30,
          "created_at": "2026-06-09T11:00:00Z"
        }
      ],
      "created_at": "2026-06-09T10:50:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "size": 20
}
```

#### POST /api/posts/{id}/comments — 发表评论

```
Headers: Authorization: Bearer <token>

请求:
{
  "content": "画得真好！",
  "parent_id": null               // 可选，回复某条评论时指定其ID
}

验证规则:
- content: 1-500字符，不能为空
- parent_id: 若不为空，必须存在且属于同一post，且parent本身为一级评论（最多2层）

成功响应 (201):
{
  "id": 32,
  "user": { ... },
  "content": "画得真好！",
  "parent_id": null,
  "created_at": "2026-06-09T11:05:00Z"
}
```

#### DELETE /api/comments/{id} — 删除评论

```
Headers: Authorization: Bearer <token>
权限: 仅限评论者本人 或 管理员

成功响应 (204): No Content
注: 删除一级评论时，其下的回复也一并删除（CASCADE）
```

#### POST /api/posts/{id}/like — 点赞

```
Headers: Authorization: Bearer <token>

成功响应 (201):
{
  "post_id": 11,
  "like_count": 19,              // 更新后的点赞数
  "is_liked": true
}

错误:
- 409: 已经点赞过（幂等：返回当前状态也不错报）
```

#### DELETE /api/posts/{id}/like — 取消点赞

```
Headers: Authorization: Bearer <token>

成功响应 (200):
{
  "post_id": 11,
  "like_count": 18,
  "is_liked": false
}
```

---

### 4.5 用户模块详细设计

#### GET /api/users/{id} — 获取用户公开信息

```
成功响应 (200):
{
  "id": 1,
  "username": "xiaoming",
  "avatar_url": "/uploads/avatars/1.jpg",
  "bio": "鬼灭之刃狂热粉",
  "role": "user",
  "stats": {
    "post_count": 12,
    "follower_count": 45,
    "following_count": 30,
    "recognition_count": 89
  },
  "is_following": false,          // 当前用户是否关注了此用户
  "created_at": "2026-06-09T10:30:00Z"
}
```

#### GET /api/users/{id}/posts — 获取用户发布的动态

```
查询参数: page, size
成功响应: 同 GET /api/posts 的 items 格式
```

#### POST /api/users/{id}/follow — 关注

```
Headers: Authorization: Bearer <token>

成功响应 (201):
{
  "follower_id": 1,
  "followed_id": 2,
  "is_following": true
}

验证: 不可关注自己
```

#### DELETE /api/users/{id}/follow — 取消关注

```
Headers: Authorization: Bearer <token>
成功响应 (200): { "is_following": false }
```

---

### 4.6 资源模块详细设计

#### GET /api/characters — 角色列表

```
查询参数:
  page      int,    默认1
  size      int,    默认20
  work_id   int,    可选，按作品筛选
  search    string, 可选，按名称/别名模糊搜索
  sort      string,  "name"(默认) | "popular" — 按识别次数排序

成功响应 (200):
{
  "items": [
    {
      "id": 5,
      "name": "灶门炭治郎",
      "name_jp": "Kamado Tanjirou",
      "work": { "id": 1, "title": "鬼灭之刃" },
      "image_url": "/data/characters/tanjiro.jpg",
      "recognition_count": 234     // 被识别的总次数
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20
}
```

#### GET /api/characters/{id} — 角色详情

```
成功响应 (200):
{
  "id": 5,
  "name": "灶门炭治郎",
  "name_jp": "Kamado Tanjirou",
  "aliases": ["炭治郎", "Tanjiro", "炭子"],
  "work": { "id": 1, "title": "鬼灭之刃", "title_jp": "鬼滅の刃", "type": "anime" },
  "description": "鬼灭之刃主角，使用水之呼吸和火之神神乐...",
  "image_url": "/data/characters/tanjiro.jpg",
  "recognition_count": 234,
  "recent_posts": [ ... ]          // 最近5条包含该角色的动态
}
```

---

### 4.7 搜索模块详细设计

#### GET /api/search — 全局搜索

```
查询参数:
  q         string, 必填, 搜索关键词
  type      string, 可选, "character" | "work" | "user" | "post" (不填=全部)
  page      int,    默认1
  size      int,    默认20

成功响应 (200):
{
  "query": "鬼灭",
  "characters": {
    "items": [
      { "id": 5, "name": "灶门炭治郎", "work_title": "鬼灭之刃", "image_url": "..." }
    ],
    "total": 5
  },
  "works": {
    "items": [
      { "id": 1, "title": "鬼灭之刃", "type": "anime", "cover_url": "..." }
    ],
    "total": 1
  },
  "users": {
    "items": [ ... ],
    "total": 3
  },
  "posts": {
    "items": [ ... ],
    "total": 8
  }
}

搜索逻辑 (基于 pg_trgm 三元组索引):
- 前置条件: CREATE EXTENSION IF NOT EXISTS pg_trgm;
- characters: name % q (相似度) OR name_jp % q OR aliases @> to_jsonb(q)
- works: title % q OR title_jp % q
- users: username % q
- posts: content % q OR tags @> to_jsonb(q)
- 相似度阈值: set_limit(0.3) — 低于此值不返回
- 排序: ORDER BY similarity(name, q) DESC

索引:
- CREATE INDEX idx_characters_name_trgm ON characters USING GIN (name gin_trgm_ops);
- CREATE INDEX idx_works_title_trgm ON works USING GIN (title gin_trgm_ops);
- CREATE INDEX idx_users_username_trgm ON users USING GIN (username gin_trgm_ops);
- CREATE INDEX idx_posts_content_trgm ON posts USING GIN (content gin_trgm_ops);
```

---

### 4.8 分析模块详细设计

#### GET /api/analytics/overview — 仪表盘概览

```
Headers: Authorization: Bearer <token>
权限: admin 或 公开（公开版隐藏部分敏感指标）

成功响应 (200):
{
  "overview": {
    "total_users": 520,
    "total_recognitions": 3420,
    "total_posts": 1800,
    "total_characters": 85,
    "dau_today": 45,                  // 今日活跃用户
    "recognition_avg_confidence": 0.878,
    "recognition_avg_time_ms": 1350
  },
  "trends": {
    "user_growth": [
      {"date": "2026-06-01", "new_users": 12, "total": 470},
      {"date": "2026-06-02", "new_users": 8, "total": 478},
      // ... 最近30天
    ],
    "recognition_daily": [
      {"date": "2026-06-01", "count": 120},
      {"date": "2026-06-02", "count": 98},
      // ...
    ]
  },
  "top_characters": [
    {"rank": 1, "character_name": "灶门炭治郎", "work_title": "鬼灭之刃", "count": 234},
    {"rank": 2, "character_name": "五条悟", "work_title": "咒术回战", "count": 198},
    // ... TOP 10
  ],
  "top_works": [
    {"rank": 1, "title": "鬼灭之刃", "count": 450},
    // ... TOP 5
  ]
}
```

#### GET /api/analytics/trending — 热门排行

```
查询参数:
  period   string,  "week"(默认) | "month" | "all"
  type     string,  "character"(默认) | "work"

成功响应 (200):
{
  "period": "week",
  "items": [
    {"rank": 1, "name": "...", "count": 55, "trend": "up"},    // trend: up/down/stable
    // ...
  ]
}
```

#### GET /api/analytics/behaviors — 用户行为统计

```
Headers: Authorization: Bearer <token>
权限: admin

查询参数:
  period    string,  "7d"(默认) | "30d" | "90d"

成功响应 (200):
{
  "action_breakdown": {
    "upload": 1500,
    "recognize": 3420,
    "like": 5600,
    "comment": 2100,
    "follow": 800,
    "browse": 12000,
    "search": 950,
    "post": 1800
  },
  "hourly_heatmap": [
    {"hour": 0, "mon": 10, "tue": 8, ...},   // 星期×小时行为量热力图数据
    // ...
  ],
  "device_breakdown": {
    "desktop": 0.65,
    "mobile": 0.30,
    "tablet": 0.05
  }
}
```

---

## 5. 前端设计

### 5.1 路由设计

```javascript
// src/router/index.jsx

const routes = [
  // 公共页面
  { path: '/',              element: <HomePage /> },           // 首页信息流
  { path: '/recognize',     element: <RecognizePage /> },      // 图像识别
  { path: '/result/:id',    element: <ResultPage /> },         // 识别结果
  { path: '/search',        element: <SearchPage /> },         // 搜索
  { path: '/characters',    element: <CharacterListPage /> },  // 角色浏览
  { path: '/characters/:id',element: <CharacterDetailPage /> },// 角色详情
  { path: '/works',         element: <WorkListPage /> },       // 作品列表
  { path: '/works/:id',     element: <WorkDetailPage /> },     // 作品详情
  { path: '/posts/:id',     element: <PostDetailPage /> },     // 动态详情

  // 用户相关（需登录）
  { path: '/login',         element: <LoginPage /> },          // 登录
  { path: '/register',      element: <RegisterPage /> },       // 注册
  { path: '/profile/:id',   element: <ProfilePage />,          // 他人主页
    auth: false },
  { path: '/me',            element: <ProtectedRoute><ProfilePage /></ProtectedRoute> },
                                                                 // 我的主页（需登录）

  // 仪表盘（管理员/公开版）
  { path: '/dashboard',     element: <DashboardPage /> },       // 数据分析仪表盘

  // 404
  { path: '*',              element: <NotFoundPage /> },
];
```

### 5.2 组件树

```
<App>
  <AppLayout>
    <AppHeader>                          // 顶部导航栏，始终显示
      ├── <Logo />
      ├── <NavMenu />                    //   首页 | 识别 | 角色 | 仪表盘
      ├── <SearchBar />                  //   全局搜索框
      └── <UserMenu />                   //   登录/头像下拉菜单
          ├── (未登录) <LoginButton /> <RegisterButton />
          └── (已登录) <Avatar /> <Dropdown>
                          ├── 我的主页
                          ├── 识别历史
                          └── 退出登录
    </AppHeader>

    <main>                               // 内容区，由路由决定
      <Routes>
        {/* 首页 */}
        <Route path="/" element={
          <HomePage>
            <FeedTabs />                 //   最新 | 热门 | 关注
            <InfiniteScrollList>         //   PostCard × N (无限滚动)
              <PostCard />
            </InfiniteScrollList>
          </HomePage>
        } />

        {/* 图像识别 */}
        <Route path="/recognize" element={
          <RecognizePage>
            <ImageUploader />            //   拖拽/点击上传区域
            <UploadHistory />            //   最近的识别历史
          </RecognizePage>
        } />

        {/* 识别结果 */}
        <Route path="/result/:id" element={
          <ResultPage>
            <ResultCard />               //   识别结果 (角色名/置信度/出处)
            <CharacterBrief />           //   角色简介
            <PostForm />                 //   一键发布动态
            <RelatedPosts />             //   相关动态推荐
          </ResultPage>
        } />

        {/* 动态详情 */}
        <Route path="/posts/:id" element={
          <PostDetailPage>
            <PostCard detail />          //   动态详情（大图模式）
            <CommentList>
              <CommentItem />            //   评论 + 嵌套回复
            </CommentList>
            <CommentInput />             //   发表评论
          </PostDetailPage>
        } />

        {/* 个人主页 */}
        <Route path="/profile/:id" element={
          <ProfilePage>
            <ProfileHeader />            //   头像/用户名/简介/关注数
            <ProfileTabs />              //   动态 | 识别记录 | 收藏
            <PostList />                 //   用户的动态列表
          </ProfilePage>
        } />

        {/* 搜索页 */}
        <Route path="/search" element={
          <SearchPage>
            <SearchResults />            //   分Tab展示结果
          </SearchPage>
        } />

        {/* 仪表盘 */}
        <Route path="/dashboard" element={
          <DashboardPage>
            <OverviewCards />            //   总用户/总识别/DAU/平均准确率
            <TrendChart />               //   用户增长 + 识别量趋势 (ECharts)
            <TopCharactersChart />       //   热门角色TOP10 (柱状图)
            <BehaviorHeatmap />          //   用户行为热力图 (ECharts)
            <ActionPieChart />           //   行为类型占比 (饼图)
          </DashboardPage>
        } />
      </Routes>
    </main>

    <AppFooter />
  </AppLayout>
</App>
```

### 5.3 状态管理 (Zustand Store)

#### useAuthStore — 认证状态

```javascript
// src/store/useAuthStore.js

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set, get) => ({
      // 状态
      user: null,                    // 当前用户对象 | null
      token: null,                   // JWT access_token
      isAuthenticated: false,
      isLoading: true,               // 初始化时检查token有效性

      // 动作
      login: async (credentials) => {
        const res = await authApi.login(credentials);
        set({ user: res.user, token: res.access_token, isAuthenticated: true });
      },

      register: async (data) => {
        const res = await authApi.register(data);
        // 注册成功不自动登录，跳转登录页
        return res;
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false });
      },

      fetchMe: async () => {
        try {
          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ user: null, token: null, isAuthenticated: false, isLoading: false });
        }
      },

      updateProfile: async (data) => {
        const user = await authApi.updateProfile(data);
        set({ user });
      },
    }),
    { name: 'auth-storage' }        // localStorage持久化
  )
);
```

#### useRecogStore — 识别状态

```javascript
// src/store/useRecogStore.js

const useRecogStore = create((set, get) => ({
  // 状态
  currentResult: null,             // 当前识别结果
  history: [],                     // 最近的识别历史（内存缓存）
  isUploading: false,              // 上传中
  isProcessing: false,             // 推理中

  // 动作
  uploadAndRecognize: async (file) => {
    set({ isUploading: true, isProcessing: true });
    try {
      const result = await recognitionApi.upload(file);
      set(state => ({
        currentResult: result,
        history: [result, ...state.history].slice(0, 20),
        isUploading: false,
        isProcessing: false,
      }));
      return result;
    } catch (err) {
      set({ isUploading: false, isProcessing: false });
      throw err;
    }
  },

  fetchHistory: async (page = 1) => {
    const data = await recognitionApi.getHistory(page);
    set({ history: data.items });
  },

  clearCurrentResult: () => set({ currentResult: null }),
}));
```

#### usePostStore — 动态状态

```javascript
// src/store/usePostStore.js

const usePostStore = create((set, get) => ({
  // 状态
  posts: [],                       // 当前信息流
  currentPost: null,               // 动态详情
  comments: [],                    // 当前动态的评论
  pagination: { page: 1, total: 0, pages: 0 },
  isLoading: false,

  // 动作
  fetchFeed: async (params = {}) => {
    set({ isLoading: true });
    const data = await postApi.getFeed(params);
    set(state => ({
      posts: params.page > 1 ? [...state.posts, ...data.items] : data.items,
      pagination: { page: data.page, total: data.total, pages: data.pages },
      isLoading: false,
    }));
  },

  createPost: async (data) => {
    const post = await postApi.create(data);
    set(state => ({ posts: [post, ...state.posts] }));
    return post;
  },

  toggleLike: async (postId) => {
    const post = get().posts.find(p => p.id === postId);
    if (post.is_liked) {
      await postApi.unlike(postId);
    } else {
      await postApi.like(postId);
    }
    set(state => ({
      posts: state.posts.map(p =>
        p.id === postId
          ? { ...p, is_liked: !p.is_liked, like_count: p.like_count + (p.is_liked ? -1 : 1) }
          : p
      ),
    }));
  },

  fetchComments: async (postId, page = 1) => {
    const data = await commentApi.getByPost(postId, page);
    set({ comments: data.items });
  },
}));
```

### 5.4 页面设计要点

| 页面 | Ant Design组件 | 关键交互 |
|------|---------------|---------|
| HomePage | `Tabs` + `List` + `Skeleton` | 无限滚动加载 + 骨架屏 + 下拉刷新 |
| RecognizePage | `Upload.Dragger` + `Spin` + `Progress` | 拖拽上传 → 进度条 → 跳转结果页 |
| ResultPage | `Result` + `Descriptions` + `Tag` + `Button` | Top-5折叠展示 + 一键分享 + 发布动态 |
| PostDetailPage | `Card` + `Comment` + `Avatar` + `Input` | 嵌套评论展开 + 回复框 |
| ProfilePage | `Avatar` + `Tabs` + `Descriptions` + `List` | Tab切换 + 关注按钮 |
| SearchPage | `Input.Search` + `Tabs` | 实时搜索建议 + 分类结果 |
| DashboardPage | `Statistic` + `Card` + ECharts图表 | 图表hover/缩放 + 时间范围切换 |

---

## 6. 任务一：数据采集与标注

### 6.1 数据集方案

基于技术选型决定使用公开数据集，任务一聚焦于**数据获取、清洗、整理、标注格式统一**。

```
┌─────────────────────────────────────────────────────────────────┐
│                     数据准备流程                                   │
│                                                                   │
│  公开数据集源                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Danbooru    │  │ iCartoonFace  │  │ Anime2Sketch │            │
│  │  (角色头像)   │  │ (卡通人脸+框)  │  │ (风格配对)    │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                 │                     │
│         └─────────────────┼─────────────────┘                     │
│                           ▼                                       │
│                    ┌──────────────┐                                │
│                    │  数据下载     │  Python脚本下载/解压            │
│                    └──────┬───────┘                                │
│                           ▼                                       │
│                    ┌──────────────┐                                │
│                    │  数据清洗     │                                │
│                    │ · 去重        │  Pandas + OpenCV               │
│                    │ · 低分辨率过滤 │  (min 112×112)                │
│                    │ · 非动漫过滤   │  (简易分类器)                  │
│                    │ · 破损检测     │  (Pillow open验证)             │
│                    └──────┬───────┘                                │
│                           ▼                                       │
│                    ┌──────────────┐                                │
│                    │  标签映射     │  统一标签格式                   │
│                    │ · 中/日/英    │  建立character→work映射         │
│                    └──────┬───────┘                                │
│                           ▼                                       │
│                    ┌──────────────┐                                │
│                    │  数据集划分   │  scikit-learn                   │
│                    │  7 : 2 : 1   │  train_test_split              │
│                    │  训练 验证 测试 │  stratified by character      │
│                    └──────┬───────┘                                │
│                           ▼                                       │
│                    ┌──────────────┐                                │
│                    │  格式标准化   │                                │
│                    │ · 224×224 px │  Pillow + Albumentations        │
│                    │ · RGB 3通道  │                                │
│                    │ · JPG quality │                                │
│                    └──────┬───────┘                                │
│                           ▼                                       │
│                    ┌──────────────┐                                │
│                    │  数据清单     │                                │
│                    │  dataset.csv │  filename,label,work,split      │
│                    └──────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 数据目录结构

```
data/datasets/
├── raw/                                # 原始下载数据（只读保留）
│   ├── danbooru/                       #   原始Danbooru图像
│   ├── iCartoonFace/                   #   原始iCartoonFace
│   └── anime2sketch/                   #   原始Anime2Sketch
│
├── processed/                          # 清洗后数据
│   ├── images/                         #   统一命名的图像文件
│   │   ├── 001_tanjiro_kamado.jpg
│   │   ├── 002_tanjiro_kamado.jpg
│   │   └── ...
│   └── metadata.csv                    #   元数据表
│                                       #   filename | character_name |
│                                       #   character_jp | work_title |
│                                       #   source | width | height
│
├── splits/                             # 数据集划分
│   ├── train/
│   │   └── images/                     #   70% 训练集图像 (符号链接或复制)
│   ├── val/
│   │   └── images/                     #   20% 验证集图像
│   └── test/
│       └── images/                     #   10% 测试集图像
│
└── dataset.csv                         # 总索引文件
                                        # columns: image_path, character_id, work_id, split
```

### 6.3 标注数据格式

```json
{
  "version": "1.0",
  "total_images": 5200,
  "total_characters": 28,
  "total_works": 12,
  "annotations": [
    {
      "image_path": "train/images/001_tanjiro_kamado.jpg",
      "character": {
        "id": 5,
        "name": "灶门炭治郎",
        "name_jp": "Kamado Tanjirou",
        "aliases": ["炭治郎", "Tanjiro"]
      },
      "work": {
        "id": 1,
        "title": "鬼灭之刃",
        "title_jp": "鬼滅の刃"
      },
      "image_info": {
        "width": 224,
        "height": 224,
        "source": "danbooru"
      },
      "split": "train",
      "augmentation": null               // 原始数据；GAN增强后填 "dcgan_v1"
    }
  ]
}
```

### 6.4 核心脚本

| 脚本 | 功能 |
|------|------|
| `scripts/download_datasets.py` | 从公开源下载数据集（支持断点续传） |
| `scripts/clean_data.py` | 数据清洗：去重、过滤、破损检测 |
| `scripts/map_labels.py` | 标签映射：统一不同源的标签格式 |
| `scripts/split_dataset.py` | 分层划分训练/验证/测试集 |
| `scripts/generate_dataset_csv.py` | 生成dataset.csv索引文件 |
| `scripts/stats.py` | 数据集统计：图像数、角色分布、作品分布 |

---

## 7. 任务二：GAN增强与识别模型

### 7.1 模块架构

```
┌──────────────────────────────────────────────────────────────────┐
│                     AI Engine 模块架构                             │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    ai_engine/recognition/                      │ │
│  │                                                                │ │
│  │  predict(image_path: str) → RecognitionResult                  │ │
│  │                                                                │ │
│  │  ┌─────────────────┐   ┌──────────────────┐                   │ │
│  │  │ preprocess.py    │   │ predictor.py      │                   │ │
│  │  │                  │   │                  │                   │ │
│  │  │ Image.open()     │   │ load_model()     │                   │ │
│  │  │ resize 300×300   │─▶│ model.eval()     │                   │ │
│  │  │ ToTensor()       │   │ predict(tensor)  │                   │ │
│  │  │ normalize        │   │ → logits         │                   │ │
│  │  │  mean=[0.485,...]│   │ → softmax        │                   │ │
│  │  │  std=[0.229,...] │   │ → top_k(5)       │                   │ │
│  │  └─────────────────┘   └────────┬─────────┘                   │ │
│  │                                  │                              │ │
│  │                    ┌─────────────▼──────────┐                   │ │
│  │                    │ model.py               │                   │ │
│  │                    │ EfficientNet-B3         │                   │ │
│  │                    │   - backbone: 预训练    │                   │ │
│  │                    │   - classifier head:    │                   │ │
│  │                    │     Linear(1536→N)      │                   │ │
│  │                    │     N = 角色类别数       │                   │ │
│  │                    └────────────────────────┘                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    ai_engine/gan/                               │ │
│  │                                                                │ │
│  │  generate(character_id: int, count: int) → List[Image]          │ │
│  │                                                                │ │
│  │  ┌─────────────────┐   ┌──────────────────┐                   │ │
│  │  │ generator.py     │   │ dcgan.py          │                   │ │
│  │  │                  │   │                  │                   │ │
│  │  │ load_generator() │   │ cDCGANGenerator: │                   │ │
│  │  │ noise = randn()  │   │   ConvTranspose2d │                  │ │
│  │  │ embed class label│   │   × 5 layers     │                   │ │
│  │  │ fake = G(z, c)   │   │   128×128→3×128×128│                 │ │
│  │  └─────────────────┘   └──────────────────┘                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    ai_engine/models/                            │ │
│  │                                                                │ │
│  │  efficientnet_b3.pth          # 识别模型权重 (~48MB)            │ │
│  │  dcgan_generator.pth          # GAN生成器权重 (~50MB)           │ │
│  │  dcgan_discriminator.pth      # GAN判别器权重 (仅训练用)         │ │
│  │  label_map.json               # 标签ID→角色名映射                │ │
│  │  class_names.txt              # 类别名称列表                     │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 识别模型设计

#### 模型架构：EfficientNet-B3 + 迁移学习

```
输入: RGB图像 300×300×3 (EfficientNet-B3 标准尺寸)
      │
      ▼
┌────────────────────────────┐
│  EfficientNet-B3 Backbone   │  ← torchvision.models.efficientnet_b3(pretrained=True)
│  (冻结前几层，只训练后几层)    │     冻结策略: 冻结 stem + blocks[0:5], 训练 blocks[5:]+head
│  输出: 1536-dim feature      │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Dropout (p=0.3)            │  ← 防过拟合
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Linear(1536, N_classes)    │  ← 分类头 (N = 训练的角色类别数)
└────────────┬───────────────┘
             │
             ▼
         Softmax
             │
             ▼
  Top-K 结果 + 置信度分数
```

#### 核心代码接口

```python
# ai_engine/recognition/predictor.py

class RecognitionPredictor:
    """角色识别预测器 (单例模式，全局加载一次模型)"""

    def __init__(self, model_path: str, label_map_path: str):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model(model_path)
        self.label_map = self._load_label_map(label_map_path)
        self.transform = get_transform()      # EfficientNet标准预处理

    def predict(self, image_path: str, top_k: int = 5) -> dict:
        """
        对单张图像进行识别

        Args:
            image_path: 图像文件路径
            top_k: 返回Top-K结果

        Returns:
            {
                "predictions": [
                    {
                        "rank": 1,
                        "character_id": 5,
                        "character_name": "灶门炭治郎",
                        "name_jp": "Kamado Tanjirou",
                        "work_id": 1,
                        "work_title": "鬼灭之刃",
                        "confidence": 0.934
                    },
                    ...
                ],
                "inference_time_ms": 1234
            }
        """
        # 1. 预处理
        image = Image.open(image_path).convert('RGB')
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        # 2. 推理
        t_start = time.time()
        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=1)

        # 3. Top-K
        topk_probs, topk_indices = torch.topk(probs, top_k)
        inference_time = (time.time() - t_start) * 1000

        # 4. 构建结果
        predictions = []
        for rank, (prob, idx) in enumerate(zip(topk_probs[0], topk_indices[0]), 1):
            char_info = self.label_map[str(idx.item())]
            predictions.append({
                "rank": rank,
                "character_id": char_info["character_id"],
                "character_name": char_info["name"],
                "name_jp": char_info.get("name_jp", ""),
                "work_id": char_info["work_id"],
                "work_title": char_info.get("work_title", ""),
                "confidence": round(prob.item(), 4),
            })

        return {
            "predictions": predictions,
            "inference_time_ms": round(inference_time, 1),
        }

    def _load_model(self, model_path: str) -> nn.Module:
        model = models.efficientnet_b3(pretrained=False)
        # 替换分类头
        num_classes = len(self.label_map)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        return model
```

#### 训练配置

| 超参数 | 值 | 说明 |
|--------|-----|------|
| 优化器 | AdamW | weight_decay=1e-4 |
| 学习率 | 1e-4 (backbone), 1e-3 (head) | 分层学习率 |
| 学习率策略 | CosineAnnealingLR | T_max=epochs |
| Batch Size | 32 | Colab T4 16GB显存下可用 |
| Epochs | 30~50 | 早停 patience=10 |
| 损失函数 | CrossEntropyLoss | label_smoothing=0.1 |
| 输入尺寸 | 300×300 | EfficientNet-B3标准 |
| 数据增强 | Albumentations: RandomResizedCrop, HorizontalFlip, ColorJitter, RandomRotation(±15°) | 训练集增强 |
| 验证增强 | Resize(300,300)+CenterCrop(300,300) | 验证集不做随机增强 |

### 7.3 GAN数据增强设计

#### cDCGAN 条件生成器架构

```
噪声 z ∈ R^100 (标准正态分布)    角色标签 c (one-hot, N_classes维)
       │                                    │
       ▼                                    ▼
┌────────────────────┐          ┌────────────────────┐
│  Linear(100, 512*4*4)│          │  Embedding(N, 512)  │
│  → Reshape (512,4,4) │          │  → Reshape (512,4,4)│
└──────────┬───────────┘          └──────────┬───────────┘
           │                                  │
           └──────────┬─ concat (channel dim)─┘
                      ▼
           (1024, 4, 4)  ← 噪声+条件拼接
                      │
                      ▼
         ┌────────────────────────┐
         │  ConvTranspose2d(1024→512) │  kernel=4, stride=2, pad=1
         │  BatchNorm2d + ReLU        │  → (512, 8, 8)
         └────────────┬───────────────┘
                      ▼
         ┌────────────────────────┐
         │  ConvTranspose2d(512→256)  │  → (256, 16, 16)
         │  BatchNorm2d + ReLU        │
         └────────────┬───────────────┘
                      ▼
         ┌────────────────────────┐
         │  ConvTranspose2d(256→128)  │  → (128, 32, 32)
         │  BatchNorm2d + ReLU        │
         └────────────┬───────────────┘
                      ▼
         ┌────────────────────────┐
         │  ConvTranspose2d(128→64)   │  → (64, 64, 64)
         │  BatchNorm2d + ReLU        │
         └────────────┬───────────────┘
                      ▼
         ┌────────────────────────┐
         │  ConvTranspose2d(64→3)     │  → (3, 128, 128)
         │  Tanh                      │
         └────────────────────────────┘
                      │
                      ▼
              生成图像 128×128×3
```

#### 训练配置

| 超参数 | 值 |
|--------|-----|
| 输入维度 | 100 (噪声) + N_classes (条件嵌入) |
| 输出图像尺寸 | 128×128×3 |
| 优化器 | Adam (lr=0.0002, β1=0.5) |
| Batch Size | 64 |
| Epochs | 100~200 |
| 损失函数 | Binary Cross Entropy (标准GAN Loss) |
| 训练策略 | 每训练1次判别器，训练1次生成器 |

#### GAN 生成图像与训练集的关系

> **重要说明**：GAN 生成的 128×128 图像**不直接**用于识别模型训练（识别模型输入为 300×300）。GAN 增强数据的参与方式如下：

| 用途 | 说明 |
|------|------|
| **定性展示** | 在答辩中展示 GAN 生成效果，证明数据增强能力 |
| **定量评估** | 通过 FID/IS 指标评估生成质量，作为课程成果之一 |
| **辅助训练（可选）** | 将生成图像 resize 到 300×300 后混入训练集，与 Albumentations 增强效果对比 |

> 识别模型的**主要数据增强手段**为 Albumentations（RandomResizedCrop、HorizontalFlip、ColorJitter 等），GAN 增强作为**补充手段**，重点展示 GAN 在动漫图像生成领域的应用价值。

#### 核心代码接口

```python
# ai_engine/gan/generator.py

class GANGenerator:
    """cDCGAN条件生成器 (单例模式)"""

    def __init__(self, model_path: str, num_classes: int):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.num_classes = num_classes
        self.generator = self._load_generator(model_path)
        self.latent_dim = 100

    def generate(self, character_id: int, count: int = 1) -> List[Image.Image]:
        """
        根据角色标签条件生成动漫角色图像

        Args:
            character_id: 目标角色ID (用于条件约束)
            count: 生成数量

        Returns:
            List[PIL.Image]: 生成的图像列表 (128×128 RGB)
        """
        # 构造噪声和条件标签
        noise = torch.randn(count, self.latent_dim, 1, 1, device=self.device)
        labels = torch.full((count,), character_id, dtype=torch.long, device=self.device)

        with torch.no_grad():
            fake = self.generator(noise, labels)     # (count, 3, 128, 128)

        images = []
        for i in range(count):
            img_tensor = fake[i].cpu()
            img_tensor = (img_tensor + 1) / 2        # [-1,1] → [0,1]
            img = ToPILImage()(img_tensor)
            images.append(img)

        return images

    def _load_generator(self, model_path: str) -> nn.Module:
        generator = cDCGANGenerator(latent_dim=100, num_classes=self.num_classes)
        generator.load_state_dict(torch.load(model_path, map_location=self.device))
        generator.to(self.device)
        generator.eval()
        return generator
```

### 7.4 Colab 训练流程

```
┌──────────────────────────────────────────────────────────────┐
│                 Google Colab 训练流程                           │
│                                                                │
│  Step 1: 挂载 Google Drive 或上传数据集                         │
│  Step 2: !pip install torch torchvision albumentations         │
│  Step 3: 从 ai_engine/ 导入模型定义                             │
│  Step 4: 加载数据集 → DataLoader                                │
│  Step 5: 训练循环 + TensorBoard 记录                            │
│  Step 6: 保存模型权重 → 下载 .pth 文件                          │
│  Step 7: 将 .pth 放入 ai_engine/models/ 目录                    │
│                                                                │
│  Notebook 路径: ai_engine/training/train_efficientnet.ipynb     │
│                ai_engine/training/train_dcgan.ipynb             │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. 任务三：社交媒体平台

### 8.1 前端页面流

```
                    ┌────────────────┐
                    │   用户首次访问   │
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │  首页信息流      │
                    │  (公开浏览)     │
                    └───┬───┬───┬────┘
                        │   │   │
          ┌─────────────┘   │   └─────────────┐
          ▼                 ▼                 ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │  搜索角色     │  │  上传识别     │  │  登录/注册    │
  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                 │                 │
         ▼                 ▼                 │
  ┌──────────────┐  ┌──────────────┐         │
  │  角色/作品详情 │  │  识别结果页    │         │
  └──────┬───────┘  └──────┬───────┘         │
         │                 │                 │
         │        ┌────────▼────────┐        │
         │        │  发布动态 (可选)  │        │
         │        └────────┬────────┘        │
         │                 │                 │
         └─────────┬───────┘                 │
                   ▼                         │
           ┌──────────────┐                  │
           │  动态详情页    │◄─────────────────┘
           │  (评论/点赞)   │         (登录后可互动)
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │  用户个人主页   │
           └──────────────┘
```

### 8.2 后端服务交互

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI 请求处理流程                              │
│                                                                       │
│  HTTP Request                                                        │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────┐                                                     │
│  │  CORS 中间件  │  处理跨域 (开发环境 localhost:5173→localhost:8000)  │
│  └──────┬──────┘                                                     │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │  请求日志     │  记录: method, path, status_code, duration          │
│  └──────┬──────┘                                                     │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │ JWT 认证     │  白名单: /api/auth/login, /api/auth/register        │
│  │ (除公开接口)  │  其余接口需 Bearer Token                             │
│  └──────┬──────┘                                                     │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │ 频率限制     │  上传识别: 20次/分钟  (SlowAPI)                       │
│  │ (可选)       │  API通用: 100次/分钟                                 │
│  └──────┬──────┘                                                     │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │  路由分发     │  Router → Service → Repository(ORM) → Database      │
│  └──────┬──────┘                                                     │
│         ▼                                                            │
│  ┌─────────────┐                                                     │
│  │ Pydantic     │  响应序列化 + 自动Swagger文档生成                     │
│  │ 响应模型      │                                                     │
│  └─────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 关键业务规则

| 业务规则 | 说明 |
|----------|------|
| 动态发布 | 未登录可浏览，但发布/点赞/评论必须登录 |
| 评论嵌套 | 最多2层（一级评论 + 回复），防止无限嵌套 |
| 点赞幂等 | 重复点赞不报错，返回当前状态 |
| 标签规范 | 前端建议标签（基于角色/作品），也允许自定义 |
| 内容审核 | 敏感词过滤 (Python: `better_profanity` 或简单正则) |
| 图片限制 | 单张 ≤10MB, 格式 JPG/PNG/WebP, 动态最多9张图 |
| 删除权限 | 用户只能删自己的内容，管理员可删任意内容 |
| 计数更新 | like_count/comment_count 使用触发器或服务层原子更新 |

---

## 9. 任务四：用户行为分析

### 9.1 数据采集管道

```
┌─────────────────────────────────────────────────────────────────┐
│                      行为数据采集管道                              │
│                                                                   │
│  用户交互                                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │ 上传  │ │ 识别  │ │ 点赞  │ │ 评论  │ │ 浏览  │ │ 搜索  │         │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘         │
│     │        │        │        │        │        │               │
│     └────────┴────────┴────┬───┴────────┴────────┘               │
│                            ▼                                      │
│                   ┌─────────────────┐                              │
│                   │  FastAPI 中间件   │                             │
│                   │  或服务层埋点     │                              │
│                   │  (非阻塞写入)     │                              │
│                   └────────┬────────┘                              │
│                            ▼                                      │
│                   ┌─────────────────┐                              │
│                   │  behavior_logs   │  PostgreSQL                  │
│                   │  表 (JSONB context)│  异步批量写入               │
│                   └────────┬────────┘                              │
│                            │                                      │
│                            ▼ 定时/按需                             │
│                   ┌─────────────────┐                              │
│                   │  数据分析管道     │                             │
│                   │  Pandas + NumPy  │                              │
│                   │  + scikit-learn  │                              │
│                   └────────┬────────┘                              │
│                            │                                      │
│              ┌─────────────┼─────────────┐                        │
│              ▼             ▼             ▼                        │
│       ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│       │ 指标计算   │ │ 推荐更新   │ │ 报表生成   │                    │
│       │ (DAU/留存)│ │ (协同过滤) │ │ (JSON→前端)│                    │
│       └──────────┘ └──────────┘ └──────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 分析指标计算

```python
# backend/app/services/analytics_service.py

class AnalyticsService:
    """用户行为分析服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self) -> dict:
        """仪表盘概览"""
        return {
            "total_users": await self._count_users(),
            "total_recognitions": await self._count_recognitions(),
            "total_posts": await self._count_posts(),
            "dau_today": await self._calc_dau(),
            "recognition_avg_confidence": await self._avg_confidence(),
            "recognition_avg_time_ms": await self._avg_processing_time(),
        }

    async def get_user_growth(self, days: int = 30) -> list:
        """用户增长趋势 (SQL聚合)"""
        query = """
            SELECT DATE(created_at) as date,
                   COUNT(*) as new_users,
                   SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) as total
            FROM users
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        # 执行查询 → 返回 [{date, new_users, total}, ...]

    async def get_top_characters(self, limit: int = 10) -> list:
        """热门角色TOP N"""
        query = """
            SELECT c.id, c.name, w.title as work_title,
                   COUNT(rl.id) as recognition_count
            FROM characters c
            LEFT JOIN works w ON c.work_id = w.id
            LEFT JOIN recognition_logs rl ON rl.final_character_id = c.id
            GROUP BY c.id, c.name, w.title
            ORDER BY recognition_count DESC
            LIMIT :limit
        """

    async def get_action_breakdown(self, days: int = 7) -> dict:
        """行为类型分布"""
        query = """
            SELECT action_type, COUNT(*) as count
            FROM behavior_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY action_type
        """

    async def get_hourly_heatmap(self, days: int = 7) -> list:
        """按星期×小时的行为热力图数据"""
        query = """
            SELECT EXTRACT(DOW FROM created_at) as dow,
                   EXTRACT(HOUR FROM created_at) as hour,
                   COUNT(*) as count
            FROM behavior_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY dow, hour
            ORDER BY dow, hour
        """

    async def _calc_dau(self) -> int:
        query = """
            SELECT COUNT(DISTINCT user_id)
            FROM behavior_logs
            WHERE DATE(created_at) = CURRENT_DATE
        """
```

### 9.3 推荐系统设计

```
┌─────────────────────────────────────────────────────────────────┐
│                       推荐系统架构                                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    协同过滤推荐                                │ │
│  │                                                               │ │
│  │  输入: 用户-角色互动矩阵 (行: user_id, 列: character_id)        │ │
│  │       值 = 用户对该角色的互动次数 (识别+点赞+评论+浏览)           │ │
│  │                                                               │ │
│  │  算法: scikit-learn NearestNeighbors                         │ │
│  │         1. 构建稀疏矩阵 (csr_matrix)                           │ │
│  │         2. cosine相似度找Top-K近邻用户                         │ │
│  │         3. 汇总近邻用户喜欢的角色，过滤已互动，排序推荐           │ │
│  │                                                               │ │
│  │  更新频率: 每日定时 / 手动触发                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    内容推荐 (标签相似度)                        │ │
│  │                                                               │ │
│  │  输入: 用户最近互动的动态/角色 → 提取标签集合                    │ │
│  │  算法:                                                         │ │
│  │    1. 汇总用户兴趣标签 (TF-IDF加权)                             │ │
│  │    2. 计算动态/角色标签与用户兴趣向量余弦相似度                   │ │
│  │    3. 返回相似度Top-N                                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    热度排序 (信息流)                            │ │
│  │                                                               │ │
│  │  score = log(like_count + 1) × 2 + log(comment_count + 1)    │ │
│  │          - (now - created_at).hours / 24 × decay_factor      │ │
│  │                                                               │ │
│  │  decay_factor = 0.3  (每天衰减系数)                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 冷启动策略

| 场景 | 策略 | 说明 |
|------|------|------|
| **新用户**（无交互记录） | 热度排序 + 随机探索 | 默认展示热门角色/作品排行，混入少量随机推荐促进探索 |
| **新角色/新作品**（无交互数据） | 内容推荐兜底 | 基于标签相似度推荐，不依赖用户交互矩阵 |
| **协同过滤失效**（近邻不足） | 降级为内容推荐 | 当相似用户数 < 3 时，自动切换为基于内容的推荐 |

> 推荐优先级：协同过滤 > 内容推荐 > 热度排序。每层降级时自动 fallback。

#### 推荐服务代码接口

```python
# backend/app/services/recommendation_service.py

class RecommendationService:
    """推荐服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend_by_collaborative(
        self, user_id: int, n_recommendations: int = 10
    ) -> List[dict]:
        """
        协同过滤推荐

        1. 构建用户-角色交互矩阵
        2. 找Top-10相似用户
        3. 汇总推荐角色列表
        """
        # 查询用户交互数据
        # 构建稀疏矩阵
        # NearestNeighbors 找相似用户
        # 聚合推荐

    async def recommend_by_content(
        self, user_id: int, n_recommendations: int = 10
    ) -> List[dict]:
        """
        基于内容的推荐 (标签相似度)
        """
        # 获取用户最近交互的标签
        # 计算与候选内容的标签相似度
        # 返回Top-N

    async def get_trending_posts(
        self, page: int = 1, size: int = 20
    ) -> dict:
        """
        热度排序信息流
        使用 HackerNews 风格的衰减算法
        """
```

### 9.4 仪表盘前端图表配置

| 图表 | ECharts类型 | 数据源API | 说明 |
|------|-----------|-----------|------|
| 核心指标卡 | Ant Design `Statistic` | `/api/analytics/overview` | 总用户、DAU、总识别、平均准确率 |
| 用户增长曲线 | `line` | overview.trends.user_growth | 折线图，30天趋势 |
| 识别量趋势 | `line` | overview.trends.recognition_daily | 折线图，双Y轴可叠加 |
| 热门角色TOP10 | `bar` (横向) | overview.top_characters | 角色名+识别次数 |
| 行为类型占比 | `pie` | behaviors.action_breakdown | 饼图 |
| 行为热力图 | `heatmap` | behaviors.hourly_heatmap | 星期×小时热力图 |

---

## 10. 关键流程时序图

### 10.1 用户上传识别流程

```
  用户(浏览器)      React前端         FastAPI后端       AI Engine        PostgreSQL
      │                │                  │                │                │
      │  拖拽/选择图片   │                  │                │                │
      │───────────────▶│                  │                │                │
      │                │                  │                │                │
      │                │  前端预校验        │                │                │
      │                │  (类型/大小)       │                │                │
      │                │                  │                │                │
      │                │ POST /api/recog/ │                │                │
      │                │   upload (file)  │                │                │
      │                │─────────────────▶│                │                │
      │                │                  │                │                │
      │                │                  │  校验文件类型    │                │
      │                │                  │  保存到uploads/ │                │
      │                │                  │                │                │
      │                │                  │ predict(path)  │                │
      │                │                  │───────────────▶│                │
      │                │                  │                │                │
      │                │                  │                │  加载模型       │
      │                │                  │                │  预处理图像     │
      │                │                  │                │  模型推理       │
      │                │                  │                │  Top-K输出     │
      │                │                  │                │                │
      │                │                  │  {predictions} │                │
      │                │                  │◀───────────────│                │
      │                │                  │                │                │
      │                │                  │  INSERT recognition_logs        │
      │                │                  │──────────────────────────────▶  │
      │                │                  │                │                │
      │                │                  │  INSERT behavior_logs           │
      │                │                  │  (action_type='recognize')       │
      │                │                  │──────────────────────────────▶  │
      │                │                  │                │                │
      │                │  201 {id,       │                │                │
      │                │   top_results}  │                │                │
      │                │◀─────────────────│                │                │
      │                │                  │                │                │
      │                │  路由跳转         │                │                │
      │                │  /result/{id}   │                │                │
      │  展示识别结果    │                  │                │                │
      │◀───────────────│                  │                │                │
```

### 10.2 发布动态+互动流程

```
  用户A          前端           后端            PostgreSQL       用户B(关注者)
   │              │              │                │                 │
   │  发布动态      │              │                │                 │
   │─────────────▶│              │                │                 │
   │              │ POST /posts  │                │                 │
   │              │─────────────▶│                │                 │
   │              │              │  INSERT post   │                 │
   │              │              │───────────────▶│                 │
   │              │  201 post    │                │                 │
   │              │◀─────────────│                │                 │
   │              │              │                │                 │
   │              │              │                │                 │
   │              │              │                │   刷新首页时      │
   │              │              │                │◀────────────────│
   │              │              │  GET /posts    │                 │
   │              │              │◀───────────────│                 │
   │              │              │  返回(含新动态)  │                 │
   │              │              │───────────────▶│                 │
   │              │              │                │                 │
   │              │              │                │   点赞/评论新动态  │
   │              │              │                │◀────────────────│
   │              │              │  POST /like    │                 │
   │              │              │◀───────────────│                 │
   │              │              │  UPDATE post   │                 │
   │              │              │   like_count++ │                 │
   │              │              │───────────────▶│                 │
   │              │              │                │                 │
   │  收到点赞通知  │              │                │                 │
   │◀─────────────│◀─────────────│                │                 │
```

### 10.3 GAN增强 + 模型重训练流程

```
  系统管理员      Colab Notebook      本地文件系统      AI Engine
      │                │                  │                │
      │  启动训练       │                  │                │
      │───────────────▶│                  │                │
      │                │                  │                │
      │                │  加载训练数据      │                │
      │                │  (从 data/datasets│                │
      │                │   /splits/train)  │                │
      │                │                  │                │
      │                │  GAN训练循环      │                │
      │                │  for epoch in    │                │
      │                │   range(200):    │                │
      │                │     train D      │                │
      │                │     train G      │                │
      │                │     log loss     │                │
      │                │                  │                │
      │                │  保存权重         │                │
      │                │  dcgan_g.pth    │                │
      │                │                  │                │
      │                │  下载到本地       │                │
      │                │─────────────────▶│                │
      │                │                  │                │
      │                │                  │  复制到         │
      │                │                  │  ai_engine/    │
      │                │                  │  models/       │
      │                │                  │───────────────▶│
      │                │                  │                │
      │                │                  │                │  FastAPI reload
      │                │                  │                │  加载新权重
      │                │                  │                │
      │  通知: 训练完成  │                  │                │
      │◀───────────────│                  │                │
```

---

## 11. 安全设计

### 11.1 认证与授权

| 层级 | 方案 | 说明 |
|------|------|------|
| 密码存储 | bcrypt (cost=12) | `passlib[bcrypt]` 库 |
| Token签发 | JWT (HS256) | `python-jose` 库, 24小时过期 |
| Token存储(前端) | localStorage | Zustand persist 中间件 |
| Token传输 | HTTP Header `Authorization: Bearer <token>` | axios 拦截器自动注入 |
| 路由保护(前端) | `<ProtectedRoute>` 组件 | 检查 isAuthenticated，否则重定向登录页 |
| 路由保护(后端) | `Depends(get_current_user)` | FastAPI 依赖注入，解析JWT获取用户 |

### 11.2 安全措施清单

| 措施 | 实现方式 | 优先级 |
|------|---------|--------|
| CORS白名单 | 仅允许 `localhost:5173` (开发) | P0 |
| 文件上传校验 | 白名单 MIME type: `image/jpeg`, `image/png`, `image/webp` | P0 |
| 文件大小限制 | ≤10MB (FastAPI `UploadFile` + 服务层校验) | P0 |
| 输入验证 | Pydantic Schema 对所有请求参数进行类型+范围校验 | P0 |
| SQL注入防护 | SQLAlchemy ORM 参数化查询 | P0 |
| XSS防护 | React 默认转义输出 + 前端输入过滤 | P1 |
| CSRF防护 | JWT在Header中，非Cookie，天然防CSRF | P1 |
| 频率限制 | SlowAPI `@limiter.limit("20/minute")` (上传接口) | P1 |
| 敏感词过滤 | `better_profanity` 或自定义正则词表 | P1 |
| 管理员接口保护 | `Depends(get_current_admin_user)` 检查 role=='admin' | P0 |

### 11.3 API访问控制矩阵

| 接口 | 未登录 | 普通用户 | 管理员 |
|------|--------|---------|--------|
| GET /api/posts | ✅ 浏览 | ✅ | ✅ |
| POST /api/recognition/upload | ✅ (不记录用户) | ✅ | ✅ |
| GET /api/posts/{id} | ✅ | ✅ | ✅ |
| GET /api/characters | ✅ | ✅ | ✅ |
| GET /api/search | ✅ | ✅ | ✅ |
| POST /api/posts | ❌ | ✅ | ✅ |
| POST /api/posts/{id}/comments | ❌ | ✅ | ✅ |
| POST /api/posts/{id}/like | ❌ | ✅ | ✅ |
| POST /api/users/{id}/follow | ❌ | ✅ | ✅ |
| DELETE /api/posts/{id} | ❌ | ✅ (自己的) | ✅ (任意) |
| GET /api/analytics/overview | ✅ (脱敏版) | ✅ (脱敏版) | ✅ (完整版) |
| GET /api/analytics/behaviors | ❌ | ❌ | ✅ |

> **仪表盘权限说明**：`/api/analytics/overview` 对所有用户开放，但返回数据根据权限分级：
> - **未登录/普通用户**：返回脱敏版数据（总用户数、总识别数、热门角色排行），隐藏 DAU、留存率、行为详情等运营指标
> - **管理员**：返回完整版数据，包含所有运营指标和行为分析数据

---

## 12. 错误处理策略

### 12.1 统一错误响应格式

```json
{
  "detail": {
    "code": "RECOGNITION_FAILED",
    "message": "图像识别失败：模型推理异常",
    "request_id": "req_a1b2c3d4"
  }
}
```

### 12.2 HTTP状态码约定

| 状态码 | 含义 | 示例场景 |
|--------|------|---------|
| 200 | 成功 | 正常GET/PUT/DELETE |
| 201 | 创建成功 | POST创建资源 |
| 204 | 删除成功 (无返回体) | DELETE |
| 400 | 请求参数错误 | 文件格式不支持、字段校验失败 |
| 401 | 未认证 | Token过期/缺失 |
| 403 | 无权限 | 删除他人动态 |
| 404 | 资源不存在 | 动态/角色/用户不存在 |
| 409 | 冲突 | 用户名已存在、重复关注 |
| 413 | 文件过大 | 上传 >10MB |
| 422 | 输入验证失败 | Pydantic 校验不通过 |
| 429 | 频率限制 | 上传接口超限 |
| 500 | 服务器内部错误 | 模型推理异常、数据库连接失败 |

### 12.3 前端错误处理

| 场景 | 处理方式 |
|------|---------|
| 网络断开 | axios拦截器捕获，`message.error('网络连接失败，请检查网络')` |
| 401 Token过期 | 清除auth状态 → 弹出登录框或跳转登录页 |
| 服务器500 | `message.error('服务异常，请稍后重试')` + 错误边界 |
| 图片上传失败 | 上传组件显示错误状态 + 重试按钮 |
| 信息流加载失败 | 骨架屏 + 底部"加载失败，点击重试" |
| 空数据 | `<EmptyState>` 组件："还没有动态，去识别一张图片吧~" |

---

## 13. 部署与启动方案

### 13.1 Docker Compose 一键启动

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: anivision
      POSTGRES_USER: anivision
      POSTGRES_PASSWORD: dev_password_123
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://anivision:dev_password_123@db:5432/anivision
      SECRET_KEY: dev-secret-key-change-in-production
      UPLOAD_DIR: /app/data/uploads
    volumes:
      - ./data:/app/data
      - ./ai_engine/models:/app/ai_engine/models
    depends_on:
      - db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  pgdata:
```

### 13.2 本地开发启动（无 Docker）

```bash
# 1. 启动 PostgreSQL (需预先安装)
pg_ctl start

# 2. 初始化数据库
python scripts/init_db.py

# 3. 启动后端 (终端 1)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. 启动前端 (终端 2)
cd frontend
npm install
npm run dev
```

### 13.3 答辩演示检查清单

| 检查项 | 命令/操作 |
|--------|----------|
| 后端 API 文档可访问 | 浏览器打开 http://localhost:8000/docs |
| 前端页面可加载 | 浏览器打开 http://localhost:5173 |
| 数据库已初始化种子数据 | `python scripts/init_db.py --seed` |
| 模型权重已就位 | 检查 `ai_engine/models/*.pth` 文件存在 |
| GAN 生成功能可用 | 在仪表盘点击"生成示例" |

---

## 附录 A：文件清单

| 文件 | 说明 | 负责人建议 |
|------|------|-----------|
| `frontend/` | React前端项目 | 前端组员 (任务3) |
| `backend/app/api/` | API路由层 | 后组员 (任务3/4) |
| `backend/app/models/` | ORM模型 | 后端组员 |
| `backend/app/services/analytics_service.py` | 行为分析服务 | 任务4组员 |
| `backend/app/services/recommendation_service.py` | 推荐服务 | 任务4组员 |
| `ai_engine/recognition/` | 识别模型 | 任务2组员 |
| `ai_engine/gan/` | GAN模型 | 任务2组员 |
| `ai_engine/training/` | Colab训练Notebook | 任务2组员 |
| `data/datasets/` | 数据集管理 | 任务1组员 |
| `scripts/` | 数据工具脚本 | 任务1组员 |
| `docs/` | 文档 | 全组 |

## 附录 B：依赖版本清单

### Python (backend + ai_engine)

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.1
pydantic-settings==2.3.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
slowapi==0.1.9
aiofiles==23.2.1

torch==2.3.0
torchvision==0.18.0
pillow==10.3.0
opencv-python==4.9.0.80
albumentations==1.4.8
scikit-learn==1.5.0
pandas==2.2.2
numpy==1.26.4
```

### JavaScript (frontend)

```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "react-router-dom": "^6.23.1",
  "antd": "^5.17.0",
  "@ant-design/charts": "^2.1.0",
  "echarts": "^5.5.0",
  "echarts-for-react": "^3.0.2",
  "zustand": "^4.5.2",
  "axios": "^1.7.2",
  "dayjs": "^1.11.11"
}
```

---

> **本文档完成标志着设计阶段结束。**  
> **下一步**: 按照本文档的模块划分，各组成员可独立开始编码。  
> **前置文档**: [需求分析文档](requirements_analysis.md) · [技术选型方案](tech_selection.md)
