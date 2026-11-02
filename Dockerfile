FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Training is offline from the committed CSV, in the same environment used for serving.
RUN python train.py
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit","run","app.py","--server.port=8501","--server.address=0.0.0.0","--server.headless=true","--browser.gatherUsageStats=false"]
