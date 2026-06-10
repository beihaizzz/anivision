# AniVision 环境配置指南

> 将本文档交给 OpenCode，一键完成环境搭建和模型训练。

---

## 你需要做的事

1. 把本文档保存为 `SETUP.md`，放到克隆好的仓库根目录
2. 在 OpenCode 中输入：**`按照 SETUP.md 配置环境并训练模型`**

OpenCode 会自动执行以下全部步骤。

---

## 环境要求

| 项目 | 最低要求 |
|------|---------|
| 操作系统 | Windows 10+ / Linux (Ubuntu 20.04+) |
| GPU | NVIDIA GPU (6GB+ VRAM)，驱动 ≥ 525 |
| Python | 3.11+ |
| 包管理器 | [uv](https://docs.astral.sh/uv/) (自动安装) |
| Git | 任意版本 |
| 磁盘 | ~10GB 空闲（含 PyTorch ~3GB + 数据集 ~120MB） |

---

## OpenCode 执行步骤

以下步骤应由 OpenCode 顺序执行，每步完成后验证再继续。

### Step 1: 克隆仓库

```bash
git clone <仓库地址> AniVision
cd AniVision
```

验证：`ls ai_engine/recognition/train.py` 应存在。

### Step 2: 检查 GPU 和 CUDA

```bash
nvidia-smi
```

预期输出：GPU 名称、驱动版本。若失败，检查驱动安装。

### Step 3: 安装 uv（如未安装）

Windows PowerShell:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux/macOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

验证：`uv --version` 应输出版本号。

### Step 4: 创建虚拟环境并安装依赖

```bash
cd ai_engine
uv sync
```

验证：`ls .venv/Scripts/python.exe` (Windows) 或 `ls .venv/bin/python` (Linux) 应存在。

### Step 5: 安装 PyTorch (CUDA 版本)

```bash
# Windows
$env:VIRTUAL_ENV = $null
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124 --python .venv/Scripts/python.exe

# Linux
unset VIRTUAL_ENV
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124 --python .venv/bin/python
```

验证：在 ai_engine 目录执行：
```bash
.venv/Scripts/python.exe -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```
应输出 `True` 和 GPU 名称。

### Step 6: 训练识别模型 (EfficientNet-B3)

```bash
# 确保在 ai_engine/ 目录
.venv/Scripts/python.exe -m recognition.train --epochs 50 --batch-size 16 --lr 0.001
```

训练约需 10-15 分钟（RTX 4060）。完成后检查：
```bash
ls models/best_model.pth          # 应存在 (~42MB)
ls models/class_names.json        # 应存在
```

### Step 7: 验证识别模型

```bash
.venv/Scripts/python.exe -c "
import sys; sys.path.insert(0, '.')
from recognition.predictor import RecognitionPredictor
from pathlib import Path

p = RecognitionPredictor('models/best_model.pth', 'models/label_map.json')
print(f'Model loaded on {p.device}, {len(p.label_map)} classes')

# Test on first validation image
test_dir = Path('../data/datasets/onepiece/val')
for char_dir in sorted(test_dir.iterdir()):
    if char_dir.is_dir():
        imgs = list(char_dir.glob('*.png'))
        if imgs:
            result = p.predict(str(imgs[0]), top_k=3)
            print(f'Test {char_dir.name}:')
            for pred in result['predictions']:
                print(f'  #{pred[\"rank\"]} {pred[\"character_name\"]} ({pred[\"confidence\"]:.4f})')
            break
"
```

预期：每个角色都能正确识别排名第一。

### Step 8 (可选): 训练 GAN 增强模型

```bash
.venv/Scripts/python.exe -m gan.train --epochs 200 --batch-size 64 --lr 0.0002
```

训练约需 30 分钟。完成后检查：
```bash
ls models/gan/generator_best.pth    # 应存在 (~50MB)
ls models/gan/samples/epoch_0200.png  # 样本图
```

### Step 9 (可选): 生成 GAN 增强数据

```bash
.venv/Scripts/python.exe -c "
import sys; sys.path.insert(0, '.')
from gan.generator import GANGenerator
from pathlib import Path

gen = GANGenerator('models/gan/generator_best.pth', num_classes=7)
names = ['lufei','luobin','namei','qiaoba','shanzhi','suolong','wusuopu']
out = Path('../data/generated/onepiece')

for cid, name in enumerate(names):
    (out / name).mkdir(parents=True, exist_ok=True)
    imgs = gen.generate(character_id=cid, count=30)
    for i, img in enumerate(imgs):
        img.save(out / name / f'gan_{i:03d}.png')
    print(f'  {name}: 30 images')

total = sum(1 for _ in out.rglob('*.png'))
print(f'Done. {total} images generated -> {out}')
"
```

---

## 目录结构确认

最终目录应包含：

```
AniVision/
├── ai_engine/
│   ├── recognition/           ← 识别模型代码
│   │   ├── model.py           (EfficientNet-B3)
│   │   ├── train.py           (训练脚本)
│   │   └── predictor.py       (推理器)
│   ├── gan/                   ← GAN 代码
│   │   ├── dcgan.py           (cDCGAN 架构)
│   │   ├── train.py           (GAN 训练脚本)
│   │   └── generator.py       (生成器封装)
│   ├── models/
│   │   ├── best_model.pth     ← 训练后的识别模型
│   │   ├── label_map.json     ← 标签映射
│   │   ├── class_names.json   ← 类名映射
│   │   ├── dataset.csv        ← 数据集索引
│   │   └── gan/               ← GAN 输出
│   ├── pyproject.toml         (uv 项目配置)
│   └── uv.lock                (依赖锁定)
├── data/
│   ├── datasets/onepiece/     ← 已划分的数据集
│   │   ├── train/ (430张)
│   │   ├── val/   (90张)
│   │   └── test/  (101张)
│   └── generated/onepiece/    ← GAN 生成图 (可选)
├── docs/                      ← 项目文档
└── SETUP.md                   ← 本文件
```

---

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| `uv sync` 失败 | 检查 Python 版本 ≥ 3.11，运行 `uv python install 3.12` |
| `torch.cuda.is_available() = False` | 检查 nvidia-smi 是否正常，重装 CUDA 版 PyTorch |
| 训练 OOM (显存不足) | 减小 batch size: `--batch-size 8` |
| 模型文件不存在 | 确保在 `ai_engine/` 目录下执行命令 |
| Windows DataLoader 卡住 | 添加 `--num-workers 0` |
