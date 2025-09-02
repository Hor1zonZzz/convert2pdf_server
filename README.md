# Convert2PDF 完整解决方案 🚀

## 📋 项目概述

这是一个完整的文档转PDF解决方案，包含**服务端**和**客户端**两部分：

- **🖥️ [服务端](./server/)** - 高性能的PDF转换服务
- **📱 [客户端](./client/)** - 简单易用的批量转换工具

### 💡 设计理念

**A** **项目出发点**: 在RAG过程中文档格式多样，统一转为PDF后可实现同构处理，简化后续文字提取和图片处理流程。

**B** **多架构适配**: 支持Linux/Windows/macOS和x86/ARM64架构，不管业务方使用什么环境，都能快速部署使用。

**C** **上手简单**: 虽然支持多种部署方式，但基础使用非常简单 - 客户端只需3行代码即可实现批量转换。

## 🚀 快速开始

### 客户端使用（推荐）

```bash
# 1. 进入客户端目录
cd client/

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行快速开始脚本
python quick_start.py
```

然后按提示输入服务端IP、端口和文件目录即可！

### 服务端部署

```bash
# 进入服务端目录
cd server/

# 使用uv快速部署（推荐）
uv sync -i https://pypi.tuna.tsinghua.edu.cn/simple
uv run python main.py

# 或使用Docker
docker pull swr.cn-north-4.myhuaweicloud.com/wyyy/convert2pdf_server:0.4.0
```

## 📁 项目结构

```
convert2pdf_server/
├── 📁 client/              # 🎯 客户端（用户主要使用）
│   ├── convert_client.py   # 核心客户端类
│   ├── convert_cli.py      # 命令行工具
│   ├── quick_start.py      # 快速开始脚本
│   ├── requirements.txt    # 客户端依赖
│   ├── README.md          # 客户端详细文档
│   └── examples/          # 使用示例
│       ├── simple_example.py    # 简单示例
│       └── advanced_example.py  # 高级示例
│
├── 📁 server/              # 🖥️ 服务端
│   ├── main.py             # 单机版服务端
│   ├── main_multi_docker.py # 多容器版服务端
│   └── pyproject.toml      # 服务端依赖
│
├── 📁 doc/                 # 📚 文档
│   ├── DEVELOPMENT_DOC.md  # 开发文档
│   ├── README-k8s.md       # K8s部署指南
│   └── ...                 # 其他文档
│
├── 🐳 docker-compose.yml   # Docker编排
├── 🐳 dockerfile          # Docker镜像
├── ⚙️ k8s-*.yaml          # K8s配置文件
└── 📖 README.md           # 项目总览（本文档）
```

## 🎯 使用方式选择

### 🔰 初学者 / 快速体验
```bash
cd client/
python quick_start.py  # 交互式引导
```

### 💼 开发者 / 集成使用
```python
# 3行代码实现批量转换
from convert_client import ConvertClient
client = ConvertClient("192.168.1.100", 7758)
results = await client.convert_directory("./documents")
```

### 🖥️ 命令行用户
```bash
cd client/
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./documents -w 10
```

### 🔧 系统管理员 / 部署服务端
```bash
cd server/
uv run python main.py              # 单机版
uv run python main_multi_docker.py # 多容器高并发版
```

## ✨ 核心特性

### 客户端特性
- **🔌 即插即用**: 只需配置服务端IP和端口
- **⚡ 异步并发**: 支持高并发转换，大幅提升效率  
- **🔄 智能重试**: 内置指数退避重试机制
- **📊 实时进度**: 实时显示转换进度和统计信息
- **📁 批量处理**: 支持目录递归搜索
- **💾 结果保存**: 自动保存转换结果和报告

### 服务端特性
- **🏃‍♂️ 高性能**: 基于LibreOffice，支持20+种文件格式
- **🐳 多部署**: 支持裸机/Docker/K8s部署
- **☁️ 云存储**: 集成MinIO/S3对象存储
- **🔄 多架构**: 支持x86/ARM64，Linux/Windows/macOS
- **📈 可扩展**: 支持水平扩展和负载均衡

## 🎬 使用演示

### 最简使用 - 3行代码
```python
import asyncio
from client.convert_client import ConvertClient

async def main():
    client = ConvertClient("192.168.1.100", 7758)
    results = await client.convert_directory("./my_documents")
    print(f"转换完成！成功: {sum(1 for r in results if r.status == 'success')} 个")

asyncio.run(main())
```

### 命令行使用
```bash
# 基础使用
cd client/
python convert_cli.py --host 192.168.1.100 --port 7758 --input ./documents

# 高并发转换
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./docs -w 15 -r

# 测试连接
python convert_cli.py --host 192.168.1.100 --port 7758 --test
```

## 📚 详细文档

- **[客户端使用文档](./client/README.md)** - 详细的客户端使用指南
- **[服务端部署文档](./doc/)** - 完整的服务端部署方案
- **[开发文档](./doc/DEVELOPMENT_DOC.md)** - 二次开发和维护指南
- **[K8s部署文档](./doc/README-k8s.md)** - 大规模部署方案

## 🔧 部署方案选择

| 场景 | 推荐方案 | 部署复杂度 | 适用规模 |
|------|---------|-----------|---------|
| **快速体验** | 客户端 + 现有服务 | ⭐ | 个人使用 |
| **小规模业务** | 裸机部署服务端 | ⭐⭐ | < 10并发 |
| **生产环境** | Docker部署 | ⭐⭐⭐ | 10-50并发 |
| **高并发** | K8s + 多副本 | ⭐⭐⭐⭐ | > 50并发 |

## 🛠️ 环境要求

### 客户端环境
- Python 3.8+
- 依赖: `aiohttp`, `aiofiles`, `tqdm`

### 服务端环境
- Python 3.12+
- LibreOffice 7.x
- MinIO/S3 存储

## 🚨 常见问题

### Q: 客户端连接失败？
**A:** 检查服务端是否启动，IP和端口是否正确
```bash
# 测试连接
cd client/
python convert_cli.py --host YOUR_IP --port 7758 --test
```

### Q: 转换速度慢？
**A:** 调整并发数，根据服务端性能设置
```python
# 增加并发数
results = await client.convert_directory("./docs", max_workers=15)
```

### Q: 支持哪些文件格式？
**A:** 查看服务端支持的格式
```bash
cd client/
python convert_cli.py --host YOUR_IP --port 7758 --list-types
```

## 🤝 贡献 & 反馈

- 🐛 **Bug报告**: [提交Issue](https://github.com/ppppangu/convert2pdf_server/issues)
- 💡 **功能建议**: 欢迎提出改进建议
- 🔧 **代码贡献**: 提交Pull Request
- 📖 **文档完善**: 帮助改进文档

## 📄 许可证

本项目采用开源许可证，欢迎自由使用和修改。

---

**🎉 现在就开始使用吧！**

1. **想快速体验？** → `cd client/ && python quick_start.py`
2. **想集成到项目？** → 查看 [客户端文档](./client/README.md)  
3. **想部署服务？** → 查看 [服务端文档](./doc/)

**只需几分钟，即可拥有强大的批量PDF转换能力！** ✨