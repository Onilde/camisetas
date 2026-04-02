# vendas_pro_streamlit.py
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
        VALUES (?,?,?,?,?,?,?)
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

def listar_vendas(filtro="", coluna="Todos"):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    filtro = filtro.lower().strip()
    if coluna == "Todos" or filtro=="":
        cursor.execute("SELECT * FROM vendas ORDER BY id")
    else:
        cursor.execute(f"SELECT * FROM vendas WHERE LOWER({coluna}) LIKE ?", ('%'+filtro+'%',))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ----------------- RELATÓRIO PDF -----------------
def gerar_pdf(vendas, nome_pdf="relatorio_vendas.pdf"):
    c = canvas.Canvas(nome_pdf, pagesize=landscape(A4))
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
    c.setFillColor(colors.black)
    qtd_total = 0
    valor_total = 0
    for row in vendas:
        y -= 15
        for j,val in enumerate(row[1:]):
            c.drawString(x_pos[j],y,str(val))
        qtd_total += row[3]
        valor_total += row[7]
        if y < 50:
            c.showPage()
            y = altura - 40

    # Totais lilás
    y -= 30
    c.setFont("Helvetica-Bold",11)
    c.setFillColor(colors.HexColor("#5F065F"))
    c.drawString(40,y,f"Total de itens: {qtd_total}")
    c.drawString(300,y,f"Valor Total: R$ {valor_total:.2f}")
    c.save()
    if os.name=="nt":
        os.startfile(nome_pdf)
    else:
        subprocess.call(["xdg-open", nome_pdf])

# ----------------- EXPORTAR EXCEL -----------------
def exportar_excel(vendas, nome_excel="vendas.xlsx"):
    df = pd.DataFrame(vendas, columns=["ID","Cliente","Tamanho","Quantidade","Valor","Pagamento","Recebedor","Total"])
    df.to_excel(nome_excel,index=False)

# ----------------- GRÁFICO -----------------
def gerar_grafico(vendas):
    df = pd.DataFrame(vendas, columns=["ID","Cliente","Tamanho","Quantidade","Valor","Pagamento","Recebedor","Total"])
    resumo = df.groupby("Tamanho")["Quantidade"].sum()
    plt.figure(figsize=(8,4))
    plt.bar(resumo.index,resumo.values,color="#7FDBFF")
    plt.title("Vendas por Tamanho")
    plt.xlabel("Tamanho")
    plt.ylabel("Quantidade")
    st.pyplot(plt)

# ----------------- STREAMLIT UI -----------------
st.set_page_config(page_title="Sistema PRO de Vendas", layout="wide")
st.title("💎 Sistema PRO de Vendas Multiusuário")

iniciar_bd()

tabs = st.tabs(["Cadastro / CRUD", "Relatórios"])

# ---------- ABA CADASTRO ----------
with tabs[0]:
    with st.form("form_venda",clear_on_submit=True):
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
    filtro_coluna = st.selectbox("Filtrar por:", ["Todos","cliente","tamanho","pagamento","recebedor"])
    filtro_texto = st.text_input("Buscar")
    vendas = listar_vendas(filtro_texto,filtro_coluna)
    df = pd.DataFrame(vendas, columns=["ID","Cliente","Tamanho","Quantidade","Valor","Pagamento","Recebedor","Total"])
    selected = st.data_editor(df, num_rows="dynamic")
    
    # Ações CRUD
    st.write("### Ações")
    st.write("Selecione uma linha acima para Editar ou Excluir")
    if st.button("Editar venda selecionada"):
        if selected.shape[0] > 0:
            row = selected.iloc[-1]  # última linha editada
            editar_venda(row["ID"], row["Cliente"], row["Tamanho"], row["Quantidade"], row["Valor"], row["Pagamento"], row["Recebedor"])
            st.success("Venda editada!")
    if st.button("Excluir venda selecionada"):
        if selected.shape[0] > 0:
            row = selected.iloc[-1]
            excluir_venda(row["ID"])
            st.success("Venda excluída!")

# ---------- ABA RELATÓRIOS ----------
with tabs[1]:
    st.write("### Relatórios e Exportações")
    if st.button("Gerar PDF PRO"):
        vendas_rel = listar_vendas()
        gerar_pdf(vendas_rel)
        st.success("PDF gerado com sucesso!")

    if st.button("Exportar Excel"):
        vendas_rel = listar_vendas()
        exportar_excel(vendas_rel)
        st.success("Excel gerado!")

    if st.button("Gráfico de Vendas"):
        vendas_rel = listar_vendas()
        gerar_grafico(vendas_rel)