#!/usr/bin/env python3
"""
Convert2PDF Client - 简单易用的PDF转换客户端

使用示例:
    # 基础用法
    client = ConvertClient("192.168.1.100", 7758)
    results = await client.convert_directory("/path/to/documents")
    
    # 高级用法
    results = await client.convert_directory(
        "/path/to/documents", 
        output_dir="/path/to/output",
        max_workers=10,
        recursive=True
    )
"""

import asyncio
import os
import pathlib
from typing import Dict, List, Optional, Union
import aiohttp
import aiofiles
from dataclasses import dataclass
from datetime import datetime
import logging
from tqdm.asyncio import tqdm
import time
import json


@dataclass
class ConvertResult:
    """转换结果数据类"""
    original_file: str
    status: str
    converted_url: Optional[str] = None
    error: Optional[str] = None
    elapsed_time: float = 0.0


class ConvertClient:
    """PDF转换客户端
    
    提供简单易用的文件批量转换功能，支持：
    - 自动连接检测
    - 异步并发处理
    - 智能重试机制
    - 进度实时显示
    - 结果导出
    """
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 7758,
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """初始化客户端
        
        Args:
            host: 服务端IP地址
            port: 服务端端口
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试间隔(秒)
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.supported_types: List[str] = []
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        pass
    
    async def connect(self) -> bool:
        """连接到服务端并获取基本信息
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 健康检查
            await self._health_check()
            
            # 获取支持的文件类型
            await self._get_supported_types()
            
            self.logger.info(f"✅ 成功连接到服务端 {self.base_url}")
            self.logger.info(f"📋 支持 {len(self.supported_types)} 种文件格式")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 连接服务端失败: {e}")
            return False
    
    async def _health_check(self):
        """健康检查"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    raise ConnectionError(f"服务端健康检查失败: {response.status}")
                result = await response.json()
                if result.get("status") != "ok":
                    raise ConnectionError("服务端状态异常")
    
    async def _get_supported_types(self):
        """获取支持的文件类型"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.base_url}/get_supported_file_types") as response:
                if response.status != 200:
                    raise ConnectionError(f"获取支持文件类型失败: {response.status}")
                result = await response.json()
                self.supported_types = result.get("supported_file_types", [])
    
    def is_supported_file(self, file_path: Union[str, pathlib.Path]) -> bool:
        """检查文件是否支持转换
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持
        """
        if not self.supported_types:
            return False
        
        file_path = pathlib.Path(file_path)
        return file_path.suffix.lower() in self.supported_types
    
    async def convert_file(self, file_path: Union[str, pathlib.Path]) -> ConvertResult:
        """转换单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            ConvertResult: 转换结果
        """
        file_path = pathlib.Path(file_path)
        start_time = time.time()
        
        if not file_path.exists():
            return ConvertResult(
                original_file=str(file_path),
                status="error",
                error="文件不存在",
                elapsed_time=time.time() - start_time
            )
        
        if not self.is_supported_file(file_path):
            return ConvertResult(
                original_file=str(file_path),
                status="error", 
                error=f"不支持的文件类型: {file_path.suffix}",
                elapsed_time=time.time() - start_time
            )
        
        # 执行转换（带重试）
        for attempt in range(self.max_retries + 1):
            try:
                result = await self._do_convert_file(file_path)
                result.elapsed_time = time.time() - start_time
                return result
                
            except Exception as e:
                if attempt < self.max_retries:
                    # 指数退避重试
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"转换失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                    self.logger.info(f"等待 {wait_time:.1f}秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    return ConvertResult(
                        original_file=str(file_path),
                        status="error",
                        error=f"转换失败 (已重试{self.max_retries}次): {str(e)}",
                        elapsed_time=time.time() - start_time
                    )
    
    async def _do_convert_file(self, file_path: pathlib.Path) -> ConvertResult:
        """执行文件转换的核心逻辑"""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # 准备multipart form data
            data = aiohttp.FormData()
            
            # 读取文件并添加到表单
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
                data.add_field('file', file_content, filename=file_path.name)
            
            # 发送转换请求
            async with session.post(f"{self.base_url}/convert", data=data) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    result = await response.json()
                    return ConvertResult(
                        original_file=str(file_path),
                        status=result.get("status", "unknown"),
                        converted_url=result.get("converted_url")
                    )
                else:
                    # 尝试解析错误信息
                    try:
                        error_data = json.loads(response_text)
                        error_msg = error_data.get("error", f"HTTP {response.status}")
                    except:
                        error_msg = f"HTTP {response.status}: {response_text}"
                    
                    raise Exception(error_msg)
    
    def find_files(
        self, 
        directory: Union[str, pathlib.Path], 
        recursive: bool = True
    ) -> List[pathlib.Path]:
        """查找目录中支持的文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归搜索子目录
            
        Returns:
            List[pathlib.Path]: 支持的文件列表
        """
        directory = pathlib.Path(directory)
        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"目录不存在或不是目录: {directory}")
            return []
        
        files = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and self.is_supported_file(file_path):
                files.append(file_path)
        
        self.logger.info(f"📁 在 {directory} 中找到 {len(files)} 个可转换文件")
        return files
    
    async def convert_directory(
        self,
        directory: Union[str, pathlib.Path],
        output_dir: Optional[Union[str, pathlib.Path]] = None,
        max_workers: int = 5,
        recursive: bool = True,
        save_results: bool = True
    ) -> List[ConvertResult]:
        """批量转换目录中的文件
        
        Args:
            directory: 输入目录
            output_dir: 结果保存目录（可选）
            max_workers: 最大并发数
            recursive: 是否递归搜索
            save_results: 是否保存结果到JSON文件
            
        Returns:
            List[ConvertResult]: 转换结果列表
        """
        # 确保已连接
        if not self.supported_types:
            if not await self.connect():
                raise ConnectionError("无法连接到服务端")
        
        # 查找文件
        files = self.find_files(directory, recursive)
        if not files:
            self.logger.warning("没有找到可转换的文件")
            return []
        
        # 创建输出目录
        if output_dir:
            output_dir = pathlib.Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建进度条
        progress_bar = tqdm(total=len(files), desc="转换进度", unit="文件")
        
        # 创建任务队列
        semaphore = asyncio.Semaphore(max_workers)
        results = []
        
        async def convert_with_progress(file_path):
            async with semaphore:
                result = await self.convert_file(file_path)
                progress_bar.update(1)
                progress_bar.set_postfix({
                    '成功': sum(1 for r in results if r.status == 'success'),
                    '失败': sum(1 for r in results if r.status == 'error'),
                    '当前': file_path.name[:20]
                })
                return result
        
        # 执行并发转换
        start_time = time.time()
        tasks = [convert_with_progress(file_path) for file_path in files]
        results = await asyncio.gather(*tasks)
        
        progress_bar.close()
        total_time = time.time() - start_time
        
        # 统计结果
        success_count = sum(1 for r in results if r.status == 'success')
        error_count = len(results) - success_count
        
        self.logger.info(f"\n📊 转换完成!")
        self.logger.info(f"   总计: {len(results)} 个文件")
        self.logger.info(f"   成功: {success_count} 个")
        self.logger.info(f"   失败: {error_count} 个")
        self.logger.info(f"   用时: {total_time:.1f} 秒")
        self.logger.info(f"   平均: {total_time/len(results):.1f} 秒/文件")
        
        # 保存结果
        if save_results:
            await self._save_results(results, output_dir or pathlib.Path(directory).parent)
        
        return results
    
    async def _save_results(
        self, 
        results: List[ConvertResult], 
        output_dir: pathlib.Path
    ):
        """保存转换结果到JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = output_dir / f"convert_results_{timestamp}.json"
        
        # 转换为可序列化的格式
        serializable_results = []
        for result in results:
            serializable_results.append({
                "original_file": result.original_file,
                "status": result.status,
                "converted_url": result.converted_url,
                "error": result.error,
                "elapsed_time": result.elapsed_time
            })
        
        # 写入文件
        async with aiofiles.open(result_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(serializable_results, indent=2, ensure_ascii=False))
        
        self.logger.info(f"💾 结果已保存到: {result_file}")


# 便捷函数
async def convert_directory_simple(
    host: str,
    port: int,
    directory: str,
    max_workers: int = 5
) -> List[ConvertResult]:
    """简化的目录转换函数
    
    Args:
        host: 服务端IP
        port: 服务端端口  
        directory: 要转换的目录
        max_workers: 并发数
        
    Returns:
        List[ConvertResult]: 转换结果
    """
    async with ConvertClient(host, port) as client:
        return await client.convert_directory(directory, max_workers=max_workers)


if __name__ == "__main__":
    # 示例用法
    async def main():
        # 基础用法
        client = ConvertClient("192.168.1.100", 7758)
        await client.connect()
        
        # 转换单个文件
        result = await client.convert_file("test.docx")
        print(f"转换结果: {result}")
        
        # 批量转换目录
        results = await client.convert_directory(
            "documents/", 
            max_workers=10,
            recursive=True
        )
        
        # 显示失败的文件
        for result in results:
            if result.status == "error":
                print(f"❌ {result.original_file}: {result.error}")
    
    # 运行示例
    # asyncio.run(main())
    print("Convert2PDF客户端已准备就绪！")
    print("使用方法请参考文档或运行 asyncio.run(main()) 查看示例")