"""
app_tkinter.py - Tela gráfica (desktop) do sistema de fórmulas de produto.

Rodar:  python app_tkinter.py
Dados gravados em formulas.db (SQLite).
"""
import tkinter as tk
from tkinter import ttk, messagebox

from arvore import (calcular_total, custo_unitario, necessidade,
                    formatar_arvore, implosao, fmt_qtd)
from banco import Repositorio
from dados_exemplo import carregar_exemplos


def moeda(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ler_numero(texto: str, campo: str) -> float:
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        raise ValueError(f"{campo} inválido(a): '{texto}'")


class FormComponente(tk.Toplevel):
    """Janela de formulário (nome, quantidade, valor)."""

    def __init__(self, master, titulo, nome="", qtd=1, valor=0.0, so_valor=False,
                 sem_qtd=False):
        super().__init__(master)
        self.title(titulo)
        self.resizable(False, False)
        self.resultado = None
        self.transient(master)

        frm = ttk.Frame(self, padding=14)
        frm.pack(fill="both")
        self.var_nome = tk.StringVar(value=nome)
        self.var_qtd = tk.StringVar(value="1" if sem_qtd else fmt_qtd(qtd))
        self.var_valor = tk.StringVar(value=f"{valor:.2f}")

        campos = [("Nome:", self.var_nome), ("Quantidade:", self.var_qtd),
                  ("Valor unitário (R$):", self.var_valor)]
        primeiro = None
        for i, (rot, var) in enumerate(campos):
            ttk.Label(frm, text=rot).grid(row=i, column=0, sticky="w", pady=4)
            e = ttk.Entry(frm, textvariable=var, width=30)
            e.grid(row=i, column=1, pady=4)
            if (so_valor and i < 2) or (sem_qtd and i == 1):
                e.state(["disabled"])
            elif primeiro is None:
                primeiro = e

        bts = ttk.Frame(frm)
        bts.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(bts, text="Salvar", command=self._ok).pack(side="left", padx=4)
        ttk.Button(bts, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        (primeiro or self).focus_set()
        self.wait_window()

    def _ok(self):
        try:
            nome = self.var_nome.get().strip()
            if not nome:
                raise ValueError("Informe o nome.")
            qtd = ler_numero(self.var_qtd.get(), "Quantidade")
            valor = ler_numero(self.var_valor.get(), "Valor")
            if qtd <= 0:
                raise ValueError("A quantidade deve ser maior que zero.")
            if valor < 0:
                raise ValueError("O valor não pode ser negativo.")
        except ValueError as e:
            messagebox.showerror("Dados inválidos", str(e), parent=self)
            return
        self.resultado = (nome, qtd, valor)
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fórmula de Produtos - Árvore Genérica")
        self.geometry("1200x640")
        self.minsize(900, 520)
        self.repo = Repositorio()
        if not self.repo.listar_produtos():
            carregar_exemplos(self.repo)

        self.produtos = []
        self.raiz = None

        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Treeview", rowheight=24)
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 13, "bold"))
        estilo.configure("Total.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1b5e20")

        self._montar_tela()
        self.carregar_produtos()

    # ------------------------------------------------------------ layout
    def _montar_tela(self):
        principal = ttk.PanedWindow(self, orient="horizontal")
        principal.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- lateral: produtos
        esq = ttk.Frame(principal, padding=6)
        principal.add(esq, weight=0)
        ttk.Label(esq, text="Produtos", style="Titulo.TLabel").pack(anchor="w")
        self.lst = tk.Listbox(esq, height=15, exportselection=False, font=("Segoe UI", 11))
        self.lst.pack(fill="both", expand=True, pady=6)
        self.lst.bind("<<ListboxSelect>>", lambda e: self.selecionar_produto())
        for txt, cmd in [("➕ Novo produto", self.novo_produto),
                         ("🗑 Excluir produto", self.excluir_produto),
                         ("📥 Carregar exemplos", self.exemplos)]:
            ttk.Button(esq, text=txt, command=cmd).pack(fill="x", pady=2)

        # ---- direita: árvore + ações
        dir_ = ttk.Frame(principal, padding=6)
        principal.add(dir_, weight=4)

        topo = ttk.Frame(dir_)
        topo.pack(fill="x")
        self.lbl_produto = ttk.Label(topo, text="Selecione um produto", style="Titulo.TLabel")
        self.lbl_produto.pack(side="left")
        self.lbl_total = ttk.Label(topo, text="", style="Total.TLabel")
        self.lbl_total.pack(side="right")

        colunas = ("tipo", "qtd", "valor", "unit", "total")
        self.tree = ttk.Treeview(dir_, columns=colunas, selectmode="browse")
        self.tree.heading("#0", text="Componente (explosão)")
        cab = {"tipo": "Tipo", "qtd": "Qtd", "valor": "Valor cadastrado",
               "unit": "Custo unitário", "total": "Custo total"}
        larg = {"tipo": 100, "qtd": 45, "valor": 125, "unit": 120, "total": 105}
        for c in colunas:
            self.tree.heading(c, text=cab[c])
            self.tree.column(c, width=larg[c], anchor="e" if c != "tipo" else "w")
        self.tree.column("#0", width=210)
        self.tree.tag_configure("diff", foreground="#b71c1c")
        sb = ttk.Scrollbar(dir_, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, pady=6)
        sb.pack(side="left", fill="y", pady=6)
        self.tree.bind("<Double-1>", lambda e: self.editar_componente())

        acoes = ttk.Frame(principal, padding=6)
        principal.add(acoes, weight=0)
        ttk.Label(acoes, text="Componente", style="Titulo.TLabel").pack(anchor="w")
        for txt, cmd in [("➕ Adicionar filho", self.adicionar_componente),
                         ("✏ Editar", self.editar_componente),
                         ("💲 Atualizar valor", self.atualizar_valor),
                         ("🗑 Remover", self.remover_componente)]:
            ttk.Button(acoes, text=txt, command=cmd).pack(fill="x", pady=2)

        ttk.Separator(acoes).pack(fill="x", pady=10)
        ttk.Label(acoes, text="Custos", style="Titulo.TLabel").pack(anchor="w")
        ttk.Button(acoes, text="🔁 Implosão (recalcular)",
                   command=self.fazer_implosao).pack(fill="x", pady=2)
        ttk.Button(acoes, text="🌳 Explosão em texto",
                   command=self.explosao_texto).pack(fill="x", pady=2)

        ttk.Separator(acoes).pack(fill="x", pady=10)
        ttk.Label(acoes, text="Produção", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(acoes, text="Quantidade a produzir:").pack(anchor="w", pady=(4, 0))
        self.var_n = tk.StringVar(value="1")
        ttk.Entry(acoes, textvariable=self.var_n).pack(fill="x", pady=2)
        ttk.Button(acoes, text="📦 Calcular produção",
                   command=self.calcular_producao).pack(fill="x", pady=2)

        ttk.Label(self, text="Vermelho = valor cadastrado diferente do custo calculado "
                             "(use Implosão para corrigir).  Duplo clique edita.",
                  foreground="#555").pack(anchor="w", padx=12, pady=(0, 6))

    # ------------------------------------------------------------ dados
    def carregar_produtos(self, selecionar_id=None):
        self.produtos = self.repo.listar_produtos()
        self.lst.delete(0, "end")
        for p in self.produtos:
            self.lst.insert("end", p["nome"])
        if not self.produtos:
            self.raiz = None
            self.atualizar_arvore()
            return
        idx = 0
        if selecionar_id is not None:
            idx = next((i for i, p in enumerate(self.produtos) if p["id"] == selecionar_id), 0)
        self.lst.selection_clear(0, "end")
        self.lst.selection_set(idx)
        self.selecionar_produto()

    def produto_atual_id(self):
        sel = self.lst.curselection()
        return self.produtos[sel[0]]["id"] if sel else None

    def selecionar_produto(self):
        pid = self.produto_atual_id()
        self.raiz = self.repo.carregar_arvore(pid) if pid else None
        self.atualizar_arvore()

    def recarregar(self, manter_sel=None):
        self.raiz = self.repo.carregar_arvore(self.raiz.id)
        self.atualizar_arvore(manter_sel)

    def atualizar_arvore(self, selecionar=None):
        self.tree.delete(*self.tree.get_children())
        if not self.raiz:
            self.lbl_produto.config(text="Nenhum produto")
            self.lbl_total.config(text="")
            return

        def inserir(no, pai_iid="", nivel=0):
            unit = custo_unitario(no)
            tipo = "Produto" if nivel == 0 else ("Matéria-prima" if no.eh_folha() else "Subconjunto")
            tags = ("diff",) if abs(unit - no.valor) > 0.005 else ()
            iid = str(no.id)
            self.tree.insert(pai_iid, "end", iid=iid, text=no.nome, open=True, tags=tags,
                             values=(tipo, "1" if nivel == 0 else fmt_qtd(no.quantidade), moeda(no.valor),
                                     moeda(unit), moeda(calcular_total(no))))
            for f in no.filhos:
                inserir(f, iid, nivel + 1)

        inserir(self.raiz)
        self.lbl_produto.config(text=f"Fórmula: {self.raiz.nome}")
        self.lbl_total.config(text=f"Custo total: {moeda(calcular_total(self.raiz))}")
        if selecionar and self.tree.exists(str(selecionar)):
            self.tree.selection_set(str(selecionar))
            self.tree.see(str(selecionar))

    def componente_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Atenção", "Selecione um componente na árvore.")
            return None
        return self.raiz.buscar_por_id(int(sel[0]))

    # ------------------------------------------------------------ CRUD produto
    def novo_produto(self):
        f = FormComponente(self, "Novo produto", nome="", qtd=1, valor=0, sem_qtd=True)
        if f.resultado:
            nome, qtd, valor = f.resultado
            pid = self.repo.criar_produto(nome, qtd, valor)
            self.carregar_produtos(pid)
            messagebox.showinfo("Produto criado",
                                f"'{nome}' criado. Agora adicione os componentes "
                                "com 'Adicionar filho'.")

    def excluir_produto(self):
        pid = self.produto_atual_id()
        if pid and messagebox.askyesno("Confirmar",
                                       f"Excluir '{self.raiz.nome}' e toda a sua fórmula?"):
            self.repo.excluir(pid)
            self.carregar_produtos()

    def exemplos(self):
        ins = carregar_exemplos(self.repo)
        self.carregar_produtos()
        messagebox.showinfo("Exemplos", "Inseridos: " + ", ".join(ins) if ins
                            else "Os exemplos (Caneta e Computador) já estão cadastrados.")

    # ------------------------------------------------------------ CRUD componente
    def adicionar_componente(self):
        if not self.raiz:
            return
        pai = self.componente_selecionado()
        if not pai:
            return
        f = FormComponente(self, f"Novo componente de '{pai.nome}'")
        if f.resultado:
            nid = self.repo.adicionar_componente(pai.id, *f.resultado)
            self.recarregar(nid)

    def editar_componente(self):
        no = self.componente_selecionado() if self.raiz else None
        if not no:
            return
        f = FormComponente(self, f"Editar '{no.nome}'", no.nome, no.quantidade, no.valor,
                           sem_qtd=no.pai is None)
        if f.resultado:
            self.repo.atualizar_componente(no.id, *f.resultado)
            self.recarregar(no.id)

    def atualizar_valor(self):
        no = self.componente_selecionado() if self.raiz else None
        if not no:
            return
        antes = calcular_total(self.raiz)
        f = FormComponente(self, f"Atualizar valor de '{no.nome}'",
                           no.nome, no.quantidade, no.valor, so_valor=True)
        if f.resultado:
            self.repo.atualizar_valor(no.id, f.resultado[2])
            self.recarregar(no.id)
            if messagebox.askyesno(
                    "Valor atualizado",
                    f"Novo valor de {no.nome}: {moeda(f.resultado[2])}\n"
                    f"Custo calculado: {moeda(antes)} -> {moeda(calcular_total(self.raiz))}\n\n"
                    "Deseja fazer a IMPLOSÃO agora (remontar o custo dos níveis acima)?"):
                self.fazer_implosao()

    def remover_componente(self):
        no = self.componente_selecionado() if self.raiz else None
        if not no:
            return
        if no.id == self.raiz.id:
            return self.excluir_produto()
        if messagebox.askyesno("Confirmar", f"Remover '{no.nome}' e seus subcomponentes?"):
            self.repo.excluir(no.id)
            self.recarregar()

    # ------------------------------------------------------------ custos
    def fazer_implosao(self):
        if not self.raiz:
            return
        antes = self.raiz.valor
        total = implosao(self.raiz)
        self.repo.salvar_valores(self.raiz)
        self.recarregar()
        messagebox.showinfo("Implosão concluída",
                            f"Custos remontados de baixo para cima.\n\n"
                            f"Valor de {self.raiz.nome}: {moeda(antes)} -> {moeda(self.raiz.valor)}\n"
                            f"Custo total: {moeda(total)}")

    def explosao_texto(self):
        if self.raiz:
            texto = formatar_arvore(self.raiz) + \
                    f"\n\nValor total: {moeda(calcular_total(self.raiz))}"
            self._janela_texto(f"Explosão - {self.raiz.nome}", texto)

    def calcular_producao(self):
        if not self.raiz:
            return
        try:
            n = ler_numero(self.var_n.get(), "Quantidade")
            r = necessidade(self.raiz, n)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return
        self._janela_producao(r)

    def _janela_producao(self, r):
        w = tk.Toplevel(self)
        w.title(f"Produção de {fmt_qtd(r['quantidade_produto'])} x {r['produto']}")
        w.geometry("560x420")
        ttk.Label(w, text=f"Para produzir {fmt_qtd(r['quantidade_produto'])} "
                          f"{r['produto']}(s), é preciso comprar:",
                  style="Titulo.TLabel").pack(anchor="w", padx=10, pady=8)
        tv = ttk.Treeview(w, columns=("nome", "qtd", "unit", "valor"), show="headings")
        tv.heading("nome", text="Componente")
        for c, t in [("qtd", "Quantidade"), ("unit", "Valor unit."), ("valor", "Valor aquisição")]:
            tv.heading(c, text=t)
            tv.column(c, anchor="e", width=110)
        tv.column("nome", width=180)
        for i in r["itens"]:
            tv.insert("", "end", values=(i["nome"], fmt_qtd(i["quantidade"]),
                                         moeda(i["valor_medio"]), moeda(i["valor"])))
        tv.pack(fill="both", expand=True, padx=10)
        ttk.Label(w, text=f"Total de componentes: {fmt_qtd(r['total_componentes'])}     "
                          f"Valor de aquisição: {moeda(r['valor_aquisicao'])}",
                  style="Total.TLabel").pack(anchor="e", padx=10, pady=10)

    def _janela_texto(self, titulo, texto):
        w = tk.Toplevel(self)
        w.title(titulo)
        w.geometry("620x480")
        t = tk.Text(w, font=("Consolas", 11), wrap="none")
        t.insert("1.0", texto)
        t.config(state="disabled")
        t.pack(fill="both", expand=True, padx=8, pady=8)


if __name__ == "__main__":
    App().mainloop()
