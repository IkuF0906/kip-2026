# アプリ（FastAPI）のイメージ。画面（static/）は nginx が配信するが、単体でも動くように含めておく
FROM python:3.12-slim

# イメージを作ったコミット。/api/version で返す（GitHub Actions が渡す）
ARG APP_VERSION=dev
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DRILL_DB=/data/drill.db \
    DRILL_WORKER_MEMORY_MB=256 \
    APP_VERSION=$APP_VERSION

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY drill/ drill/
COPY static/ static/

# root で動かさない。DB は名前付きボリュームの /data に置く
RUN useradd --create-home app && mkdir /data && chown app /data
USER app
VOLUME /data

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/units')"

# nginx の後ろで動くので、X-Forwarded-* を信用する
CMD ["uvicorn", "drill.api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
