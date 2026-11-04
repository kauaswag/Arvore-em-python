"""
testes.py - Execução dos Testes 1 e 2 do enunciado (versão Python do main Java)
+ demonstração das demais funções (produção, atualização de valor e implosão).

Rodar:  python testes.py
"""
from arvore import (build_tree, print_tree, calcular_total, necessidade,
                    formatar_necessidade, atualizar_valor_por_nome, implosao)
from dados_exemplo import ITENS_CANETA, ITENS_PC


def teste1():
    print("=" * 60)
    print("TESTE 1")
    print("=" * 60)
    itens = ITENS_CANETA
    raiz = build_tree(itens)

    print("Árvore da fórmula da caneta:")
    print_tree(raiz, 0)

    total = calcular_total(raiz)
    print(f"\nValor total da caneta: R$ {total:.2f}")
    assert round(total, 2) == 2.50
    return raiz


def teste2():
    print("\n" + "=" * 60)
    print("TESTE 2")
    print("=" * 60)
    itens_pc = ITENS_PC
    raiz = build_tree(itens_pc)

    print("Árvore da fórmula do computador:")
    print_tree(raiz, 0)

    total = calcular_total(raiz)
    print(f"\nValor total do computador: R$ {total:.2f}")
    print(f"(valor cadastrado na raiz era R$ {raiz.valor:.2f}; "
          f"o total é recalculado a partir das peças)")
    assert round(total, 2) == 3380.00
    return raiz


def demonstracao(caneta, pc):
    print("\n" + "=" * 60)
    print("PRODUÇÃO (quantidade de componentes e valor de aquisição)")
    print("=" * 60)
    print(formatar_necessidade(necessidade(caneta, 100)))
    print()
    print(formatar_necessidade(necessidade(pc, 10)))

    print("\n" + "=" * 60)
    print("ATUALIZAÇÃO DE VALOR + IMPLOSÃO")
    print("=" * 60)
    print(f"Custo da caneta antes: R$ {calcular_total(caneta):.2f}")
    n = atualizar_valor_por_nome(caneta, "Pigmento", 0.45)
    print(f"Pigmento: R$ 0,30 -> R$ 0,45 ({n} componente atualizado)")
    novo = implosao(caneta)
    print("Árvore após implosão (custos remontados de baixo para cima):")
    print_tree(caneta)
    print(f"Novo custo da caneta: R$ {novo:.2f}")
    assert round(novo, 2) == 2.65
    assert caneta.filhos[0].valor == 0.95   # Tinta = 0,45 + 0,50

    print()
    novo_pc = implosao(pc)
    print("Implosão do computador (corrige valores de subconjuntos):")
    print_tree(pc)
    print(f"Custo do computador: R$ {novo_pc:.2f}")


if __name__ == "__main__":
    caneta = teste1()
    pc = teste2()
    demonstracao(caneta, pc)
    print("\nTodos os testes passaram ✔")
