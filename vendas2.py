import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, os, subprocess
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
import pandas as pd

DB = "vendas.db"

# ---------------- BANCO ----------------
def iniciar_bd():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            tamanho TEXT,
            quantidade INTEGER,
            valor_unitario REAL,
            pagamento TEXT,
            recebedor TEXT,
            total REAL
        )
    ''')
    conn.commit()
    conn.close()

# ---------------- CRUD ----------------
def registrar():
    try:
        qtd = int(entry_qtd.get())
        valor = float(entry_valor.get())
        total = qtd * valor
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vendas(cliente,tamanho,quantidade,valor_unitario,pagamento,recebedor,total)
            VALUES (?,?,?,?,?,?,?)
        ''', (
            entry_nome.get(),
            entry_tamanho.get(),
            qtd,
            valor,
            entry_pagamento.get(),
            entry_recebedor.get(),
            total
        ))
        conn.commit()
        conn.close()
        carregar()
        limpar()
    except:
        messagebox.showerror("Erro","Verifique os dados digitados!")

def carregar(filtro="", coluna="Todos"):
    tabela.delete(*tabela.get_children())
    filtro = filtro.lower().strip()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    if coluna == "Todos":
        cursor.execute("SELECT * FROM vendas")
    else:
        cursor.execute(f"SELECT * FROM vendas WHERE LOWER({coluna}) LIKE ?",('%'+filtro+'%',))
    rows = cursor.fetchall()
    conn.close()

    qtd_total = 0
    valor_total = 0
    for row in rows:
        tabela.insert("",tk.END,values=row[1:])
        qtd_total += row[3]
        valor_total += row[7]
    label_total.config(text=f"Qtd: {qtd_total} | Total: R$ {valor_total:.2f}")

