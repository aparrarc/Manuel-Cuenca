FROM python:3.12-slim
WORKDIR /app
COPY server/ /app/server/
COPY dist/ /app/dist/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 STATIC_DIR=/app/dist DATABASE_PATH=/data/bookings.sqlite PORT=8080
RUN mkdir -p /data && chown 10001:10001 /data
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)" || exit 1
CMD ["python", "-m", "server.app"]
