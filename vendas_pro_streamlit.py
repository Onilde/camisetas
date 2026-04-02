# vendas_pro_streamlit_simples.py
import streamlit as st
import sqlite3
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import matplotlib.pyplot as plt
import os
import subprocess

DB = "vendas.db"

# ----------------- BANCO DE DADOS -----------------
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

# ----------------- CRUD -----------------
def registrar_venda(cliente, tamanho, qtd, valor, pagamento, recebedor):
    total = qtd * valor
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO vendas(cliente,tamanho,quantidade,valor_unitario,pagamento,recebedor,total)
        VALUES (?,?,?,?,?,?,?,?)
    ''', (cliente, tamanho, qtd, valor, pagamento, recebedor, total))
    conn.commit()
    conn.close()

def editar_venda(id_venda, cliente, tamanho, qtd, valor, pagamento, recebedor):
    total = qtd * valor
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE vendas
        SET cliente=?, tamanho=?, quantidade=?, valor_unitario=?, pagamento=?, recebedor=?, total=?
        WHERE id=?
    ''', (cliente, tamanho, qtd, valor, pagamento, recebedor, total, id_venda))
    conn.commit()
    conn.close()

def excluir_venda(id_venda):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas WHERE id=?", (id_venda,))
    conn.commit()
    conn.close()

def listar_vendas(filtro_cliente="", filtro_tamanho="", filtro_pagamento="", filtro_recebedor=""):
    conn = sqlite3.connect(DB)
    query = "SELECT * FROM vendas WHERE 1=1"
    params = []
    if filtro_cliente:
        query += " AND LOWER(cliente) LIKE ?"
        params.append(f"%{filtro_cliente.lower()}%")
    if filtro_tamanho:
        query += " AND LOWER(tamanho) LIKE ?"
        params.append(f"%{filtro_tamanho.lower()}%")
    if filtro_pagamento:
        query += " AND LOWER(pagamento) LIKE ?"
        params.append(f"%{filtro_pagamento.lower()}%")
    if filtro_recebedor:
        query += " AND LOWER(recebedor) LIKE ?"
        params.append(f"%{filtro_recebedor.lower()}%")
    query += " ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# ----------------- RELATÓRIO PDF -----------------
def gerar_pdf(df, nome_pdf="relatorio_vendas.pdf"):
    c = canvas.Canvas(nome_pdf, pagesize=landscape(A4))
    largura, altura = landscape(A4)

    # Marca d'água
    try:
        logo = ImageReader("logo.png")  # opcional
        c.saveState()
        c.translate((largura-300)/2,(altura-300)/2)
        c.setFillAlpha(0.1)
        c.drawImage(logo,0,0,width=300,height=300,mask='auto')
        c.restoreState()
    except:
        pass

    y = altura - 40
    c.setFont("Helvetica-Bold", 14)
    texto = "RELATÓRIO DE VENDAS"
    largura_texto = c.stringWidth(texto, "Helvetica-Bold", 14)
    c.drawString((largura - largura_texto)/2, y, texto)

    # Cabeçalho azul piscina
    y -= 30
    colunas = ["Cliente","Tamanho","Qtd","Valor","Pagamento","Recebedor","Total"]
    x_pos = [40,150,200,250,330,450,580]
    c.setFont("Helvetica-Bold",10)
    for i,col in enumerate(colunas):
        c.setFillColor(colors.HexColor("#7FDBFF"))
        c.rect(x_pos[i]-2,y-2,100,15,fill=1,stroke=0)
        c.setFillColor(colors.black)
        c.drawString(x_pos[i],y,col)
    y -= 15
    c.line(40,y,800,y)

    # Dados
    c.setFont("Helvetica",9)
    qtd_total = 0
    valor_total = 0
    for _, row in df.iterrows():
        y -= 15
        for j, val in enumerate(row[1:]):
            c.drawString(x_pos[j],y,str(val))
        qtd_total += row["quantidade"]
        valor_total += row["total"]
        if y < 50:
            c.showPage()
            y = altura - 40

    # Totais lilás
    y -= 30
    c.setFont("Helvetica-Bold",11)
    c.setFillColor(colors.HexColor("#5F065F"))
    c.drawString(40,y,f"Total de itens: {qtd_total}")
    c.drawString(300,y,f"Valor Total: R$ {valor_total:.2f}")
    c.setFillColor(colors.black)
    c.save()
    return nome_pdf

# ----------------- EXPORTAR EXCEL -----------------
def exportar_excel(df, nome_excel="vendas.xlsx"):
    df.to_excel(nome_excel,index=False)
    return nome_excel

# ----------------- GRÁFICO -----------------
def gerar_grafico(df):
    resumo = df.groupby("tamanho")["quantidade"].sum()
    fig, ax = plt.subplots()
    resumo.plot(kind="bar", color="#7FDBFF", ax=ax)
    ax.set_title("Vendas por Tamanho")
    ax.set_ylabel("Quantidade")
    ax.set_xlabel("Tamanho")
    st.pyplot(fig)

# ----------------- STREAMLIT -----------------
st.set_page_config(page_title="Sistema PRO Vendas", layout="wide")
st.title("💎 Sistema PRO de Vendas")

iniciar_bd()

tabs = st.tabs(["Cadastro / CRUD", "Relatórios"])

# ---------- ABA CADASTRO ----------
with tabs[0]:
    st.subheader("Registrar Venda")
    with st.form("form_venda", clear_on_submit=True):
        cliente = st.text_input("Cliente")
        tamanho = st.text_input("Tamanho")
        quantidade = st.number_input("Quantidade", min_value=1)
        valor = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")
        pagamento = st.text_input("Pagamento")
        recebedor = st.text_input("Recebedor")
        submitted = st.form_submit_button("Registrar")
        if submitted:
            registrar_venda(cliente,tamanho,quantidade,valor,pagamento,recebedor)
            st.success("Venda registrada com sucesso!")

    st.subheader("Vendas cadastradas")
    filtro_cliente = st.text_input("Filtrar por Cliente", key="fcliente")
    filtro_tamanho = st.text_input("Filtrar por Tamanho", key="ftamanho")
    filtro_pagamento = st.text_input("Filtrar por Pagamento", key="fpagamento")
    filtro_recebedor = st.text_input("Filtrar por Recebedor", key="frecebedor")
    df = listar_vendas(filtro_cliente,filtro_tamanho,filtro_pagamento,filtro_recebedor)
    st.dataframe(df)

# ---------- ABA RELATÓRIOS ----------
with tabs[1]:
    st.subheader("Relatórios e Exportações")
    df_rel = listar_vendas()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Gerar PDF PRO"):
            pdf_file = gerar_pdf(df_rel)
            with open(pdf_file,"rb") as f:
                st.download_button("Baixar PDF", f, file_name=pdf_file)
    with col2:
        if st.button("Exportar Excel"):
            excel_file = exportar_excel(df_rel)
            with open(excel_file,"rb") as f:
                st.download_button("Baixar Excel", f, file_name=excel_file)
    with col3:
        if st.button("Gráfico de Vendas"):
            gerar_grafico(df_rel)