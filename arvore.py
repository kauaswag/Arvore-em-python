"""
arvore.py - Núcleo do sistema: Árvore Genérica de fórmula de produto.

Cada nó (TreeNode) pode ter N filhos (árvore genérica / n-ária).
- Nó raiz   = o produto final (ex.: Caneta)
- Nós internos = subconjuntos (ex.: Tinta, Corpo, Tampa)
- Folhas    = matérias-primas compradas (ex.: Pigmento, Solvente)

Operações principais:
- build_tree       -> monta a árvore a partir de uma lista de ItemFormula
- print_tree       -> imprime a árvore (explosão)
- calcular_total   -> custo total calculado a partir das folhas
- explosao         -> lista detalhada de todos os itens (com qtd acumulada)
- necessidade      -> qtd de componentes e valor de aquisição para N produtos
- atualizar_valor  -> altera o preço de um componente
- implosao         -> recalcula (de baixo para cima) o custo de cada nível
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class ItemFormula:
    """Equivalente à classe ItemFormula do enunciado (Java)."""
    nome: str
    pai: Optional[str]      # nome do item pai (None = raiz / produto)
    quantidade: float       # quantidade usada dentro do pai
    valor: float            # valor unitário cadastrado


class TreeNode:
    """Nó da árvore genérica. Guarda uma lista com qualquer número de filhos."""

    def __init__(self, nome: str, quantidade: float = 1, valor: float = 0.0,
                 id: Optional[int] = None):
        self.id = id
        self.nome = nome
        self.quantidade = quantidade
        self.valor = valor
        self.filhos: list[TreeNode] = []
        self.pai: Optional[TreeNode] = None

    # ---------- operações de árvore genérica ----------
    def adicionar_filho(self, filho: "TreeNode") -> "TreeNode":
        filho.pai = self
        self.filhos.append(filho)
        return filho

    def remover_filho(self, filho: "TreeNode") -> None:
        self.filhos.remove(filho)
        filho.pai = None

    def eh_folha(self) -> bool:
        return len(self.filhos) == 0

    def percorrer(self, nivel: int = 0) -> Iterator[tuple["TreeNode", int]]:
        """Percurso em pré-ordem: (nó, nível)."""
        yield self, nivel
        for f in self.filhos:
            yield from f.percorrer(nivel + 1)

    def buscar_por_id(self, id: int) -> Optional["TreeNode"]:
        for no, _ in self.percorrer():
            if no.id == id:
                return no
        return None

    def buscar_por_nome(self, nome: str) -> list["TreeNode"]:
        alvo = nome.strip().lower()
        return [no for no, _ in self.percorrer() if no.nome.lower() == alvo]

    def __repr__(self) -> str:
        return f"TreeNode({self.nome!r}, qtd={self.quantidade}, valor={self.valor})"


# Montagem e impressão
def build_tree(itens: list[ItemFormula]) -> TreeNode:
    """Monta a árvore. O pai é procurado pelo nome do último nó criado com
    aquele nome (permite nomes repetidos em ramos diferentes, ex.: Plástico)."""
    raiz: Optional[TreeNode] = None
    ultimo_por_nome: dict[str, TreeNode] = {}

    for item in itens:
        no = TreeNode(item.nome, item.quantidade, item.valor)
        if item.pai is None:
            if raiz is not None:
                raise ValueError("A fórmula só pode ter um produto raiz.")
            raiz = no
        else:
            pai = ultimo_por_nome.get(item.pai)
            if pai is None:
                raise ValueError(f"Pai '{item.pai}' de '{item.nome}' não encontrado "
                                 f"(cadastre o pai antes dos filhos).")
            pai.adicionar_filho(no)
        ultimo_por_nome[item.nome] = no

    if raiz is None:
        raise ValueError("Nenhum produto raiz informado (pai = None).")
    return raiz


def formatar_arvore(no: TreeNode, nivel: int = 0) -> str:
    linhas = []
    for n, nv in no.percorrer(nivel):
        prefixo = "    " * nv + ("└── " if nv > 0 else "")
        linhas.append(f"{prefixo}{n.nome} (Qtd: {fmt_qtd(n.quantidade)}, "
                      f"Valor: R$ {n.valor:.2f})")
    return "\n".join(linhas)


def print_tree(no: TreeNode, nivel: int = 0) -> None:
    print(formatar_arvore(no, nivel))


# Custos

def custo_unitario(no: TreeNode) -> float:
    """Custo de UMA unidade do nó.
    - folha: o próprio valor (preço de compra)
    - nó interno: soma do custo dos filhos (cada filho x sua quantidade)"""
    if no.eh_folha():
        return no.valor
    return sum(calcular_total(f) for f in no.filhos)


def calcular_total(no: TreeNode) -> float:
    """Custo do nó considerando a quantidade dele no pai (recursivo).
    O produto (raiz, sem pai) não está dentro de ninguém: o total dele é o
    custo de 1 unidade, e a quantidade da raiz é ignorada."""
    if no.pai is None:
        return custo_unitario(no)
    return no.quantidade * custo_unitario(no)



# Explosão: detalhes do produto
def explosao(raiz: TreeNode, quantidade_produto: float = 1) -> list[dict]:
    """Lista todos os itens da fórmula com nível, qtd acumulada e custo."""
    linhas: list[dict] = []

    def visitar(no: TreeNode, nivel: int, multiplicador: float):
        qtd_total = multiplicador * (no.quantidade if nivel > 0 else 1)
        linhas.append({
            "id": no.id,
            "nivel": nivel,
            "nome": no.nome,
            "tipo": "Matéria-prima" if no.eh_folha() else ("Produto" if nivel == 0 else "Subconjunto"),
            "qtd_no_pai": no.quantidade,
            "qtd_total": qtd_total,
            "valor_cadastrado": no.valor,
            "custo_unitario": custo_unitario(no),
            "custo_total": qtd_total * custo_unitario(no),
        })
        for f in no.filhos:
            visitar(f, nivel + 1, qtd_total)

    visitar(raiz, 0, quantidade_produto)
    return linhas


# Produção: quantidade de componentes e valor de aquisição
def necessidade(raiz: TreeNode, quantidade_produto: float) -> dict:
    """Para produzir N produtos: quanto comprar de cada matéria-prima (folha)
    e quanto isso custa. Folhas com o mesmo nome são somadas."""
    if quantidade_produto <= 0:
        raise ValueError("A quantidade a produzir deve ser maior que zero.")

    compras: dict[str, dict] = {}
    for linha in explosao(raiz, quantidade_produto):
        if linha["tipo"] != "Matéria-prima" or linha["nivel"] == 0:
            continue
        item = compras.setdefault(linha["nome"], {"nome": linha["nome"],
                                                  "quantidade": 0.0, "valor": 0.0})
        item["quantidade"] += linha["qtd_total"]
        item["valor"] += linha["custo_total"]

    itens = list(compras.values())
    for i in itens:
        i["valor_medio"] = i["valor"] / i["quantidade"] if i["quantidade"] else 0
    return {
        "produto": raiz.nome,
        "quantidade_produto": quantidade_produto,
        "itens": itens,
        "total_componentes": sum(i["quantidade"] for i in itens),
        "valor_aquisicao": sum(i["valor"] for i in itens),
        "custo_unitario": custo_unitario(raiz),
    }


def formatar_necessidade(r: dict) -> str:
    linhas = [f"Produção de {fmt_qtd(r['quantidade_produto'])} x {r['produto']}",
              "-" * 52,
              f"{'Componente':<24}{'Quantidade':>12}{'Valor (R$)':>16}"]
    for i in r["itens"]:
        linhas.append(f"{i['nome']:<24}{fmt_qtd(i['quantidade']):>12}{i['valor']:>16.2f}")
    linhas += ["-" * 52,
               f"{'TOTAL':<24}{fmt_qtd(r['total_componentes']):>12}{r['valor_aquisicao']:>16.2f}"]
    return "\n".join(linhas)


# Atualização de valor e Implosão
def atualizar_valor(no: TreeNode, novo_valor: float) -> None:
    if novo_valor < 0:
        raise ValueError("O valor não pode ser negativo.")
    no.valor = novo_valor


def atualizar_valor_por_nome(raiz: TreeNode, nome: str, novo_valor: float) -> int:
    """Atualiza todos os componentes com o nome informado. Retorna quantos mudaram."""
    nos = raiz.buscar_por_nome(nome)
    for no in nos:
        atualizar_valor(no, novo_valor)
    return len(nos)


def implosao(raiz: TreeNode) -> float:
    """Remonta o custo de baixo para cima (pós-ordem): cada nó interno passa a
    valer a soma dos custos dos filhos. Retorna o novo custo total do produto."""
    def visitar(no: TreeNode):
        for f in no.filhos:
            visitar(f)
        if not no.eh_folha():
            no.valor = round(custo_unitario(no), 2)

    visitar(raiz)
    return calcular_total(raiz)


# Utilidades
def fmt_qtd(q: float) -> str:
    return str(int(q)) if float(q).is_integer() else f"{q:.2f}"


def arvore_para_dict(no: TreeNode) -> dict:
    """Serializa a árvore (usado pela API web)."""
    return {
        "id": no.id,
        "nome": no.nome,
        "quantidade": no.quantidade,
        "valor": no.valor,
        "custo_unitario": round(custo_unitario(no), 2),
        "custo_total": round(calcular_total(no), 2),
        "folha": no.eh_folha(),
        "filhos": [arvore_para_dict(f) for f in no.filhos],
    }
