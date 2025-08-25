# 导入必要库
import asyncio
import os
import pathlib
import shutil
import time
import uuid

import aiohttp
import docker
from docker.errors import DockerException
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

# 加载环境变量,系统环境变量优先级最高
load_dotenv()

# 从环境变量中获取 s3 云存储的配置，用于上传文件到 s3 云存储
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

# 转换后的pdf在 S3 过期时间，单位为秒, 为0表示不设置过期时间
PDF_EXPIRE_TIME = int(os.getenv("PDF_EXPIRE_TIME", 0))
# 返回的下载地址，如果为空则返回S3ENDPOINTURL/BUCKETNAME/convert_file2pdf_server/文件名，不为空返回响应里为这里的下载地址开头，用于进行了端口映射后的情况
DOWNLOAD_URL_PREFIX = os.getenv("DOWNLOAD_URL_PREFIX", "")

# 下载文件时是否校验 SSL 证书，默认关闭（即跳过校验）；如需开启请将环境变量 DOWNLOAD_SSL_VERIFY 设为 true/1/yes
DOWNLOAD_SSL_VERIFY = os.getenv("DOWNLOAD_SSL_VERIFY", "false").lower() not in (
    "false",
    "0",
    "no",
)

# 1、文档格式
document_input_formats = [
    ".odt",  # OpenDocument文本文档
    ".doc",  # Microsoft Word 97-2003
    ".docx",  # Microsoft Word 2007-2019
    ".docm",  # Microsoft Word 2007-2019 (带宏)
    ".rtf",  # 富文本格式
    ".txt",  # 纯文本文档
    ".html",  # HTML文档
    ".htm",  # HTML文档
    ".xml",  # XML文档
    ".wps",  # WPS文本文档
    ".wpd",  # WordPerfect文档
    ".lwp",  # Lotus WordPro
    ".sdw",  # StarWriter文档
    ".sxw",  # OpenOffice.org 1.0 文本文档
]

document_output_formats = [
    ".odt",  # OpenDocument文本文档
    ".doc",  # Microsoft Word 97-2003
    ".docx",  # Microsoft Word 2007-2019
    ".rtf",  # 富文本格式
    ".txt",  # 纯文本文档
    ".html",  # HTML文档
    ".pdf",  # PDF文档
    ".epub",  # EPUB电子书格式
    ".xml",  # XML文档
]

# 2、电子表格格式
spreadsheet_input_formats = [
    ".ods",  # OpenDocument电子表格
    ".xls",  # Microsoft Excel 97-2003
    ".xlsx",  # Microsoft Excel 2007-2019
    ".xlsm",  # Microsoft Excel 2007-2019 (带宏)
    ".csv",  # 逗号分隔值
    ".tsv",  # 制表符分隔值
    ".dif",  # 数据交换格式
    ".sylk",  # 符号链接格式
    ".wk1",  # Lotus 1-2-3
    ".wks",  # Lotus 1-2-3
    ".123",  # Lotus 1-2-3
    ".sdc",  # StarCalc电子表格
    ".sxc",  # OpenOffice.org 1.0 电子表格
]

spreadsheet_output_formats = [
    ".ods",  # OpenDocument电子表格
    ".xls",  # Microsoft Excel 97-2003
    ".xlsx",  # Microsoft Excel 2007-2019
    ".csv",  # 逗号分隔值
    ".html",  # HTML表格
    ".pdf",  # PDF文档
    ".xml",  # XML电子表格
]

# 3、演示文稿格式
presentation_input_formats = [
    ".odp",  # OpenDocument演示文稿
    ".ppt",  # Microsoft PowerPoint 97-2003
    ".pptx",  # Microsoft PowerPoint 2007-2019
    ".pptm",  # Microsoft PowerPoint 2007-2019 (带宏)
    ".sdd",  # StarImpress演示文稿
    ".sxi",  # OpenOffice.org 1.0 演示文稿
]

presentation_output_formats = [
    ".odp",  # OpenDocument演示文稿
    ".ppt",  # Microsoft PowerPoint 97-2003
    ".pptx",  # Microsoft PowerPoint 2007-2019
    ".pdf",  # PDF文档
    ".html",  # HTML演示文稿
    ".swf",  # Flash演示文稿
]

