FROM python:3.9-slim

WORKDIR /app

# Copia o requirements.txt
COPY api-pix/requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação
COPY api-pix/app ./app
COPY api-pix/test ./test

# Expõe as portas da API e das métricas
EXPOSE 5000
EXPOSE 8000

# Comando de execução
CMD ["python", "-m", "app.main"]
