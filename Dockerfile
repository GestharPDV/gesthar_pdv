# Usa uma imagem base oficial do Python
FROM python:3.12-slim

# Define variáveis de ambiente para otimizar o Python no Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias para o PostgreSQL (psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia todo o código do projeto para dentro do container
COPY . .

# Expõe a porta que o Django usará
EXPOSE 8000

# Comando para iniciar o servidor (pode ser trocado por gunicorn em produção)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]