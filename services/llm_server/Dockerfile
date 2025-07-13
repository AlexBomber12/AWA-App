FROM ubuntu:22.04
RUN apt-get update && apt-get install -y git build-essential cmake curl python3 python3-pip
RUN pip install fastapi uvicorn[standard] numpy sentencepiece
RUN git clone https://github.com/ggerganov/llama.cpp.git /llama && \
    cd /llama && make LLAMA_CUBLAS=1
COPY download_and_quantize.sh /setup.sh
RUN bash /setup.sh
COPY app.py /app.py
EXPOSE 8000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
