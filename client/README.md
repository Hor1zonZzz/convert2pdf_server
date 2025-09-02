# Convert2PDF 客户端 🚀

一个简单易用的PDF转换客户端，让你只需几行代码就能实现高并发的批量文件转换。

## ✨ 特性

- **🔌 即插即用**: 只需配置服务端IP和端口
- **⚡ 异步并发**: 支持高并发转换，大幅提升效率
- **🔄 智能重试**: 内置指数退避重试机制，确保转换成功
- **📊 实时进度**: 实时显示转换进度和统计信息
- **📁 批量处理**: 支持目录递归搜索，一次处理多个文件
- **💾 结果保存**: 自动保存转换结果和详细报告
- **🛡️ 错误处理**: 完善的错误处理和日志记录

## 🚀 快速开始

### 安装依赖

```bash
pip install aiohttp aiofiles tqdm
# 或者
pip install -r requirements.txt
```

### 最简单的用法

```python
import asyncio
from convert_client import ConvertClient

async def main():
    # 1. 创建客户端 - 只需要填写服务端IP和端口
    client = ConvertClient("192.168.1.100", 7758)
    
    # 2. 传入目录路径，自动批量转换
    results = await client.convert_directory("./documents")
    
    # 3. 查看结果
    for result in results:
        if result.status == "success":
            print(f"✅ {result.original_file} -> {result.converted_url}")

# 运行
asyncio.run(main())
```

### 命令行使用

```bash
# 基础使用
python convert_cli.py --host 192.168.1.100 --port 7758 --input ./documents

# 高并发转换
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./documents -w 10 -r

# 测试连接
python convert_cli.py --host 192.168.1.100 --port 7758 --test
```

## 📖 详细使用指南

### 1. 客户端类使用

#### 基础初始化

```python
from convert_client import ConvertClient

# 基础配置
client = ConvertClient("192.168.1.100", 7758)

# 高级配置
client = ConvertClient(
    host="192.168.1.100",
    port=7758,
    timeout=600,        # 10分钟超时
    max_retries=5,      # 最多重试5次
    retry_delay=2.0     # 重试间隔2秒
)
```

#### 连接检测

```python
# 检查服务端连接
if await client.connect():
    print("连接成功!")
    print(f"支持 {len(client.supported_types)} 种文件格式")
```

#### 单文件转换

```python
# 转换单个文件
result = await client.convert_file("document.docx")

if result.status == "success":
    print(f"转换成功: {result.converted_url}")
else:
    print(f"转换失败: {result.error}")
```

#### 批量转换目录

```python
# 批量转换（基础）
results = await client.convert_directory("./documents")

# 批量转换（高级配置）
results = await client.convert_directory(
    directory="./documents",      # 输入目录
    output_dir="./output",       # 输出目录
    max_workers=10,              # 并发数
    recursive=True,              # 递归搜索
    save_results=True            # 保存结果
)
```

#### 使用上下文管理器

```python
# 推荐的使用方式
async with ConvertClient("192.168.1.100", 7758) as client:
    results = await client.convert_directory("./documents")
```

### 2. 命令行工具使用

#### 基础命令

```bash
# 转换指定目录
python convert_cli.py --host 192.168.1.100 --port 7758 --input ./documents

# 指定输出目录
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./docs -o ./output

# 递归搜索子目录
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./docs -r
```

#### 高级选项

```bash
# 设置高并发
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./docs -w 20

# 自定义超时和重试
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./docs --timeout 600 --retries 5

# 静默模式
python convert_cli.py -H 192.168.1.100 -p 7758 -i ./docs --quiet
```

#### 实用功能

```bash
# 测试服务端连接
python convert_cli.py --host 192.168.1.100 --port 7758 --test

# 查看支持的文件类型
python convert_cli.py --host 192.168.1.100 --port 7758 --list-types

# 查看帮助
python convert_cli.py --help
```

### 3. 便捷函数

```python
from convert_client import convert_directory_simple

# 一行代码完成转换
results = await convert_directory_simple(
    host="192.168.1.100",
    port=7758,
    directory="./documents",
    max_workers=5
)
```

## 📊 转换结果

### 结果对象

每个转换操作都会返回一个 `ConvertResult` 对象：

```python
@dataclass
class ConvertResult:
    original_file: str          # 原文件路径
    status: str                 # 转换状态: "success" 或 "error"
    converted_url: str          # 转换后的下载链接
    error: str                  # 错误信息（如果失败）
    elapsed_time: float         # 转换耗时（秒）
```

### 结果处理

