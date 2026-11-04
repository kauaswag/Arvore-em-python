"""
banco.py - Persistência em banco de dados SQLite (já vem com o Python).

Tabela única e auto-relacionada:
    componente(id, pai_id, nome, quantidade, valor)
- pai_id NULL  -> é um PRODUTO (raiz da árvore)
- pai_id = X   -> é filho do componente X
Excluir um nó apaga todos os descendentes (ON DELETE CASCADE).
"""
from __future__ import annotations

import os
import sqlite3
from typing import Optional

from arvore import TreeNode, ItemFormula, build_tree

CAMINHO_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "formulas.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS componente (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pai_id      INTEGER REFERENCES componente(id) ON DELETE CASCADE,
    nome        TEXT    NOT NULL,
    quantidade  REAL    NOT NULL DEFAULT 1 CHECK (quantidade > 0),
    valor       REAL    NOT NULL DEFAULT 0 CHECK (valor >= 0)
);
CREATE INDEX IF NOT EXISTS idx_componente_pai ON componente(pai_id);
"""


class Repositorio:
    def __init__(self, caminho: str = CAMINHO_PADRAO):
        self.conn = sqlite3.connect(caminho, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def criar_produto(self, nome: str, quantidade: float = 1, valor: float = 0) -> int:
        return self._inserir(None, nome, quantidade, valor)

    def adicionar_componente(self, pai_id: int, nome: str, quantidade: float, valor: float) -> int:
        if self._buscar(pai_id) is None:
            raise ValueError("Componente pai não existe.")
        return self._inserir(pai_id, nome, quantidade, valor)

    def salvar_arvore(self, raiz: TreeNode, pai_id: Optional[int] = None) -> int:
        """Grava uma árvore inteira (em memória) no banco. Retorna id da raiz."""
        raiz.id = self._inserir(pai_id, raiz.nome, raiz.quantidade, raiz.valor, commit=False)
        for f in raiz.filhos:
            self.salvar_arvore(f, raiz.id)
        if pai_id is None:
            self.conn.commit()
        return raiz.id

    def importar_itens(self, itens: list[ItemFormula]) -> int:
        return self.salvar_arvore(build_tree(itens))

    def listar_produtos(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM componente WHERE pai_id IS NULL ORDER BY nome").fetchall()
        return [dict(r) for r in rows]

    def existe_produto(self, nome: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM componente WHERE pai_id IS NULL AND lower(nome)=lower(?)",
            (nome,)).fetchone() is not None

    def carregar_arvore(self, raiz_id: int) -> TreeNode:
        """Lê a subárvore com uma consulta recursiva (WITH RECURSIVE)."""
        rows = self.conn.execute("""
            WITH RECURSIVE sub(id) AS (
                SELECT id FROM componente WHERE id = ?
                UNION ALL
                SELECT c.id FROM componente c JOIN sub s ON c.pai_id = s.id
            )
            SELECT c.* FROM componente c JOIN sub USING(id) ORDER BY c.id
        """, (raiz_id,)).fetchall()
        if not rows:
            raise ValueError("Produto não encontrado.")

        nos = {r["id"]: TreeNode(r["nome"], r["quantidade"], r["valor"], r["id"]) for r in rows}
        raiz = nos[raiz_id]
        for r in rows:
            if r["id"] != raiz_id:
                nos[r["pai_id"]].adicionar_filho(nos[r["id"]])
        return raiz

    def raiz_de(self, id: int) -> int:
        """Descobre o produto (raiz) a que um componente pertence."""
        atual = self._buscar(id)
        while atual and atual["pai_id"] is not None:
            atual = self._buscar(atual["pai_id"])
        if atual is None:
            raise ValueError("Componente não encontrado.")
        return atual["id"]

    def atualizar_componente(self, id: int, nome: str, quantidade: float, valor: float) -> None:
        self._validar(nome, quantidade, valor)
        cur = self.conn.execute(
            "UPDATE componente SET nome=?, quantidade=?, valor=? WHERE id=?",
            (nome.strip(), quantidade, valor, id))
        self.conn.commit()
        if cur.rowcount == 0:
            raise ValueError("Componente não encontrado.")

    def atualizar_valor(self, id: int, valor: float) -> None:
        if valor < 0:
            raise ValueError("O valor não pode ser negativo.")
        cur = self.conn.execute("UPDATE componente SET valor=? WHERE id=?", (valor, id))
        self.conn.commit()
        if cur.rowcount == 0:
            raise ValueError("Componente não encontrado.")

    def salvar_valores(self, raiz: TreeNode) -> None:
        """Grava o valor de todos os nós (usado após a implosão)."""
        self.conn.executemany("UPDATE componente SET valor=? WHERE id=?",
                              [(no.valor, no.id) for no, _ in raiz.percorrer()])
        self.conn.commit()

    def excluir(self, id: int) -> None:
        """Exclui o componente/produto e todos os seus descendentes."""
        self.conn.execute("DELETE FROM componente WHERE id=?", (id,))
        self.conn.commit()

    def _buscar(self, id: int):
        return self.conn.execute("SELECT * FROM componente WHERE id=?", (id,)).fetchone()

    @staticmethod
    def _validar(nome: str, quantidade: float, valor: float) -> None:
        if not nome or not nome.strip():
            raise ValueError("Informe o nome.")
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        if valor < 0:
            raise ValueError("O valor não pode ser negativo.")

    def _inserir(self, pai_id, nome, quantidade, valor, commit=True) -> int:
        self._validar(nome, quantidade, valor)
        cur = self.conn.execute(
            "INSERT INTO componente (pai_id, nome, quantidade, valor) VALUES (?,?,?,?)",
            (pai_id, nome.strip(), quantidade, valor))
        if commit:
            self.conn.commit()
        return cur.lastrowid
