"""Servidor da oficina: quatro atividades de investigação e comparação textual.

Fluxo: formulário → validação → atividade escolhida → resultado e relatório.
O programa não acessa páginas nem determina se houve plágio.
Comentários (linhas com #) explicam as instruções e não são executados.
"""
import mimetypes
from urllib.parse import unquote
import atividades
import hashlib
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Localiza os arquivos a partir da pasta deste programa.
BASE = Path(__file__).resolve().parent
MODEL_ID = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
# Cada modelo é baixado no primeiro uso e mantido em memória para a aula.
MODELS = {'texto': MODEL_ID, 'visual': 'sentence-transformers/clip-ViT-B-32'}
_models = {}
_lock = threading.Lock()


def load_model(kind):
    """Carrega apenas o modelo necessário à atividade, em processador comum."""
    if kind not in _models:
        from sentence_transformers import SentenceTransformer
        _models[kind] = SentenceTransformer(MODELS[kind], device='cpu', trust_remote_code=False)
    return _models[kind]


def save_report(result, activity):
    """Guarda o relatório na pasta compartilhada com o computador."""
    result['atividade'] = activity
    result['execucao_utc'] = datetime.now(timezone.utc).isoformat()
    output = BASE / 'resultados'
    output.mkdir(exist_ok=True)
    filename = activity + '_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f') + '.json'
    (output / filename).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def validate(data):
    """Confere os dois campos antes de entregar os textos ao modelo."""
    if not isinstance(data, dict):
        raise ValueError('Formato inválido.')
    texts = []
    for field, label in [('referencia', 'texto de referência'), ('texto_comparado', 'texto a comparar')]:
        value = data.get(field, '')
        if not isinstance(value, str) or not value.strip() or len(value) > 2000:
            raise ValueError(f'Informe o {label}, com até 2.000 caracteres.')
        texts.append(value)
    return tuple(texts)


def analyze(data):
    """Calcula proximidade de sentido; não dá um parecer sobre direitos autorais."""
    reference, compared = validate(data)
    with _lock:
        _model = load_model('texto')

        def chunks(text):
            # Tokens são pedaços de texto, nem sempre palavras completas.
            # Trechos curtos evitam que o modelo descarte o final de entradas longas.
            ids = _model.tokenizer.encode(text, add_special_tokens=False)
            return [_model.tokenizer.decode(ids[i:i+90], skip_special_tokens=True)
                    for i in range(0, len(ids), 90)]

        # O modelo transforma os trechos em listas de números chamadas vetores.
        # Normalizar coloca esses vetores em uma escala comparável.
        refs = _model.encode(chunks(reference), normalize_embeddings=True)
        vectors = _model.encode(chunks(compared), normalize_embeddings=True)
        # Compara cada par de trechos e guarda a maior proximidade encontrada.
        # 0,8 não significa 80% de cópia: textos do mesmo tema também podem pontuar alto.
        score = float((vectors @ refs.T).max())
        result = {
            'modelo': MODEL_ID,
            'revisao': getattr(_model[0].auto_model.config, '_commit_hash', None),
            # UTC é um horário de referência mundial; este é o momento da análise.
            'execucao_utc': datetime.now(timezone.utc).isoformat(),
            'referencia': reference,
            'texto_comparado': compared,
            'similaridade': round(score, 4),
            'metodo': 'Maior similaridade cosseno entre segmentos de até 90 tokens.',
            # Impressões digitais ajudam a conferir versões dos textos, mas não
            # comprovam autoria, autenticidade ou data da publicação original.
            'sha256_referencia': hashlib.sha256(reference.encode()).hexdigest(),
            'sha256_texto_comparado': hashlib.sha256(compared.encode()).hexdigest(),
        }
    return save_report(result, 'textos')



class Handler(BaseHTTPRequestHandler):
    """Recebe pedidos do navegador e devolve a página ou os dados da análise."""
    def send(self, status, body, content_type='application/json; charset=utf-8'):
        # A resposta informa situação (200 = sucesso), tipo e tamanho do conteúdo.
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        # GET é um pedido de leitura: página, exemplo inicial ou estado do serviço.
        if self.path == '/':
            self.send(200, (BASE / 'web/index.html').read_bytes(), 'text/html; charset=utf-8')
        elif self.path == '/api/cenario':
            self.send(200, json.loads((BASE / 'dados/cenario.json').read_text()))
        elif self.path == '/api/recursos':
            # Lista somente os recursos didáticos distribuídos junto ao projeto.
            resources = BASE / 'recursos_exemplo'
            manifest = {}
            for folder in ['imagens', 'criacao', 'livro', 'logs', 'licencas', 'evidencias']:
                manifest[folder] = [str(p.relative_to(resources)) for p in sorted((resources / folder).iterdir()) if p.is_file()]
            self.send(200, manifest)
        elif self.path.startswith('/recursos/'):
            # resolve + is_relative_to impedem que um endereço leia arquivos fora dos exemplos.
            root = (BASE / 'recursos_exemplo').resolve()
            path = (root / unquote(self.path[len('/recursos/'):])).resolve()
            if path.is_relative_to(root) and path.is_file():
                self.send(200, path.read_bytes(), mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            else:
                self.send(404, {'erro': 'Recurso não encontrado.'})
        elif self.path == '/health':
            self.send(200, {'status': 'ok', 'modelos_carregados': list(_models)})
        else:
            self.send(404, {'erro': 'Endereço não encontrado.'})

    def do_POST(self):
        # POST entrega as entradas à atividade escolhida na interface.
        routes = {'/api/imagens': atividades.images, '/api/criacao': atividades.chronology,
                  '/api/licenca': atividades.license_review, '/api/inventario': atividades.inventory}
        if self.path not in routes and self.path != '/api/analisar':
            self.send(404, {'erro': 'Endereço não encontrado.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 36000000:
                raise ValueError('Requisição vazia ou muito grande.')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Formato inválido.')
            if self.path == '/api/analisar':
                result = analyze(data)
            else:
                # Uma atividade por vez evita sobrecarregar o computador da aula.
                with _lock:
                    function = routes[self.path]
                    if self.path in ['/api/imagens', '/api/licenca']:
                        result = function(data, load_model)
                        kind = 'visual' if self.path == '/api/imagens' else 'texto'
                        model = _models[kind]
                        result['modelo'] = MODELS[kind]
                        # A revisão identifica a versão dos arquivos quando o modelo a informa.
                        component = model[0].auto_model if kind == 'texto' else getattr(model[0], 'model', None)
                        result['revisao'] = getattr(getattr(component, 'config', None), '_commit_hash', None)
                    else:
                        result = function(data)
                    # Guarda também as entradas textuais usadas na revisão da licença.
                    if self.path == '/api/licenca':
                        result['licenca_recebida'] = data['licenca']
                    result = save_report(result, self.path.split('/')[-1])
        except (ValueError, TypeError, KeyError) as exc:
            # 400 indica dados inválidos; 500 indica falha de processamento.
            self.send(400, {'erro': str(exc)})
        except Exception:
            import traceback
            traceback.print_exc()
            self.send(500, {'erro': 'Não foi possível analisar. Confira os logs e o download do modelo.'})
        else:
            self.send(200, result)


if __name__ == '__main__':
    # O Compose apresenta a porta interna 8080 como localhost:8091 no computador.
    print('Servidor na porta interna 8080. Abra http://localhost:8091 ao usar o Compose.', flush=True)
    ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