```python
results = await client.convert_directory("./documents")

# 统计结果
success_count = sum(1 for r in results if r.status == "success")
error_count = len(results) - success_count

print(f"成功: {success_count}, 失败: {error_count}")

# 处理成功的结果
for result in results:
    if result.status == "success":
        print(f"✅ {result.original_file}")
        print(f"   下载: {result.converted_url}")
        print(f"   耗时: {result.elapsed_time:.1f}秒")

# 处理失败的结果
for result in results:
    if result.status == "error":
        print(f"❌ {result.original_file}: {result.error}")
```

## 🔧 高级配置

### 并发控制

```python
# 根据服务端性能调整并发数
client = ConvertClient("192.168.1.100", 7758)

# CPU密集型服务，建议并发数 = CPU核心数 * 2
results = await client.convert_directory(
    "./documents",
    max_workers=8  # 4核CPU建议使用8并发
)
```

### 重试策略

```python
# 自定义重试策略
client = ConvertClient(
    "192.168.1.100", 7758,
    max_retries=5,      # 最大重试5次
    retry_delay=1.5     # 初始延迟1.5秒，使用指数退避
)
```

### 超时设置

```python
# 处理大文件时增加超时时间
client = ConvertClient(
    "192.168.1.100", 7758,
    timeout=1800  # 30分钟超时
)
```

## 📋 支持的文件格式

客户端会自动从服务端获取支持的文件格式，常见格式包括：

- **文档**: .doc, .docx, .odt, .rtf, .txt, .html
- **表格**: .xls, .xlsx, .ods, .csv, .tsv  
- **演示**: .ppt, .pptx, .odp
- **图像**: .jpg, .jpeg, .png, .bmp, .tiff
- **其他**: .xml, .md 等

## 🚨 错误处理

### 常见错误及解决方案

1. **连接失败**
   ```
   ❌ 无法连接到服务端
   ```
   - 检查服务端是否启动
   - 检查IP地址和端口是否正确
   - 检查网络连接

2. **文件格式不支持**
   ```  
   ❌ 不支持的文件类型: .xyz
   ```
   - 使用 `--list-types` 查看支持的格式
   - 确认文件扩展名正确

3. **转换超时**
   ```
   ❌ 转换失败: timeout
   ```
   - 增加 `timeout` 参数
   - 减少并发数 `max_workers`
   - 检查服务端性能

4. **权限错误**
   ```
   ❌ 文件不存在或无权限访问
   ```
   - 检查文件路径
   - 确认文件读取权限

### 日志调试

```python
import logging

# 开启调试日志
logging.basicConfig(level=logging.DEBUG)

client = ConvertClient("192.168.1.100", 7758)
# 现在会看到详细的调试信息
```

## 📁 项目结构

```
convert2pdf_client/
├── convert_client.py       # 核心客户端类
├── convert_cli.py         # 命令行工具
├── requirements.txt       # 依赖文件
├── CLIENT_README.md       # 说明文档
└── examples/              # 使用示例
    ├── simple_example.py  # 简单示例
    └── advanced_example.py # 高级示例
```

## 🤝 实际使用场景

### 场景1: 文档中心批量转换

```python
# 批量转换公司文档
async with ConvertClient("doc-server", 7758) as client:
    results = await client.convert_directory(
        "/company/documents",
        output_dir="/company/pdfs", 
        max_workers=15,
        recursive=True
    )
```

### 场景2: 自动化流水线

```python
# 定时任务批量处理
import schedule
import asyncio

async def daily_convert():
    async with ConvertClient("192.168.1.100", 7758) as client:
        await client.convert_directory("/daily/uploads")

# 每天凌晨2点执行
schedule.every().day.at("02:00").do(lambda: asyncio.run(daily_convert()))
```

### 场景3: 与其他系统集成

```python
# 与文件上传系统集成
async def process_uploaded_files(upload_dir):
    async with ConvertClient("convert-service", 7758) as client:
        results = await client.convert_directory(upload_dir)
        
        # 通知其他系统
        for result in results:
            if result.status == "success":
                await notify_system(result.converted_url)
```

## 🛠️ 故障排除

### 性能优化建议

1. **合理设置并发数**: 根据服务端CPU核心数调整
2. **网络优化**: 确保客户端与服务端网络延迟较低
3. **文件大小**: 超大文件建议单独处理
4. **批次处理**: 文件过多时分批处理

### 监控建议

```python
# 添加转换监控
results = await client.convert_directory("./docs")

# 统计分析
total_time = sum(r.elapsed_time for r in results)
avg_time = total_time / len(results)
success_rate = sum(1 for r in results if r.status == "success") / len(results)

print(f"平均转换时间: {avg_time:.2f}秒")
print(f"成功率: {success_rate:.1%}")
```

## 📞 联系支持

如有问题，请：

1. 查看日志获取详细错误信息
2. 确认服务端状态和版本
3. 提供错误重现步骤
4. 联系技术支持

---

**🎉 现在就开始使用吧！只需几行代码，轻松实现批量PDF转换！**