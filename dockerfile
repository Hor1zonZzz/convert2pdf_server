FROM ubuntu:22.04

# 安装Python、必要的构建工具和全面的字体支持
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository universe && add-apt-repository multiverse && apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    # 中文字体
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    # 更全面的字体支持
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-noto-color-emoji \
    fonts-noto-mono \
    fonts-noto-ui-core \
    # 西方字体
    fonts-dejavu \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    fonts-liberation \
    fonts-liberation2 \
    fonts-freefont-ttf \
    fonts-opensymbol \
    # 系统和基础字体
    fonts-urw-base35 \
    xfonts-utils \
    fontconfig \
    # 拉丁文和欧洲字体
    fonts-liberation \
    fonts-crosextra-carlito \
    fonts-crosextra-caladea \
    fonts-roboto \
    fonts-open-sans \
    fonts-ubuntu \
    # 多语言支持的综合字体
    fonts-noto-unhinted \
    fonts-ipafont \
    fonts-ipafont-gothic \
    fonts-ipafont-mincho \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    fonts-arphic-bkai00mp \
    fonts-arphic-bsmi00lp \
    fonts-arphic-gbsn00lp \
    fonts-arphic-gkai00mp \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-kacst-one \
    fonts-khmeros \
    fonts-khmeros-core \
    fonts-lklug-sinhala \
    fonts-sil-abyssinica \
    fonts-sil-ezra \
    fonts-sil-padauk \
    fonts-tibetan-machine \
    fonts-indic \
    fonts-beng \
    fonts-beng-extra \
    fonts-gujr \
    fonts-gujr-extra \
    fonts-knda \
    fonts-mlym \
    fonts-orya \
    fonts-orya-extra \
    fonts-telu \
    fonts-telu-extra \
    fonts-samyak \
    fonts-samyak-taml \
    fonts-samyak-gujr \
    fonts-samyak-deva \
    fonts-sarai \
    fonts-kalapi \
    fonts-nakula \
    fonts-navilu \
    fonts-gargi \
    # MS兼容字体
    cabextract \
    libreoffice \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装MS核心字体（需要接受EULA）
RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections \
    && apt-get update && apt-get install -y ttf-mscorefonts-installer \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml ./

# 创建requirements.txt文件
RUN echo "starlette==0.31.1" > requirements.txt && \
    echo "pydantic==2.5.3" >> requirements.txt && \
    echo "boto3==1.28.65" >> requirements.txt && \
    echo "loguru==0.7.0" >> requirements.txt && \
    echo "uvicorn==0.23.2" >> requirements.txt && \
    echo "aiohttp==3.8.5" >> requirements.txt && \
    echo "python-multipart==0.0.6" >> requirements.txt

# asyncio是Python标准库，不需要通过pip安装

# 直接使用pip安装依赖
RUN pip3 install -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/tmp /app/logs

# 复制应用代码
COPY main.py ./

# 设置环境变量（生产环境中应该使用更安全的方式注入这些值，如Docker Secrets或环境变量注入）
ENV S3_BUCKET_NAME=""
ENV S3_ACCESS_KEY_ID=""
ENV S3_SECRET_ACCESS_KEY=""
ENV S3_REGION="us-east-1"
ENV S3_ENDPOINT_URL=""
ENV PDF_EXPIRE_TIME="60"
ENV DOWNLOAD_URL_PREFIX=""

# 暴露服务端口
EXPOSE 7758

# 运行时确保有足够的权限创建和删除临时文件
RUN chmod -R 777 /app/tmp /app/logs

# 启动命令
CMD ["python3", "main.py"]