def editar():
    item = tabela.selection()
    if not item: return
    idx = tabela.index(item)
    id_venda = get_id_from_index(idx)
    try:
        qtd = int(entry_qtd.get())
        valor = float(entry_valor.get())
        total = qtd * valor
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE vendas
            SET cliente=?, tamanho=?, quantidade=?, valor_unitario=?, pagamento=?, recebedor=?, total=?
            WHERE id=?
        ''', (
            entry_nome.get(),
            entry_tamanho.get(),
            qtd,
            valor,
            entry_pagamento.get(),
            entry_recebedor.get(),
            total,
            id_venda
        ))
        conn.commit()
        conn.close()
        carregar()
        limpar()
    except:
        messagebox.showerror("Erro","Verifique os dados")

def excluir():
    item = tabela.selection()
    if not item: return
    idx = tabela.index(item)
    id_venda = get_id_from_index(idx)
    if messagebox.askyesno("Confirmar","Excluir venda?"):
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vendas WHERE id=?",(id_venda,))
        conn.commit()
        conn.close()
        carregar()

def limpar():
    for e in [entry_nome, entry_tamanho, entry_qtd, entry_valor, entry_pagamento, entry_recebedor]:
        e.delete(0, tk.END)

def selecionar(event):
    item = tabela.selection()
    if item:
        valores = tabela.item(item)["values"]
        for e,v in zip([entry_nome, entry_tamanho, entry_qtd, entry_valor, entry_pagamento, entry_recebedor], valores):
            e.delete(0, tk.END)
            e.insert(0, v)

def get_id_from_index(idx):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vendas ORDER BY id")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids[idx]

# ---------------- PESQUISA ----------------
def pesquisar():
    carregar(entry_busca.get(), combo_filtro.get())

# ---------------- PDF PRO ----------------
def gerar_pdf_pro():
    filtro_texto = entry_filtro_pdf.get().lower()
    filtro_coluna = combo_filtro_pdf.get().lower()

    nome = "relatorio_vendas_pro.pdf"
    c = canvas.Canvas(nome, pagesize=landscape(A4))
    largura, altura = landscape(A4)

    # Marca d'água
    try:
        logo = ImageReader("logo.png")
        c.saveState()
        c.translate((largura-300)/2,(altura-300)/2)
        c.setFillAlpha(0.1)
        c.drawImage(logo,0,0,width=300,height=300,mask='auto')
        c.restoreState()
    except:
        pass

    y = altura - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40,y,"RELATÓRIO PRO DE VENDAS")

    # Cabeçalho azul piscina
    y -= 30
    colunas = ["Cliente","Tamanho","Qtd","Valor","Pagamento","Recebedor","Total"]
    x_pos = [40,150,200,250,330,450,580]
    c.setFont("Helvetica-Bold",10)
    for i,col in enumerate(colunas):
        c.setFillColor(colors.HexColor("#7FDBFF"))
        c.rect(x_pos[i]-2,y-2,100,15,fill=1,stroke=0)
        c.setFillColor(colors.white)
        c.drawString(x_pos[i],y,col)
    y -= 15
    c.line(40,y,800,y)

    # Dados filtrados
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    if filtro_coluna=="todos" or filtro_texto=="":
        cursor.execute("SELECT cliente,tamanho,quantidade,valor_unitario,pagamento,recebedor,total FROM vendas")
    else:
        cursor.execute(f"SELECT cliente,tamanho,quantidade,valor_unitario,pagamento,recebedor,total FROM vendas WHERE LOWER({filtro_coluna}) LIKE ?",('%'+filtro_texto+'%',))
    rows = cursor.fetchall()
    conn.close()

    qtd_total = 0
    valor_total = 0
    for row in rows:
        y -= 15
        for j,val in enumerate(row):
            c.setFillColor(colors.black)
            c.drawString(x_pos[j],y,str(val))
        qtd_total += row[2]
        valor_total += row[6]
        if y<50:
            c.showPage()
            y = altura - 40

    # Totais lilás
    y -= 30
    c.setFont("Helvetica-Bold",11)
    c.setFillColor(colors.HexColor("#C8A2C8"))
    c.drawString(40,y,f"Total de itens: {qtd_total}")
    c.drawString(300,y,f"Valor Total: R$ {valor_total:.2f}")

    # Gráfico de barras
    if rows:
        drawing = Drawing(400,200)
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 30
        bc.height = 150
        bc.width = 300
        bc.data = [[row[2] for row in rows]]
        bc.categoryAxis.categoryNames = [row[1] for row in rows]
        bc.barWidth = 10
        bc.fillColor = colors.HexColor("#7FDBFF")
        drawing.add(bc)
        drawing.drawOn(c,400,50)

    c.save()
    os.startfile(nome) if os.name=="nt" else subprocess.call(["xdg-open",nome])

# ---------------- EXCEL ----------------
def excel():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT cliente,tamanho,quantidade,valor_unitario,pagamento,recebedor,total FROM vendas", conn)
    df.to_excel("vendas_pro.xlsx",index=False)
    conn.close()
    messagebox.showinfo("Sucesso","Excel gerado!")

# ---------------- UI ----------------
root = tk.Tk()
root.title("Sistema PRO EXTREMO")
root.geometry("1000x600")

abas = ttk.Notebook(root)
abas.pack(fill="both", expand=True)

# ABA CADASTRO
aba1 = tk.Frame(abas)
abas.add(aba1,text="Cadastro")

frame = tk.Frame(aba1)
frame.pack(pady=10)

def campo(txt,row):
    tk.Label(frame,text=txt).grid(row=row,column=0)
    e = tk.Entry(frame)
    e.grid(row=row,column=1)
    return e

entry_nome = campo("Cliente",0)
entry_tamanho = campo("Tamanho",1)
entry_qtd = campo("Qtd",2)
entry_valor = campo("Valor",3)
entry_pagamento = campo("Pagamento",4)
entry_recebedor = campo("Recebedor",5)

tk.Button(frame,text="Registrar",command=registrar).grid(row=6,column=0,padx=5)
tk.Button(frame,text="Editar",command=editar).grid(row=6,column=1,padx=5)
tk.Button(frame,text="Excluir",command=excluir).grid(row=6,column=2,padx=5)

# Busca
frame_busca = tk.Frame(aba1)
frame_busca.pack(pady=5)
entry_busca = tk.Entry(frame_busca)
entry_busca.pack(side="left", padx=5)
combo_filtro = ttk.Combobox(frame_busca, values=["Todos","cliente","tamanho","pagamento","recebedor"])
combo_filtro.set("Todos")
combo_filtro.pack(side="left", padx=5)
tk.Button(frame_busca,text="Pesquisar",command=pesquisar).pack(side="left", padx=5)

# Tabela
tabela = ttk.Treeview(aba1, columns=("Cliente","Tamanho","Qtd","Valor","Pagamento","Recebedor","Total"), show="headings")
for c in tabela["columns"]:
    tabela.heading(c,text=c)
tabela.pack(fill="both", expand=True)
tabela.bind("<<TreeviewSelect>>", selecionar)

label_total = tk.Label(aba1,text="")
label_total.pack()

# ABA RELATÓRIOS
aba2 = tk.Frame(abas)
abas.add(aba2,text="Relatórios")

tk.Label(aba2,text="Filtro de relatório (opcional)").pack(pady=5)
frame_pdf_filter = tk.Frame(aba2)
frame_pdf_filter.pack()
entry_filtro_pdf = tk.Entry(frame_pdf_filter)
entry_filtro_pdf.pack(side="left", padx=5)
combo_filtro_pdf = ttk.Combobox(frame_pdf_filter, values=["Todos","cliente","tamanho","pagamento","recebedor"])
combo_filtro_pdf.set("Todos")
combo_filtro_pdf.pack(side="left", padx=5)
tk.Button(frame_pdf_filter,text="Gerar PDF PRO",command=gerar_pdf_pro).pack(side="left", padx=5)
tk.Button(aba2,text="Exportar Excel",command=excel,width=25).pack(pady=10)

# ---------------- INICIAR ----------------
iniciar_bd()
carregar()
root.mainloop()