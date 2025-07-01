from prometheus_client import Counter

REQUEST_COUNT = Counter('request_count', 'Número total de requisições')

def setup_metrics(app):
    from prometheus_client import generate_latest

    @app.before_request
    def before_request():
        REQUEST_COUNT.inc()

    @app.route('/metrics')
    def metrics():
        return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
