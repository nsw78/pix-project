# pix-project

**Minikube rodando dentro do WSL Ubuntu no Windows 10**, explorando cada passo, com comandos, códigos, explicações e testes.

---

# Passo 1 — Preparar Ambiente no WSL Ubuntu

### 1.1 Atualizar sistema

```bash
sudo apt update && sudo apt upgrade -y
```

---

### 1.2 Instalar Docker (será usado para rodar Minikube com driver Docker)

* Instalar dependências:

```bash
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
```

* Adicionar chave GPG oficial do Docker:

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

* Adicionar repositório Docker ao APT sources:

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

* Instalar Docker:

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
```

* Verificar instalação:

```bash
docker --version
```

---

### 1.3 Permitir executar Docker sem sudo (opcional, para facilitar)

```bash
sudo usermod -aG docker $USER
```

* Depois saia do terminal e entre de novo para o grupo ter efeito, ou:

```bash
newgrp docker
```

* Testar sem sudo:

```bash
docker run hello-world
```

---

### 1.4 Instalar Minikube

Baixar binário oficial Minikube Linux (atualmente 1.30+):

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm minikube-linux-amd64
```

Testar:

```bash
minikube version
```

---

### 1.5 Instalar kubectl

* Baixar a versão compatível:

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

Testar:

```bash
kubectl version --client
```

---

### 1.6 Configurar Docker para funcionar com Minikube

* Como você tem Docker instalado no WSL, Minikube pode usar esse Docker para criar os containers do cluster.

---

# Passo 2 — Criar e Iniciar Cluster Minikube

### 2.1 Iniciar Minikube usando driver docker:

```bash
minikube start --driver=docker
```

Vai baixar a imagem do Kubernetes e criar os containers para o cluster.

### 2.2 Verificar status

```bash
minikube status
kubectl get nodes
```

Você deve ver o nó rodando.

---

# Passo 3 — Criar Namespace para seu projeto (organizar melhor)

```bash
kubectl create namespace pix-project
```

Defina o namespace padrão para comandos que vamos usar depois:

```bash
kubectl config set-context --current --namespace=pix-project
```

---

# Passo 4 — Criar API Flask em Python + Dockerfile

### 4.1 Código da API — `app.py`

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'message': 'API Pix Rodando!'})

