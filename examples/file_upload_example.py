#!/usr/bin/env python3
"""
文件上传API使用示例

演示如何使用文件上传API上传文件并获取保存路径
"""

import asyncio
import json
import tempfile
from pathlib import Path
import httpx
from loguru import logger


class FileUploadClient:
    """文件上传客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def upload_single_file(self, file_path: str, custom_path: str = None) -> dict:
        """上传单个文件"""
        url = f"{self.base_url}/file/upload"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
                data = {}
                if custom_path:
                    data['custom_path'] = custom_path
                
                response = await self.client.post(url, files=files, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"单文件上传失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应内容: {e.response.text}")
            raise
    
    async def upload_multiple_files(self, file_paths: list, custom_path: str = None) -> dict:
        """上传多个文件"""
        url = f"{self.base_url}/file/upload/multiple"
        
        try:
            files = []
            for file_path in file_paths:
                with open(file_path, 'rb') as f:
                    files.append(('files', (Path(file_path).name, f.read(), 'application/octet-stream')))
            
            data = {}
            if custom_path:
                data['custom_path'] = custom_path
            
            response = await self.client.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"多文件上传失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应内容: {e.response.text}")
            raise
    
    async def get_upload_info(self) -> dict:
        """获取上传配置信息"""
        url = f"{self.base_url}/file/info"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取上传信息失败: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> dict:
        """删除文件"""
        url = f"{self.base_url}/file/delete/{file_path}"
        
        try:
            response = await self.client.delete(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"删除文件失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应内容: {e.response.text}")
            raise
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


def create_test_files():
    """创建测试文件"""
    test_files = []
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    # 创建测试JSON文件
    json_file = temp_dir / "test_config.json"
    json_data = {
        "name": "test_pipeline",
        "description": "测试管道配置",
        "components": [
            {"name": "test_component", "type": "event_monitor"}
        ]
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    test_files.append(str(json_file))
    
    # 创建测试文本文件
    txt_file = temp_dir / "test_data.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文本文件\n包含中文内容\n用于测试文件上传功能")
    test_files.append(str(txt_file))
    
    # 创建测试CSV文件
    csv_file = temp_dir / "test_data.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("名称,类型,描述\n")
        f.write("组件1,event_monitor,事件监控器\n")
        f.write("组件2,contract_caller,合约调用器\n")
    test_files.append(str(csv_file))
    
    logger.info(f"创建了 {len(test_files)} 个测试文件在: {temp_dir}")
    return test_files, temp_dir


async def main():
    """主函数"""
    print("文件上传API使用示例")
    print("=" * 50)
    
    # 创建测试文件
    test_files, temp_dir = create_test_files()
    
    # 创建API客户端
    client = FileUploadClient()
    
    try:
        print("1. 获取上传配置信息")
        print("-" * 30)
        
        upload_info = await client.get_upload_info()
        print(f"上传目录: {upload_info['upload_directory']}")
        print(f"最大文件大小: {upload_info['max_file_size_mb']} MB")
        print(f"支持的文件类型: {', '.join(upload_info['allowed_extensions'])}")
        print(f"目录结构: {upload_info['upload_structure']}")
        
        print(f"\n2. 上传单个文件")
        print("-" * 30)
        
        # 上传第一个文件
        single_result = await client.upload_single_file(test_files[0])
        print(f"上传结果: {json.dumps(single_result, indent=2, ensure_ascii=False)}")
        
        print(f"\n3. 上传多个文件")
        print("-" * 30)
        
        # 上传剩余文件
        multiple_result = await client.upload_multiple_files(test_files[1:])
        print(f"批量上传结果: {json.dumps(multiple_result, indent=2, ensure_ascii=False)}")
        
        print(f"\n4. 使用自定义路径上传")
        print("-" * 30)
        
        # 使用自定义路径上传
        custom_result = await client.upload_single_file(
            test_files[0], 
            custom_path="uploads/custom/test"
        )
        print(f"自定义路径上传结果: {json.dumps(custom_result, indent=2, ensure_ascii=False)}")
        
        print(f"\n5. 上传统计")
        print("-" * 30)
        
        total_uploaded = 1 + len(multiple_result['uploaded_files']) + 1  # 单个 + 批量 + 自定义路径
        total_failed = len(multiple_result.get('failed_files', []))
        
        print(f"总上传文件数: {total_uploaded}")
        print(f"上传成功数: {total_uploaded - total_failed}")
        print(f"上传失败数: {total_failed}")
        
        # 显示所有上传的文件路径
        print(f"\n6. 上传的文件路径")
        print("-" * 30)
        
        uploaded_paths = []
        uploaded_paths.append(single_result['file_path'])
        
        for file_info in multiple_result['uploaded_files']:
            uploaded_paths.append(file_info['file_path'])
        
        uploaded_paths.append(custom_result['file_path'])
        
        for i, path in enumerate(uploaded_paths, 1):
            print(f"文件 {i}: {path}")
        
        print(f"\n7. 文件验证")
        print("-" * 30)
        
        # 验证文件是否存在
        for path in uploaded_paths:
            file_exists = Path(path).exists()
            status = "✅ 存在" if file_exists else "❌ 不存在"
            file_size = Path(path).stat().st_size if file_exists else 0
            print(f"{Path(path).name}: {status} ({file_size} bytes)")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()
        
        # 清理测试文件
        try:
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"清理测试文件: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理测试文件失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行示例
    asyncio.run(main())
