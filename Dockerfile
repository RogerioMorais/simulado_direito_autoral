# Imagem de partida: um pequeno sistema Linux com Python instalado.
FROM python:3.11-slim
# Exibe mensagens imediatamente e guarda os modelos na pasta de cache.
ENV PYTHONUNBUFFERED=1 HF_HOME=/cache/huggingface
# Pasta de trabalho dentro do container, diferente da pasta no computador.
WORKDIR /app
# Tesseract lê palavras em imagens; os pacotes por/eng fornecem os idiomas.
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-por tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
# Instala o motor de cálculos para processador comum, sem exigir placa de vídeo.
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
# Copia a lista de dependências antes de instalar as bibliotecas da aplicação.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# Motor CPU para executar o modelo de linguagem GGUF do Hugging Face.
# Compila para o Linux da imagem; evita dependências incompatíveis de wheels externas.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake ninja-build \
    && CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_OPENMP=OFF" CMAKE_BUILD_PARALLEL_LEVEL=4 \
       pip install --no-cache-dir --no-binary=llama-cpp-python llama-cpp-python==0.3.19 \
    && rm -rf /var/lib/apt/lists/*
# Copia o programa, os exemplos e a interface para dentro da imagem.
COPY demo.py atividades.py analise_prompts.py autoria_textual.py gerar_recursos.py gerar_cartaz.py gerar_livro.py /app/
COPY recursos_exemplo /app/recursos_exemplo
COPY dados /app/dados
COPY web /app/web
# Documenta a porta interna. O Compose define a porta acessível no computador.
EXPOSE 8080
# Comando executado ao iniciar o container: liga o servidor da demonstração.
ENTRYPOINT ["python", "/app/demo.py"]
