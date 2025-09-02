#!/usr/bin/env python3
"""
简单示例：最基础的使用方法

这个示例展示了如何用最少的代码实现批量文件转换
"""

import asyncio
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from convert_client import ConvertClient


async def main():
    """简单示例：几行代码完成批量转换"""
    
    # 1. 创建客户端 - 只需要填写服务端IP和端口
    client = ConvertClient("192.168.1.100", 7758)
    
    # 2. 传入目录路径，自动批量转换
    results = await client.convert_directory("./test_documents")
    
    # 3. 查看结果
    print(f"\n转换完成! 共处理 {len(results)} 个文件")
    for result in results:
        if result.status == "success":
            print(f"✅ {result.original_file} -> {result.converted_url}")
        else:
            print(f"❌ {result.original_file}: {result.error}")


if __name__ == "__main__":
    # 运行转换
    asyncio.run(main())