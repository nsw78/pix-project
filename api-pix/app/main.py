from flask import Flask, jsonify
from app.metrics import setup_metrics

def create_app():
    app = Flask(__name__)

    setup_metrics(app)

    @app.route('/')
    def index():
        return jsonify({'message': 'API Pix Rodando!'})

    @app.route('/hello')
    def hello():
        return jsonify({'message': 'Olá do endpoint /hello'})

    return app

def run_app():
    from prometheus_client import start_http_server
    import threading

    threading.Thread(target=lambda: start_http_server(8000), daemon=True).start()

    app = create_app()
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_app()