# 4、绘图/图形格式
drawing_input_formats = [
    ".odg",  # OpenDocument绘图
    ".vsd",  # Microsoft Visio
    ".vsdx",  # Microsoft Visio
    ".wmf",  # Windows图元文件
    ".emf",  # 增强图元文件
    ".svg",  # 可缩放矢量图形
    ".sda",  # StarDraw绘图
    ".sxd",  # OpenOffice.org 1.0 绘图
]

drawing_output_formats = [
    ".odg",  # OpenDocument绘图
    ".pdf",  # PDF文档
    ".svg",  # 可缩放矢量图形
    ".png",  # 便携式网络图形
    ".jpg",  # JPEG图像
    ".jpeg",  # JPEG图像
    ".bmp",  # 位图图像
]

# 5、数据库格式
database_input_formats = [
    ".odb",  # OpenDocument数据库
    ".mdb",  # Microsoft Access数据库
    ".accdb",  # Microsoft Access数据库
    ".csv",  # 逗号分隔值(作为数据源)
]

database_output_formats = [
    ".odb",  # OpenDocument数据库
    ".csv",  # 逗号分隔值
    ".pdf",  # PDF报表
]

# 6、数学公式格式
formula_input_formats = [
    ".odf",  # OpenDocument公式
    ".mml",  # MathML
]

formula_output_formats = [
    ".odf",  # OpenDocument公式
    ".mml",  # MathML
    ".pdf",  # PDF文档
]

# supported_file_types = [
#     ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
#     ".odt", ".ods", ".odp", ".txt", ".rtf",
#     ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp",
#     ".html", ".htm", ".md", ".csv", ".tsv", ".xml"
# ]

supported_file_types = (
    document_input_formats
    + document_output_formats
    + spreadsheet_input_formats
    + spreadsheet_output_formats
    + presentation_input_formats
    + presentation_output_formats
    + drawing_input_formats
    + drawing_output_formats
    + database_input_formats
    + database_output_formats
    + formula_input_formats
    + formula_output_formats
)


# 创建Docker客户端的辅助函数
def create_docker_client():
    """创建并返回Docker客户端"""
    try:
        return docker.from_env()
    except DockerException as e:
        logger.error(f"Failed to create Docker client: {e}")
        return None


# Docker容器管理函数
async def convert_file_with_docker(
    file_url: str = None, file_path: str = None, task_uuid: str = None
) -> tuple[bool, dict]:
    """
    使用Docker容器转换文件为PDF
    支持两种模式：
    1. file_url: 直接传递URL给Docker容器
    2. file_path: 通过主服务器临时文件接口提供文件访问
    返回 (success, response_data) 的元组
    """
    if not file_url and not file_path:
        return False, {"error": "Either file_url or file_path is required"}

    client = create_docker_client()
    if not client:
        return False, {"error": "Failed to create Docker client"}

    container_name = f"pdf_converter_{task_uuid}"
    container = None

    try:
        # 启动Docker容器
        logger.info(f"Starting Docker container: {container_name}")

        # 准备环境变量
        env_vars = {
            "S3_BUCKET_NAME": S3_BUCKET_NAME,
            "S3_ACCESS_KEY_ID": S3_ACCESS_KEY_ID,
            "S3_SECRET_ACCESS_KEY": S3_SECRET_ACCESS_KEY,
            "S3_REGION": S3_REGION,
            "S3_ENDPOINT_URL": S3_ENDPOINT_URL,
            "PDF_EXPIRE_TIME": str(PDF_EXPIRE_TIME),
            "DOWNLOAD_URL_PREFIX": DOWNLOAD_URL_PREFIX or "",
        }

        container = client.containers.run(
            image="swr.cn-north-4.myhuaweicloud.com/wyyy/convert2pdf_server:0.4.0",
            name=container_name,
            ports={"7758/tcp": None},  # 动态分配端口
            detach=True,
            remove=False,  # 暂不自动删除，稍后手动清理
            environment=env_vars,
        )

        # 等待容器启动
        await asyncio.sleep(15)  # 等待15秒让容器完全启动

        # 获取容器端口映射
        container.reload()
        ports = container.attrs["NetworkSettings"]["Ports"]
        if "7758/tcp" not in ports or not ports["7758/tcp"]:
            return False, {"error": "Failed to get container port mapping"}

        host_port = ports["7758/tcp"][0]["HostPort"]
        logger.info(f"Container {container_name} started on port {host_port}")

        # 准备请求数据
        convert_url = f"http://localhost:{host_port}/convert"

        # 处理文件URL
        if file_url:
            # 模式1：直接传递URL给Docker容器
            logger.info(f"Using file_url mode: {file_url}")
            request_data = {"file_url": file_url}
        else:
            # 模式2：通过主服务器的临时文件接口提供文件访问
            logger.info(f"Using file_path mode: {file_path}")

            # 获取文件名
            file_name = os.path.basename(file_path)

            # 使用主服务器的临时文件接口
            temp_url = f"http://172.17.0.1:7758/temp/{task_uuid}/{file_name}"
            logger.info(f"File accessible at: {temp_url}")

            request_data = {"file_url": temp_url}

        # 发送转换请求
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    convert_url,
                    data=request_data,
                    timeout=aiohttp.ClientTimeout(total=600),  # 10分钟超时
                ) as response:
                    if response.status == 200:
                        # 获取响应JSON
                        response_data = await response.json()
                        logger.info("File conversion successful via Docker container")
                        return True, response_data
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Conversion request failed with status {response.status}: {error_text}"
                        )
                        return False, {
                            "error": f"Conversion request failed: {error_text}"
                        }

            except Exception as e:
                logger.error(f"Error during conversion request: {e}")
                return False, {"error": str(e)}

    except Exception as e:
        logger.error(f"Error managing Docker container: {e}")
        return False, {"error": str(e)}

    finally:
        # 清理Docker容器
        if container:
            try:
                container.stop(timeout=10)
                container.remove(force=True)
                logger.info(
                    f"Docker container {container_name} cleaned up successfully"
                )
            except Exception as e:
                logger.error(
                    f"Failed to cleanup Docker container {container_name}: {e}"
                )


