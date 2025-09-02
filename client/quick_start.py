#!/usr/bin/env python3
"""
Convert2PDF 客户端快速开始脚本

这个脚本展示了最简单的使用方法，让你立即开始使用客户端
"""

import asyncio
from convert_client import ConvertClient


async def quick_start():
    """快速开始示例"""
    
    print("🚀 Convert2PDF 客户端快速开始")
    print("=" * 40)
    
    # 配置你的服务端信息
    SERVER_HOST = input("请输入服务端IP地址 (例如: 192.168.1.100): ").strip()
    SERVER_PORT = input("请输入服务端端口 (默认: 7758): ").strip()
    
    if not SERVER_HOST:
        print("❌ 请输入正确的IP地址")
        return
    
    SERVER_PORT = int(SERVER_PORT) if SERVER_PORT else 7758
    
    # 输入目录
    INPUT_DIR = input("请输入要转换的目录路径: ").strip()
    if not INPUT_DIR:
        print("❌ 请输入正确的目录路径")
        return
    
    try:
        print(f"\n🔗 连接服务端 {SERVER_HOST}:{SERVER_PORT}...")
        
        # 创建客户端
        client = ConvertClient(SERVER_HOST, SERVER_PORT)
        
        # 检查连接
        if not await client.connect():
            print("❌ 无法连接到服务端，请检查服务是否启动")
            return
        
        print(f"✅ 连接成功！支持 {len(client.supported_types)} 种文件格式")
        
        # 查找文件
        files = client.find_files(INPUT_DIR)
        if not files:
            print(f"❌ 在目录 {INPUT_DIR} 中没有找到可转换的文件")
            return
        
        print(f"📁 找到 {len(files)} 个可转换文件")
        
        # 确认转换
        confirm = input(f"\n是否开始转换这 {len(files)} 个文件？(y/N): ").strip().lower()
        if confirm != 'y':
            print("取消转换")
            return
        
        # 开始转换
        print("\n🔄 开始批量转换...")
        results = await client.convert_directory(INPUT_DIR)
        
        # 显示结果
        success_count = sum(1 for r in results if r.status == "success")
        error_count = len(results) - success_count
        
        print(f"\n📊 转换完成！")
        print(f"   总计: {len(results)} 个文件")
        print(f"   成功: {success_count} 个")
        print(f"   失败: {error_count} 个")
        
        if success_count > 0:
            print(f"\n✅ 成功转换的文件:")
            for result in results:
                if result.status == "success":
                    print(f"   📄 {result.original_file}")
                    print(f"      🔗 {result.converted_url}")
        
        if error_count > 0:
            print(f"\n❌ 转换失败的文件:")
            for result in results:
                if result.status == "error":
                    print(f"   📄 {result.original_file}: {result.error}")
        
        print(f"\n🎉 任务完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户取消操作")
    except Exception as e:
        print(f"❌ 执行失败: {e}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║       Convert2PDF 客户端 v1.0        ║
    ║                                      ║
    ║   简单几步，批量转换文档为PDF！        ║
    ║                                      ║
    ║   1. 输入服务端IP和端口              ║
    ║   2. 选择要转换的目录                ║ 
    ║   3. 坐等转换完成！                  ║
    ╚══════════════════════════════════════╝
    """)
    
    asyncio.run(quick_start())