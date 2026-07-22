# Librario – 개인 만화·웹툰·전자책 서버
# 단일 이미지로 백엔드(FastAPI) + 프론트엔드(PWA) 를 함께 서빙합니다.
FROM python:3.12-slim

# 예약(심층) 스캔이 지정 시각에 정확히 돌도록 tzdata 설치 (TZ 환경변수 사용)
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data \
    FRONTEND_DIR=/app/frontend

WORKDIR /app

# 1) 의존성 먼저 설치 (레이어 캐시로 재빌드 빠르게)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 2) 애플리케이션 코드 복사
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# DB·썸네일·설정이 저장되는 영구 볼륨
VOLUME ["/data"]
EXPOSE 8080

# uvicorn 이 app 패키지를 찾을 수 있도록 backend 를 작업 디렉터리로
WORKDIR /app/backend

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=3).status==200 else 1)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
