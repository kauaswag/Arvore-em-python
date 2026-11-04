"""dados_exemplo.py - Fórmulas dos Testes 1 (Caneta) e 2 (Computador)."""
from arvore import ItemFormula

ITENS_CANETA = [
    ItemFormula("Caneta", None, 1, 2.50),
    ItemFormula("Tinta", "Caneta", 1, 0.80),
    ItemFormula("Pigmento", "Tinta", 1, 0.30),
    ItemFormula("Solvente", "Tinta", 1, 0.50),
    ItemFormula("Corpo", "Caneta", 1, 1.00),
    ItemFormula("Plástico", "Corpo", 1, 0.70),
    ItemFormula("Clip", "Corpo", 1, 0.30),
    ItemFormula("Tampa", "Caneta", 1, 0.70),
    ItemFormula("Plástico", "Tampa", 1, 0.50),
    ItemFormula("Vedação", "Tampa", 1, 0.20),
]

ITENS_PC = [
    ItemFormula("Computador", None, 1, 2500.00),

    ItemFormula("Gabinete", "Computador", 1, 800.00),
    ItemFormula("Placa-Mãe", "Gabinete", 1, 500.00),
    ItemFormula("CPU", "Placa-Mãe", 1, 1000.00),
    ItemFormula("Memória RAM", "Placa-Mãe", 2, 200.00),
    ItemFormula("Chipset", "Placa-Mãe", 1, 150.00),
    ItemFormula("Fonte de Alimentação", "Gabinete", 1, 300.00),
    ItemFormula("Armazenamento", "Gabinete", 1, 0.00),
    ItemFormula("HDD", "Armazenamento", 1, 250.00),
    ItemFormula("SSD", "Armazenamento", 1, 400.00),

    ItemFormula("Monitor", "Computador", 1, 900.00),
    ItemFormula("Tela LCD", "Monitor", 1, 600.00),
    ItemFormula("Carcaça", "Monitor", 1, 100.00),

    ItemFormula("Periféricos", "Computador", 1, 0.00),
    ItemFormula("Teclado", "Periféricos", 1, 100.00),
    ItemFormula("Mouse", "Periféricos", 1, 80.00),
]

EXEMPLOS = {"Caneta": ITENS_CANETA, "Computador": ITENS_PC}


def carregar_exemplos(repo) -> list[str]:
    """Grava no banco os exemplos que ainda não existem. Retorna os inseridos."""
    inseridos = []
    for nome, itens in EXEMPLOS.items():
        if not repo.existe_produto(nome):
            repo.importar_itens(itens)
            inseridos.append(nome)
    return inseridos
