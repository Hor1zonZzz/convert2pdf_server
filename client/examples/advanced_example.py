#!/usr/bin/env python3
"""
高级示例：展示客户端的高级功能

包括：
- 连接检测
- 自定义并发数
- 递归目录搜索
- 结果过滤和处理
- 错误处理
"""

import asyncio
from pathlib import Path
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from convert_client import ConvertClient, ConvertResult


async def main():
    """高级用法示例"""
    
    print("🚀 Convert2PDF 高级客户端示例")
    print("=" * 50)
    
    # 1. 创建客户端，配置更多参数
    client = ConvertClient(
        host="192.168.1.100", 
        port=7758,
        timeout=600,        # 10分钟超时
        max_retries=5,      # 最多重试5次
        retry_delay=2.0     # 重试间隔2秒
    )
    
    # 2. 检查连接
    print("🔗 检查服务端连接...")
    if not await client.connect():
        print("❌ 无法连接到服务端，请检查服务是否启动")
        return
    
    # 3. 显示服务端信息
    print(f"📋 服务端支持的文件格式：{len(client.supported_types)} 种")
    print(f"   {', '.join(client.supported_types[:10])}{'...' if len(client.supported_types) > 10 else ''}")
    
    # 4. 查找可转换文件
    input_dir = "./test_documents"
    output_dir = "./converted_files"
    
    files = client.find_files(input_dir, recursive=True)
    if not files:
        print(f"❌ 在 {input_dir} 中没有找到可转换的文件")
        return
    
    print(f"\n📁 找到 {len(files)} 个可转换文件：")
    for file in files[:5]:  # 只显示前5个
        print(f"   📄 {file.name} ({file.stat().st_size} bytes)")
    if len(files) > 5:
        print(f"   ... 还有 {len(files) - 5} 个文件")
    
    # 5. 执行批量转换
    print(f"\n🔄 开始批量转换（并发数：10）...")
    
    results = await client.convert_directory(
        directory=input_dir,
        output_dir=output_dir,
        max_workers=10,     # 高并发
        recursive=True,     # 递归搜索
        save_results=True   # 保存结果
    )
    
    # 6. 结果分析
    print("\n📊 详细转换报告")
    print("=" * 50)
    
    success_results = [r for r in results if r.status == "success"]
    error_results = [r for r in results if r.status == "error"]
    
    print(f"✅ 成功转换：{len(success_results)} 个文件")
    print(f"❌ 转换失败：{len(error_results)} 个文件")
    
    if success_results:
        avg_time = sum(r.elapsed_time for r in success_results) / len(success_results)
        print(f"⏱️ 平均转换时间：{avg_time:.2f} 秒/文件")
        
        # 显示成功的文件
        print("\n✅ 成功转换的文件：")
        for result in success_results:
            file_name = Path(result.original_file).name
            print(f"   📄 {file_name} ({result.elapsed_time:.1f}s)")
            print(f"      🔗 {result.converted_url}")
    
    # 7. 错误分析
    if error_results:
        print(f"\n❌ 转换失败的文件：")
        error_stats = {}
        for result in error_results:
            error_type = result.error.split(':')[0] if result.error else "未知错误"
            error_stats[error_type] = error_stats.get(error_type, 0) + 1
            file_name = Path(result.original_file).name
            print(f"   📄 {file_name}: {result.error}")
        
        print(f"\n📈 错误统计：")
        for error_type, count in error_stats.items():
            print(f"   {error_type}: {count} 次")
    
    # 8. 生成报告
    await generate_report(results, output_dir)
    
    print(f"\n🎉 任务完成！转换后的文件保存在：{output_dir}")


async def generate_report(results: list[ConvertResult], output_dir: str):
    """生成详细的转换报告"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(output_dir) / f"conversion_report_{timestamp}.md"
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 生成Markdown报告
    report_content = f"""# PDF转换报告

**转换时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**总文件数**: {len(results)}
**成功转换**: {sum(1 for r in results if r.status == 'success')}
**转换失败**: {sum(1 for r in results if r.status == 'error')}

## 转换详情

### ✅ 成功转换的文件

| 文件名 | 用时(秒) | 下载链接 |
|-------|---------|---------|
"""
    
    for result in results:
        if result.status == "success":
            file_name = Path(result.original_file).name
            report_content += f"| {file_name} | {result.elapsed_time:.1f} | [下载]({result.converted_url}) |\n"
    
    report_content += """
### ❌ 转换失败的文件

| 文件名 | 错误信息 |
|-------|---------|
"""
    
    for result in results:
        if result.status == "error":
            file_name = Path(result.original_file).name
            report_content += f"| {file_name} | {result.error} |\n"
    
    # 写入报告文件
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 详细报告已生成：{report_file}")


if __name__ == "__main__":
    # 运行高级示例
    asyncio.run(main())