@app.route('/hello')
def hello():
    return jsonify({'message': 'Olá do endpoint /hello'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

### 4.2 Dockerfile para a API (no mesmo diretório)

```Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY app.py .

RUN pip install flask

EXPOSE 5000

CMD ["python", "app.py"]
```

---

### 4.3 Construir a imagem Docker local para usar no Minikube

Dentro do WSL, no diretório do projeto:

```bash
docker build -t pix-api:1.0 .
```

---

# Passo 5 — Implantar API no Kubernetes

### 5.1 Criar arquivo `deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pix-api-deployment
  labels:
    app: pix-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pix-api
  template:
    metadata:
      labels:
        app: pix-api
    spec:
      containers:
      - name: pix-api-container
        image: pix-api:1.0
        ports:
        - containerPort: 5000
```

---

### 5.2 Criar arquivo `service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: pix-api-service
spec:
  selector:
    app: pix-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: ClusterIP
```

---

### 5.3 Aplicar os manifests

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

---

### 5.4 Verificar pods e serviços

```bash
kubectl get pods
kubectl get svc
```

---

# Passo 6 — Testar API dentro do cluster

### 6.1 Abrir shell no pod da API

Pegue o nome do pod (ex: pix-api-deployment-xxxxx):

```bash
kubectl get pods
kubectl exec -it pix-api-deployment-xxxxx -- /bin/sh
```

### 6.2 Usar curl para testar endpoint local

Dentro do pod:

```bash
curl http://localhost:5000/
curl http://localhost:5000/hello
```

### 6.3 Testar acesso via serviço interno

Ainda dentro do pod:

```bash
curl http://pix-api-service/
```

Você deve receber o JSON da API.

---

# Passo 7 — Subir Prometheus e Grafana

### 7.1 Ativar addons no Minikube

```bash
minikube addons enable metrics-server
minikube addons enable dashboard
minikube addons enable ingress
minikube addons enable prometheus
```

*Obs: Se addon prometheus não funcionar, pode usar manifests customizados. Mas vamos tentar pelo addon.*

---

### 7.2 Verificar pods do Prometheus e Grafana

```bash
kubectl get pods -n kube-system
```

Procure pods com nomes `prometheus` e `grafana`.

---

# Passo 8 — Configurar API para expor métricas Prometheus (via Flask exporter)

### 8.1 Atualizar `app.py` para expor métricas

Adicione:

```python
from prometheus_client import start_http_server, Summary, Counter
import threading
import time

REQUEST_COUNT = Counter('request_count', 'Número total de requisições')

app = Flask(__name__)

@app.before_request
def before_request():
    REQUEST_COUNT.inc()

@app.route('/')
def index():
    return jsonify({'message': 'API Pix Rodando!'})

@app.route('/hello')
def hello():
    return jsonify({'message': 'Olá do endpoint /hello'})

@app.route('/metrics')
def metrics():
    from prometheus_client import generate_latest
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    # Inicia servidor prometheus numa porta paralela
    threading.Thread(target=lambda: start_http_server(8000), daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
```

---

### 8.2 Atualizar Dockerfile para incluir prometheus\_client

```Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY app.py .

RUN pip install flask prometheus_client

EXPOSE 5000 8000

CMD ["python", "app.py"]
```

---

### 8.3 Build e aplicar novamente

```bash
docker build -t pix-api:1.1 .
kubectl set image deployment/pix-api-deployment pix-api-container=pix-api:1.1
```

---

### 8.4 Configurar Prometheus para raspar essa métrica (opcional, avançado)

Você pode criar um `ServiceMonitor` (se estiver usando Prometheus Operator) ou adicionar um scrape config no Prometheus.
Mas para manter simples, vou deixar para depois ou podemos fazer manualmente.

---

# Passo 9 — Acessar Grafana

### 9.1 Encaminhar porta do Grafana para local

```bash
kubectl port-forward -n kube-system svc/grafana 3000:3000
```

Acesse no browser: [http://localhost:3000](http://localhost:3000)
Usuário padrão: `admin`
Senha padrão: `admin` (pode ser solicitado para mudar)

---

# Passo 10 — Criar teste unitário para API

### 10.1 Criar arquivo `test_app.py`

```python
import unittest
from app import app

class PixApiTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'API Pix Rodando', response.data)

    def test_hello(self):
        response = self.client.get('/hello')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Olá do endpoint', response.data)

if __name__ == '__main__':
    unittest.main()
```

---

### 10.2 Atualizar Dockerfile para rodar testes (exemplo)

Você pode criar um comando para rodar testes dentro do container:

```Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY app.py test_app.py ./

RUN pip install flask prometheus_client unittest2

EXPOSE 5000 8000

CMD ["python", "app.py"]
```

---

### 10.3 Rodar teste dentro do pod

Copie o arquivo `test_app.py` para dentro do pod:

```bash
kubectl cp test_app.py pix-api-deployment-xxxxx:/app/test_app.py
```

Entre no pod:

```bash
kubectl exec -it pix-api-deployment-xxxxx -- /bin/sh
```

Instale pip e unittest (se não tiver):

```bash
pip install unittest2
```

Rode o teste:

```bash
python -m unittest test_app.py
```

---

# Passo 11 — Testar chamada API via URL interna

Dentro do pod ou de outro pod:

```bash
curl http://pix-api-service/
```

---

# Passo 12 — Bônus: Configurar Ingress para acesso externo (opcional)

---

Se quiser, seguimos detalhando a configuração do Ingress.

---

---

# Recapitulando o que você deve fazer agora

1. Atualizar e instalar Docker + Minikube + kubectl no WSL Ubuntu
2. Iniciar minikube com driver docker
3. Criar namespace
4. Criar API Flask + Dockerfile + build local
5. Criar deployment + service e aplicar
6. Testar API dentro do cluster
7. Habilitar addons prometheus, grafana, ingress
8. Expor métricas na API e configurar
9. Acessar Grafana local
10. Criar teste unitário, rodar dentro do pod
11. Testar chamadas API interna
12. (Opcional) Configurar ingress

---
