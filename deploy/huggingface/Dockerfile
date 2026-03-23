# Hugging Face Space (SDK: Docker). Local: docker build -f deploy/huggingface/Dockerfile -t log-filter .

FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd -m -u 1000 user

WORKDIR /home/user/app
COPY --chown=user app ./app
COPY --chown=user ui ./ui
COPY --chown=user samples ./samples
COPY --chown=user deploy/huggingface/app.py ./app.py

USER user

ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address", "0.0.0.0"]
