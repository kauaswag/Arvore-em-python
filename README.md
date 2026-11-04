# Sistema de Fórmula de Produtos — Árvore Genérica (Python)

O sistema cadastra a fórmula (estrutura) de produtos usando uma **árvore genérica**: cada nó pode ter qualquer número de filhos.
Funções do sistema:

| Requisito | Onde está |
|---|---|
| Cadastrar a fórmula de um produto (CRUD) | `banco.py` + telas (Tkinter e HTML) |
| Exibir detalhes do produto (**explosão**) | `explosao()`, `print_tree()` em `arvore.py` |
| Informar qtd a produzir → qtd de componentes e valor de aquisição | `necessidade()` em `arvore.py` |
| Atualizar o valor de um componente | `atualizar_valor()` / `Repositorio.atualizar_valor()` |
| Remontar o custo após atualização (**implosão**) | `implosao()` em `arvore.py` |
| Testes 1 e 2 | `testes.py` |
| Tela gráfica | `app_tkinter.py` |
| Front-end em HTML (avançado) | `app_web.py` + `web/index.html` |
| Persistência em banco de dados (avançado) | `banco.py` (SQLite → `formulas.db`) |

Nenhuma biblioteca externa é necessária, só o Python 3.10+.

## Como executar

```bash
python testes.py         # Teste 1 (caneta) e Teste 2 (computador)
python app_tkinter.py    # Tela gráfica desktop
python app_web.py        # Front-end HTML -> abre http://localhost:8000
```

No Windows, dá para usar dois cliques em `iniciar.bat`: ele liga o servidor e abre o navegador.
Se o servidor já estiver ligado, abrir `web/index.html` direto leva automaticamente para `http://localhost:8000`.

> As duas telas usam o **mesmo banco** (`formulas.db`, criado automaticamente).
> Na primeira execução, Caneta e Computador já são cadastrados como exemplo.
> Para começar do zero, apague o arquivo `formulas.db`.
> No Linux, se faltar o Tkinter: `sudo apt install python3-tk`.

## Estrutura

```
arvore.py          núcleo: ItemFormula, TreeNode, build_tree, print_tree,
                   calcular_total, explosao, necessidade, atualizar_valor, implosao
banco.py           persistência SQLite (CRUD + consulta recursiva WITH RECURSIVE)
dados_exemplo.py   fórmulas dos testes 1 e 2
testes.py          execução dos testes do enunciado
app_tkinter.py     tela gráfica (Tkinter)
app_web.py         servidor HTTP + API REST (http.server)
web/index.html     front-end HTML/CSS/JavaScript
```

## Regras de cálculo

- **Folha** (matéria-prima): custo = valor de compra.
- **Nó interno** (subconjunto/produto): custo = soma de (custo do filho × quantidade do filho).
- **Explosão**: percorre a árvore de cima para baixo (pré-ordem) mostrando cada nível.
- **Implosão**: percorre de baixo para cima (pós-ordem) e grava em cada nó interno o custo somado dos filhos.
- **Produção de N unidades**: a quantidade de cada folha é multiplicada pelas quantidades de todos os níveis acima e por N. Folhas com o mesmo nome (ex.: Plástico do Corpo e da Tampa) são somadas.

## Resultados esperados

- Teste 1: valor total da caneta **R$ 2,50**
- Teste 2: valor total do computador **R$ 3.380,00**

No Teste 2, o valor cadastrado no Computador é R$ 2.500,00 e o de alguns subconjuntos também não bate com a soma das peças (Placa-Mãe: 500 cadastrado × 1.550 calculado).
O total é calculado a partir das peças, e a **implosão** corrige esses valores. Na tela, essas linhas aparecem em vermelho.

Observação: no `main` Java do Teste 2, a lista se chama `itensPC`, mas é chamado `buildTree(itens)`, e a mensagem final diz "caneta". Na versão Python isso foi corrigido.

## Banco de dados

Uma tabela auto-relacionada (cada componente aponta para o pai):

```sql
CREATE TABLE componente (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    pai_id     INTEGER REFERENCES componente(id) ON DELETE CASCADE,  -- NULL = produto
    nome       TEXT NOT NULL,
    quantidade REAL NOT NULL DEFAULT 1 CHECK (quantidade > 0),
    valor      REAL NOT NULL DEFAULT 0 CHECK (valor >= 0)
);
```

A árvore inteira de um produto é carregada com uma consulta `WITH RECURSIVE`.
