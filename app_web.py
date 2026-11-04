"""
app_web.py - Servidor do front-end HTML + API REST (somente biblioteca padrão).

Rodar:  python app_web.py      e abrir http://localhost:8000

Rotas da API:
  GET    /api/produtos                     lista produtos
  POST   /api/produtos                     cria produto {nome, quantidade, valor}
  GET    /api/produtos/<id>                árvore do produto (explosão)
  GET    /api/produtos/<id>/producao?n=10  componentes e valor de aquisição
  POST   /api/produtos/<id>/implosao       remonta o custo
  POST   /api/componentes                  cria componente {pai_id, nome, quantidade, valor}
  PUT    /api/componentes/<id>             edita {nome, quantidade, valor}
  PUT    /api/componentes/<id>/valor       atualiza só o valor {valor}
  DELETE /api/componentes/<id>             exclui (com descendentes)
  POST   /api/exemplos                     carrega Caneta e Computador
"""
import json
import os
import re
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from arvore import arvore_para_dict, necessidade, implosao, calcular_total, formatar_arvore
from banco import Repositorio
from dados_exemplo import carregar_exemplos

PORTA = 8000
PASTA_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
repo = Repositorio()
if not repo.listar_produtos():
    carregar_exemplos(repo)


class Handler(BaseHTTPRequestHandler):
    # ---------------------------------------------------------------- util
    def _json(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self) -> dict:
        tam = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(tam) or b"{}") if tam else {}

    def _arquivo(self, caminho, tipo):
        with open(caminho, "rb") as f:
            dados = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def log_message(self, fmt, *args):
        print("[web]", fmt % args)

    def _rota(self, metodo):
        url = urlparse(self.path)
        p = url.path.rstrip("/") or "/"
        q = parse_qs(url.query)
        try:
            if metodo == "GET" and p in ("/", "/index.html"):
                return self._arquivo(os.path.join(PASTA_WEB, "index.html"), "text/html; charset=utf-8")

            if p == "/api/produtos":
                if metodo == "GET":
                    return self._json(repo.listar_produtos())
                if metodo == "POST":
                    d = self._corpo()
                    pid = repo.criar_produto(d.get("nome", ""), float(d.get("quantidade", 1)),
                                             float(d.get("valor", 0)))
                    return self._json({"id": pid}, 201)

            if p == "/api/exemplos" and metodo == "POST":
                return self._json({"inseridos": carregar_exemplos(repo)})

            m = re.fullmatch(r"/api/produtos/(\d+)", p)
            if m and metodo == "GET":
                raiz = repo.carregar_arvore(int(m[1]))
                d = arvore_para_dict(raiz)
                d["texto"] = formatar_arvore(raiz)
                return self._json(d)

            m = re.fullmatch(r"/api/produtos/(\d+)/producao", p)
            if m and metodo == "GET":
                n = float(q.get("n", ["1"])[0].replace(",", "."))
                return self._json(necessidade(repo.carregar_arvore(int(m[1])), n))

            m = re.fullmatch(r"/api/produtos/(\d+)/implosao", p)
            if m and metodo == "POST":
                raiz = repo.carregar_arvore(int(m[1]))
                antes = raiz.valor
                total = implosao(raiz)
                repo.salvar_valores(raiz)
                return self._json({"valor_antes": antes, "valor_depois": raiz.valor,
                                   "custo_total": round(total, 2)})

            if p == "/api/componentes" and metodo == "POST":
                d = self._corpo()
                cid = repo.adicionar_componente(int(d["pai_id"]), d.get("nome", ""),
                                                float(d.get("quantidade", 1)),
                                                float(d.get("valor", 0)))
                return self._json({"id": cid}, 201)

            m = re.fullmatch(r"/api/componentes/(\d+)/valor", p)
            if m and metodo == "PUT":
                cid = int(m[1])
                raiz_id = repo.raiz_de(cid)
                antes = calcular_total(repo.carregar_arvore(raiz_id))
                repo.atualizar_valor(cid, float(self._corpo()["valor"]))
                depois = calcular_total(repo.carregar_arvore(raiz_id))
                return self._json({"custo_antes": antes, "custo_depois": depois})

            m = re.fullmatch(r"/api/componentes/(\d+)", p)
            if m and metodo == "PUT":
                d = self._corpo()
                repo.atualizar_componente(int(m[1]), d.get("nome", ""),
                                          float(d.get("quantidade", 1)), float(d.get("valor", 0)))
                return self._json({"ok": True})
            if m and metodo == "DELETE":
                repo.excluir(int(m[1]))
                return self._json({"ok": True})

            return self._json({"erro": "Rota não encontrada"}, 404)
        except (ValueError, KeyError, TypeError) as e:
            return self._json({"erro": str(e)}, 400)

    def do_GET(self):    self._rota("GET")
    def do_POST(self):   self._rota("POST")
    def do_PUT(self):    self._rota("PUT")
    def do_DELETE(self): self._rota("DELETE")


if __name__ == "__main__":
    servidor = HTTPServer(("localhost", PORTA), Handler)
    url = f"http://localhost:{PORTA}"
    print(f"Servidor rodando em {url}  (Ctrl+C para parar)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
