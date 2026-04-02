import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import subprocess
from collections import defaultdict
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfgen import canvas
import pandas as pd

ARQUIVO = "vendas.csv"

def inicializar_arquivo():
    if not os.path.exists(ARQUIVO):
        with open(ARQUIVO, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Cliente", "Tamanho", "Quantidade", "Valor Unitário", 
                             "Forma de Pagamento", "Recebedor", "Valor Total"])

def carregar_vendas(filtro=""):
    tabela.delete(*tabela.get_children())
    tabela_tamanhos.delete(*tabela_tamanhos.get_children())
    qtd_total = 0
    valor_total_geral = 0
    qtd_por_tamanho = defaultdict(int)

    with open(ARQUIVO, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (filtro.lower() in row["Cliente"].lower() or 
                filtro.lower() in row["Tamanho"].lower() or 
                filtro.lower() in row["Forma de Pagamento"].lower() or
                filtro.lower() in row["Recebedor"].lower()):
                qtd = int(row["Quantidade"])
                valor_total = float(row["Valor Total"])
                qtd_total += qtd
                valor_total_geral += valor_total
                qtd_por_tamanho[row["Tamanho"]] += qtd
                tabela.insert("", tk.END, values=(
                    row["Cliente"], row["Tamanho"], row["Quantidade"], 
                    f"{float(row['Valor Unitário']):.2f}", 
                    row["Forma de Pagamento"], row["Recebedor"], 
                    f"{valor_total:.2f}"
                ))

    for tam, qtd in qtd_por_tamanho.items():
        tabela_tamanhos.insert("", tk.END, values=(tam, qtd))
    label_totais.config(text=f"Qtd total de itens: {qtd_total} | Valor total geral: R$ {valor_total_geral:.2f}")

def registrar_venda():
    try:
        venda = coletar_dados_venda()
        with open(ARQUIVO, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(venda)
        messagebox.showinfo("Sucesso", "Venda registrada com sucesso!")
        limpar_campos()
        carregar_vendas()
    except ValueError:
        messagebox.showerror("Erro", "Verifique os valores digitados!")

def coletar_dados_venda():
    nome_cliente = entry_nome.get()
    tamanho = entry_tamanho.get()
    quantidade = int(entry_quantidade.get())
    valor_unitario = float(entry_valor.get())
    forma_pagamento = entry_pagamento.get()
    recebedor = entry_recebedor.get()
    valor_total = quantidade * valor_unitario
    return [nome_cliente, tamanho, quantidade, valor_unitario, forma_pagamento, recebedor, valor_total]

def limpar_campos():
    entry_nome.delete(0, tk.END)
    entry_tamanho.delete(0, tk.END)
    entry_quantidade.delete(0, tk.END)
    entry_valor.delete(0, tk.END)
    entry_pagamento.delete(0, tk.END)
    entry_recebedor.delete(0, tk.END)

def selecionar_venda(event):
    item = tabela.selection()
    if item:
        valores = tabela.item(item)["values"]
        for entry, valor in zip([entry_nome, entry_tamanho, entry_quantidade, entry_valor, entry_pagamento, entry_recebedor], valores):
            entry.delete(0, tk.END)
            entry.insert(0, valor)

def salvar_edicao():
    item = tabela.selection()
    if not item:
        messagebox.showwarning("Aviso", "Selecione uma venda para editar.")
        return
    try:
        venda = coletar_dados_venda()
        with open(ARQUIVO, "r", newline="", encoding="utf-8") as f:
            linhas = list(csv.reader(f))
        indice = tabela.index(item)
        linhas[indice + 1] = venda
        with open(ARQUIVO, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(linhas)
        messagebox.showinfo("Sucesso", "Venda editada com sucesso!")
        carregar_vendas()
        limpar_campos()
    except ValueError:
        messagebox.showerror("Erro", "Verifique os valores digitados!")

def excluir_venda():
    item = tabela.selection()
    if not item:
        messagebox.showwarning("Aviso", "Selecione uma venda para excluir.")
        return
    if messagebox.askyesno("Confirmação", "Deseja realmente excluir esta venda?"):
        indice = tabela.index(item)
        with open(ARQUIVO, "r", newline="", encoding="utf-8") as f:
            linhas = list(csv.reader(f))
        del linhas[indice + 1]
        with open(ARQUIVO, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(linhas)
        messagebox.showinfo("Sucesso", "Venda excluída com sucesso!")
        carregar_vendas()
        limpar_campos()

def aplicar_filtro():
    filtro = entry_filtro.get()
    carregar_vendas(filtro)

def gerar_relatorio():
    relatorio_window = tk.Toplevel(root)
    relatorio_window.title("Relatório Completo de Vendas")
    relatorio_tabela = ttk.Treeview(relatorio_window, columns=("Cliente", "Tamanho", "Quantidade", 
                                                                "Valor Unitário", "Forma de Pagamento", 
                                                                "Recebedor", "Valor Total"), show="headings")
    for col in relatorio_tabela["columns"]:
        relatorio_tabela.heading(col, text=col)
        relatorio_tabela.column(col, width=120)
    relatorio_tabela.pack(fill=tk.BOTH, expand=True)
    with open(ARQUIVO, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            relatorio_tabela.insert("", tk.END, values=(
                row["Cliente"], row["Tamanho"], row["Quantidade"],
                f"{float(row['Valor Unitário']):.2f}", 
                row["Forma de Pagamento"], row["Recebedor"], 
                f"{row['Valor Total']}"
            ))
    tk.Button(relatorio_window, text="Imprimir em PDF", command=imprimir_relatorio_pdf).pack(pady=5)
    tk.Button(relatorio_window, text="Exportar para Excel", command=gerar_planilha_excel).pack(pady=5)

def imprimir_relatorio_pdf():
    arquivo_pdf = "relatorio_vendas.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=landscape(A4))
    largura, altura = landscape(A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, altura - 50, "Relatório de Vendas")

    cabecalho = ["Cliente", "Tamanho", "Quantidade", "Valor Unitário", "Forma de Pagamento", "Recebedor", "Valor Total"]
    larguras = [150, 100, 100, 100, 90, 100, 100]
    x = 50
    y = altura - 100
    c.setFont("Helvetica-Bold", 12)
    for i, col in enumerate(cabecalho):
        c.drawString(x, y, col)
        x += larguras[i]
    c.line(50, y-5, largura-50, y-5)

    qtd_total = 0
    valor_total_geral = 0
    c.setFont("Helvetica", 10)
    y -= 20
    with open(ARQUIVO, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x = 50
            valores = [
                row["Cliente"], row["Tamanho"], row["Quantidade"],
                f"{float(row['Valor Unitário']):.2f}",
                row["Forma de Pagamento"], row["Recebedor"],
                f"{row['Valor Total']}"
            ]
            qtd_total += int(row["Quantidade"])
            valor_total_geral += float(row["Valor Total"])
            for valor, largura_col in zip(valores, larguras):
                c.drawString(x, y, str(valor))
                x += largura_col
            c.line(50, y-5, largura-50, y-5)
            y -= 20
            if y < 50:
                c.showPage()
                y = altura - 50

        c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y-30, f"Total de itens: {qtd_total}")
    c.drawString(250, y-30, f"Valor total geral: R$ {valor_total_geral:.2f}")

    c.save()
    messagebox.showinfo("Sucesso", f"Relatório gerado: {arquivo_pdf}")
    subprocess.Popen([arquivo_pdf], shell=True)

def gerar_planilha_excel():
    df = pd.read_csv(ARQUIVO)
    df.to_excel("relatorio_vendas.xlsx", index=False)
    messagebox.showinfo("Sucesso", "Planilha Excel gerada: relatorio_vendas.xlsx")

# Interface gráfica principal
root = tk.Tk()
root.title("Sistema de Vendas de Camisetas")

tk.Label(root, text="Nome do cliente").grid(row=0, column=0)
entry_nome = tk.Entry(root); entry_nome.grid(row=0, column=1)

tk.Label(root, text="Tamanho").grid(row=1, column=0)
entry_tamanho = tk.Entry(root); entry_tamanho.grid(row=1, column=1)

tk.Label(root, text="Quantidade").grid(row=2, column=0)
entry_quantidade = tk.Entry(root); entry_quantidade.grid(row=2, column=1)

tk.Label(root, text="Valor unitário (R$)").grid(row=3, column=0)
entry_valor = tk.Entry(root); entry_valor.grid(row=3, column=1)

tk.Label(root, text="Forma de pagamento").grid(row=4, column=0)
entry_pagamento = tk.Entry(root); entry_pagamento.grid(row=4, column=1)

tk.Label(root, text="Recebedor").grid(row=5, column=0)
entry_recebedor = tk.Entry(root); entry_recebedor.grid(row=5, column=1)

# Botões CRUD
tk.Button(root, text="Registrar venda", command=registrar_venda).grid(row=6, column=0)
tk.Button(root, text="Salvar edição", command=salvar_edicao).grid(row=6, column=1)
tk.Button(root, text="Excluir venda", command=excluir_venda).grid(row=6, column=2)
tk.Button(root, text="Ver Relatório Completo", command=gerar_relatorio).grid(row=6, column=3)

# Campo de filtro
tk.Label(root, text="Filtro (Cliente/Tamanho/Forma de Pagamento/Recebedor)").grid(row=7, column=0)
entry_filtro = tk.Entry(root); entry_filtro.grid(row=7, column=1)
tk.Button(root, text="Aplicar filtro", command=aplicar_filtro).grid(row=7, column=2)

# Tabela principal
colunas = ("Cliente", "Tamanho", "Quantidade", "Valor Unitário", "Forma de Pagamento", "Recebedor", "Valor Total")
tabela = ttk.Treeview(root, columns=colunas, show="headings")
for col in colunas:
    tabela.heading(col, text=col)
    tabela.column(col, width=120)
tabela.grid(row=8, column=0, columnspan=4)
tabela.bind("<<TreeviewSelect>>", selecionar_venda)

# Label totais gerais
label_totais = tk.Label(root, text="Qtd total de itens: 0 | Valor total geral: R$ 0.00", font=("Arial", 10, "bold"))
label_totais.grid(row=9, column=0, columnspan=4)

# Tabela de resumo por tamanho
tk.Label(root, text="Resumo por tamanho").grid(row=10, column=0, columnspan=4)
tabela_tamanhos = ttk.Treeview(root, columns=("Tamanho", "Quantidade"), show="headings")
tabela_tamanhos.heading("Tamanho", text="Tamanho")
tabela_tamanhos.heading("Quantidade", text="Quantidade")
tabela_tamanhos.column("Tamanho", width=100)
tabela_tamanhos.column("Quantidade", width=100)
tabela_tamanhos.grid(row=11, column=0, columnspan=4)

# Inicializa o arquivo e carrega vendas
inicializar_arquivo()
carregar_vendas()

# Mantém a janela aberta
root.mainloop()