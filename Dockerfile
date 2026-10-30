# CorpAssist app image (Streamlit UI + RAG + DB tool).
# Ollama runs as its own service in docker-compose, not in this image.
FROM python:3.11-slim

# curl is used by entrypoint.sh to health-check Ollama; build-essential covers
# any native wheels pulled by chromadb / sentence-transformers.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8501
ENTRYPOINT ["./entrypoint.sh"]
