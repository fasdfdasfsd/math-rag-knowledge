# Content Validation Service — ADR-SEC-006 独立部署
# 用途: Pre-LLM / Post-LLM 内容安全审核（轻量独立应用）
FROM python:3.12-alpine

RUN apk add --no-cache curl && \
    pip install --no-cache-dir fastapi uvicorn[standard] pydantic

WORKDIR /app
COPY app.py /app/

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8010/health || exit 1

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8010", "app:app"]
