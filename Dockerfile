# 使用 Debian 為基底的 Python 映像檔，確保有完整的套件管理員
FROM python:3.10-bullseye

# 1. 更新系統並安裝 WeasyPrint 需要的底層繪圖庫與【中文字型】
RUN apt-get update && apt-get install -y \
    pango1.0-tools \
    libpango1.0-dev \
    libffi-dev \
    shared-mime-info \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 2. 建立工作目錄
WORKDIR /app

# 3. 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# 4. 複製你的 main.py
COPY . .

# 5. 啟動 FastAPI (Render 會自動分配 PORT)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
