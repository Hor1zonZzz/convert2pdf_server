#!/usr/bin/env python3
"""
Convert2PDF 命令行工具

使用方法:
    python convert_cli.py --host 192.168.1.100 --port 7758 --input ./documents
    python convert_cli.py -h 192.168.1.100 -p 7758 -i ./documents -o ./output -w 10
"""

import argparse
import asyncio
import sys
from pathlib import Path
import json
from convert_client import ConvertClient, convert_directory_simple


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Convert2PDF 客户端 - 批量将文档转换为PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  基础使用：
    python convert_cli.py --host 192.168.1.100 --port 7758 --input ./documents
    
  高级使用：
    python convert_cli.py -h 192.168.1.100 -p 7758 -i ./documents -o ./output -w 10 -r
    
  测试连接：
    python convert_cli.py --host 192.168.1.100 --port 7758 --test
        """
    )
    
    # 必需参数
    parser.add_argument(
        "--host", "-H",
        required=True,
        help="服务端IP地址 (例如: 192.168.1.100)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=7758,
        help="服务端端口 (默认: 7758)"
    )
    
    # 输入输出
    parser.add_argument(
        "--input", "-i",
        help="输入目录路径 (包含要转换的文件)"
    )
    
    parser.add_argument(
        "--output", "-o", 
        help="输出目录路径 (可选，默认为输入目录的父目录)"
    )
    
    # 转换选项
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=5,
        help="并发转换数 (默认: 5)"
    )
    
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="递归搜索子目录"
    )
    
    parser.add_argument(
        "--no-save-results",
        action="store_true", 
        help="不保存结果到JSON文件"
    )
    
    # 连接选项
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="请求超时时间（秒，默认: 300）"
    )
    
    parser.add_argument(
        "--retries",
        type=int, 
        default=3,
        help="最大重试次数 (默认: 3)"
    )
    
    # 功能选项
    parser.add_argument(
        "--test",
        action="store_true",
        help="仅测试连接，不执行转换"
    )
    
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="列出服务端支持的文件类型"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，减少输出"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Convert2PDF Client v1.0.0"
    )
    
    return parser


async def test_connection(host: str, port: int) -> bool:
    """测试与服务端的连接"""
    try:
        client = ConvertClient(host, port)
        success = await client.connect()
        
        if success:
            print(f"✅ 成功连接到服务端 {host}:{port}")
            print(f"📋 服务端支持 {len(client.supported_types)} 种文件格式")
            return True
        else:
            print(f"❌ 无法连接到服务端 {host}:{port}")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


async def list_supported_types(host: str, port: int):
    """列出服务端支持的文件类型"""
    try:
        client = ConvertClient(host, port)
        if await client.connect():
            print(f"📋 服务端 {host}:{port} 支持的文件类型:")
            print("=" * 50)
            
            # 按类别分组显示（简单分类）
            categories = {
                "文档": [".doc", ".docx", ".odt", ".rtf", ".txt"],
                "表格": [".xls", ".xlsx", ".ods", ".csv"],
                "演示": [".ppt", ".pptx", ".odp"],
                "其他": []
            }
            
            # 分类
            remaining_types = set(client.supported_types)
            for category, types in categories.items():
                found_types = [t for t in types if t in remaining_types]
                if found_types:
                    print(f"\n{category}: {', '.join(found_types)}")
                    remaining_types -= set(found_types)
            
            # 其他类型
            if remaining_types:
                categories["其他"] = sorted(remaining_types)
                print(f"\n其他: {', '.join(categories['其他'])}")
            
            print(f"\n总计: {len(client.supported_types)} 种格式")
            
    except Exception as e:
        print(f"❌ 获取支持类型失败: {e}")


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 测试连接模式
    if args.test:
        success = await test_connection(args.host, args.port)
        sys.exit(0 if success else 1)
    
    # 列出支持类型模式  
    if args.list_types:
        await list_supported_types(args.host, args.port)
        sys.exit(0)
    
    # 检查必需参数
    if not args.input:
        print("❌ 错误: 必须指定输入目录 (--input)")
        parser.print_help()
        sys.exit(1)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 错误: 输入目录不存在: {input_path}")
        sys.exit(1)
    
    # 设置输出目录
    output_path = Path(args.output) if args.output else input_path.parent / "converted_files"
    
    # 静默模式设置
    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # 创建客户端
        client = ConvertClient(
            host=args.host,
            port=args.port, 
            timeout=args.timeout,
            max_retries=args.retries
        )
        
        print(f"🚀 开始批量转换")
        print(f"   服务端: {args.host}:{args.port}")
        print(f"   输入: {input_path}")
        print(f"   输出: {output_path}")
        print(f"   并发数: {args.workers}")
        print(f"   递归搜索: {'是' if args.recursive else '否'}")
        print("=" * 50)
        
        # 执行转换
        results = await client.convert_directory(
            directory=input_path,
            output_dir=output_path,
            max_workers=args.workers,
            recursive=args.recursive,
            save_results=not args.no_save_results
        )
        
        # 简要结果
        success_count = sum(1 for r in results if r.status == "success")
        error_count = len(results) - success_count
        
        if success_count > 0:
            print(f"\n🎉 转换完成！成功转换 {success_count} 个文件")
            
            if not args.quiet:
                print("成功的文件:")
                for result in results:
                    if result.status == "success":
                        file_name = Path(result.original_file).name
                        print(f"  ✅ {file_name}")
        
        if error_count > 0:
            print(f"\n⚠️ {error_count} 个文件转换失败:")
            for result in results:
                if result.status == "error":
                    file_name = Path(result.original_file).name
                    print(f"  ❌ {file_name}: {result.error}")
        
        sys.exit(0 if error_count == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())