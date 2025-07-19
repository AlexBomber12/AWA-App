FROM ubuntu:22.04 AS build
ARG WITH_CUDA=0
WORKDIR /llama
RUN apt-get update && apt-get install -y git build-essential cmake python3 curl
RUN git clone https://github.com/ggerganov/llama.cpp.git .
RUN if [ "$WITH_CUDA" = "1" ]; then make LLAMA_CUBLAS=1; else make -j; fi

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/llm_server/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY --from=build /llama /llama
COPY services/llm_server/download_and_quantize.sh /setup.sh
COPY services/llm_server/app.py /app.py
RUN bash /setup.sh
EXPOSE 8000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
HEALTHCHECK CMD curl -fs http://localhost:8000/health || exit 1
