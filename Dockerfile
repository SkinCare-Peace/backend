FROM python:3.10-slim

# 시스템 의존성 설치 (OpenCV 및 Selenium/Chromium 지원)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app 폴더 내부의 콘텐츠를 /app으로 바로 복사
COPY app/ .

# 실행 명령어
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