# 编写初始化函数和关闭函数
async def on_startup():
    # 设置 日志文件 位置，每次启动自动生成一个log文件
    log_file = (
        pathlib.Path(__file__).parent
        / "logs"
        / f"log_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
    )
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(log_file, rotation="100 MB", retention="1000 days")
    logger.info(
        f"server start up, time: {time.strftime('%Y-%m-%d %H:%M:%S')}, s3 url is: {S3_ENDPOINT_URL}, log file is at: {log_file}"
    )


async def on_shutdown():
    logger.info(f"server shut down, time: {time.strftime('%Y-%m-%d %H:%M:%S')}")


# 健康检查接口
async def health(request: Request):
    return JSONResponse({"status": "ok"}, status_code=200)


# 获取支持的文件类型接口
async def get_supported_file_types(request: Request):
    return JSONResponse({"supported_file_types": supported_file_types}, status_code=200)


# 临时文件服务接口
async def serve_temp_file(request: Request):
    task_uuid = request.path_params["task_uuid"]
    filename = request.path_params["filename"]

    # 构造文件路径
    temp_dir = pathlib.Path(__file__).parent / "tmp" / task_uuid
    file_path = temp_dir / filename

    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    else:
        return JSONResponse({"error": "File not found"}, status_code=404)


class ConvertRequest(BaseModel):
    file_url: str


