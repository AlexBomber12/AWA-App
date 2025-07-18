FROM ubuntu:22.04
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements*.txt constraints.txt ./
ARG CONSTRAINTS=""
RUN apt-get update && apt-get install -y git build-essential cmake curl python3 python3-pip \
    && if [ -n "$CONSTRAINTS" ] && [ -f "$CONSTRAINTS" ]; then \
        pip install -r requirements.txt -c "$CONSTRAINTS"; \
    else \
        pip install -r requirements.txt; \
    fi
RUN git clone https://github.com/ggerganov/llama.cpp.git /llama && cd /llama && make LLAMA_CUBLAS=1
COPY download_and_quantize.sh /setup.sh
RUN bash /setup.sh
COPY app.py /app.py
EXPOSE 8000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
