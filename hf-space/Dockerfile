# Hugging Face Space (SDK: Docker, app_port: 8501 in README.md).
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# pip as root → streamlit in /usr/local/bin (on PATH); non-root pip often breaks HF's `streamlit` exec.
RUN curl -fsSL -o /tmp/requirements.txt \
    https://raw.githubusercontent.com/sugyan91/ai-log-noise-filter/main/requirements.txt \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd -m -u 1000 user

WORKDIR /home/user/app
COPY --chown=user app ./app
COPY --chown=user ui ./ui
RUN mkdir -p samples \
    && curl -fsSL -o samples/demo.log \
    https://raw.githubusercontent.com/sugyan91/ai-log-noise-filter/main/samples/demo.log \
    && chown -R user:user samples
COPY --chown=user app.py ./app.py

USER user

ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address", "0.0.0.0"]