# 转换文件格式接口
async def convert(request: Request):
    # 获取客户端ip地址和表单数据
    client_ip = request.client.host
    form_data = await request.form()
    logger.info(
        f"client ip is : {client_ip}, time: {time.strftime('%Y-%m-%d %H:%M:%S')}, form data is: {form_data}"
    )

    # 支持两种方式：1. 通过file_url下载文件  2. 直接上传文件
    file_url = form_data.get("file_url")
    uploaded_file = form_data.get("file")

    # 检查是否提供了文件URL或上传的文件
    if not file_url and not uploaded_file:
        return JSONResponse(
            {"error": "Either file_url or file upload is required"}, status_code=400
        )

    # 如果同时提供了两个参数，优先使用file_url
    if file_url and uploaded_file:
        logger.warning("Both file_url and file provided, using file_url")
        uploaded_file = None

    # 处理文件扩展名和文件名
    if file_url:
        # 从URL获取文件信息
        file_url = file_url.strip("\"'\\[]")
        file_extension = file_url.split(".")[-1].strip("\"'\\[]")
        file_name = pathlib.Path(file_url.split("/")[-1].strip("\"'\\[]"))
        original_source = file_url
    else:
        # 从上传文件获取文件信息
        if not uploaded_file.filename:
            return JSONResponse(
                {"error": "Uploaded file must have a filename"}, status_code=400
            )
        file_name = pathlib.Path(uploaded_file.filename)
        file_extension = file_name.suffix.lstrip(".").lower()
        original_source = f"uploaded_file: {uploaded_file.filename}"

    # 检查文件是否已经是PDF
    if file_extension.lower() == "pdf":
        return JSONResponse({"error": "file is already pdf"}, status_code=400)

    # 检查文件扩展名是否在支持的列表中
    file_ext_with_dot = f".{file_extension.lower()}"
    if file_ext_with_dot not in supported_file_types:
        return JSONResponse(
            {"error": f"file type not supported, given file type is: {file_extension}"},
            status_code=400,
        )

    # 生成任务UUID
    task_uuid = str(uuid.uuid4())

    # 创建任务专用的临时文件夹
    download_file_dir = pathlib.Path(__file__).parent / "tmp" / task_uuid
    download_file_dir.mkdir(parents=True, exist_ok=True)

    # 生成下载文件路径
    download_file_path = download_file_dir / file_name

    # 结果字典
    result = {
        "status": "success",
        "original_source": original_source,
        "converted_url": "",
    }

    try:
        # 获取文件内容（下载或保存上传的文件）
        try:
            if file_url:
                # 从URL下载文件
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(
                            file_url,
                            timeout=aiohttp.ClientTimeout(total=300),
                            ssl=DOWNLOAD_SSL_VERIFY,  # 根据环境变量决定是否校验 SSL
                        ) as response:
                            if response.status != 200:
                                # 记录非 200 状态码以便排查
                                logger.error(
                                    f"Failed to download file, url: {file_url}, status: {response.status}, reason: {response.reason}"
                                )
                                raise RuntimeError(
                                    f"Download failed, status code: {response.status}, reason: {response.reason}"
                                )
                            with open(download_file_path, "wb") as f:
                                f.write(await response.read())
                    except Exception as download_exc:
                        # 捕获下载过程中的异常，输出更详细的日志
                        logger.error(
                            f"Exception occurred while downloading file: {file_url}, error: {download_exc}"
                        )
                        raise
                logger.info(
                    f"File downloaded successfully, file_url: {file_url}, time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                # 保存上传的文件
                with open(download_file_path, "wb") as f:
                    f.write(await uploaded_file.read())
                logger.info(
                    f"File uploaded successfully, filename: {uploaded_file.filename}, time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
        except Exception as e:
            logger.error(
                f"Failed to process file, source: {original_source}, error: {e}"
            )
            return JSONResponse({"error": "Failed to process file"}, status_code=500)

        # 使用Docker容器转换文件为PDF
        try:
            logger.info(
                f"Converting file with Docker container, task_uuid: {task_uuid}"
            )

            # 统一使用file_path模式调用Docker转换函数，避免重复下载
            # 无论是从URL下载还是直接上传，都使用已保存到本地的文件路径
            logger.info(
                f"Using file_path mode for Docker conversion: {download_file_path}"
            )
            success, response_data = await convert_file_with_docker(
                file_path=str(download_file_path), task_uuid=task_uuid
            )

            if success:
                # 转换成功，返回Docker服务返回的响应数据
                result.update(response_data)
                logger.info(
                    f"File conversion successful via Docker container, task_uuid: {task_uuid}"
                )
                del result["original_url"]
                logger.info(f"Conversion result: {result}")
            else:
                # 转换失败
                logger.error(
                    f"Failed to convert file via Docker container, task_uuid: {task_uuid}, error: {response_data}"
                )
                return JSONResponse(
                    {
                        "error": response_data.get(
                            "error", "Failed to convert file via Docker"
                        )
                    },
                    status_code=500,
                )
        except Exception as e:
            logger.error(
                f"Failed to convert file via Docker, source: {original_source}, error: {e}"
            )
            return JSONResponse(
                {"error": "Failed to convert file via Docker"}, status_code=500
            )

    finally:
        # 删除任务临时目录
        if download_file_dir.exists():
            try:
                shutil.rmtree(download_file_dir)
                logger.info(f"Deleted task directory: {download_file_dir}")
            except Exception as e:
                logger.error(
                    f"Failed to delete task directory: {download_file_dir}, error: {e}"
                )

    return JSONResponse(result, status_code=200)


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/get_supported_file_types", get_supported_file_types, methods=["GET"]),
        Route("/convert", convert, methods=["POST"]),
        Route("/temp/{task_uuid}/{filename:path}", serve_temp_file, methods=["GET"]),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
            expose_headers=["*"],
            allow_origin_regex="https?://.*",
        )
    ],
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7758)
