FROM python:3.10-slim

# 安裝 WeasyPrint 必備的系統底層繪圖庫與 Google 繁體中文黑體字型
RUN apt-get update && apt-get install -y \
    pango1.0-tools \
    libpango1.0-dev \
    libffi-dev \
    shared-mime-info \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render 會動態分配 PORT，所以我們讓 uvicorn 去抓系統變數
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
