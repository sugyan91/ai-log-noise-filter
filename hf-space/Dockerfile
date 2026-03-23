# Hugging Face Space (SDK: Docker, app_port: 8501 in README.md).
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app
# pip install --user puts scripts in ~/.local/bin; HF image PATH may omit it.
ENV PATH="/home/user/.local/bin:${PATH}"

# Space repo may omit requirements.txt; pin to same file as GitHub main.
RUN curl -fsSL -o requirements.txt \
    https://raw.githubusercontent.com/sugyan91/ai-log-noise-filter/main/requirements.txt \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=user app ./app
COPY --chown=user ui ./ui
# HF Space repos often omit samples/; fetch demo.log so "Load example" still works.
RUN mkdir -p samples && curl -fsSL -o samples/demo.log \
    https://raw.githubusercontent.com/sugyan91/ai-log-noise-filter/main/samples/demo.log
COPY --chown=user app.py ./app.py

ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address", "0.0.0.0"]
