# 使用官方的 Python 轻量级镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖清单并安装（利用 Docker 缓存机制）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制剩下的所有代码
COPY . .

# 默认启动命令（注意这里只跑测试，因为真实环境里被测系统通常已经在别的容器/服务器上跑着了）
CMD ["pytest", "tests/", "-v", "--alluredir=reports/allure-results"]