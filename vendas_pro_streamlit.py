import streamlit as st
import pandas as pd
from supabase import create_client, Client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import matplotlib.pyplot as plt
import io

# --------- Conexão Supabase ---------
SUPABASE_URL = "COLE_SUA_URL_AQUI"
SUPABASE_KEY = "COLE_SUA_CHAVE_PUBLICA_AQUI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------- Funções ---------
def registrar_venda(cliente, tamanho, qtd, valor, pagamento, recebedor):
    total = qtd * valor
    supabase.table("vendas").insert({
        "cliente": cliente,
        "tamanho": tamanho,
        "quantidade": qtd,
        "valor_unitario": valor,
        "pagamento": pagamento,
        "recebedor": recebedor,
        "total": total
    }).execute()

def listar_vendas(filtro_cliente="", filtro_tamanho="", filtro_pagamento="", filtro_recebedor=""):
    res = supabase.table("vendas").select("*").execute()
    df = pd.DataFrame(res.data)
    if df.empty:
        return df
    if filtro_cliente:
        df = df[df["cliente"].str.lower().str.contains(filtro_cliente.lower())]
    if filtro_tamanho:
        df = df[df["tamanho"].str.lower().str.contains(filtro_tamanho.lower())]
    if filtro_pagamento:
        df = df[df["pagamento"].str.lower().str.contains(filtro_pagamento.lower())]
    if filtro_recebedor:
        df = df[df["recebedor"].str.lower().str.contains(filtro_recebedor.lower())]
    return df

def gerar_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    largura, altura = landscape(A4)

    # Cabeçalho
    y = altura - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, y, "RELATÓRIO DE VENDAS")
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

    c.setFont("Helvetica",9)
    for _, row in df.iterrows():
        y -= 15
        for j, val in enumerate([row.get(col.lower(), "") for col in colunas]):
            c.drawString(x_pos[j],y,str(val))
        if y < 50:
            c.showPage()
            y = altura - 40
    c.save()
    buffer.seek(0)
    return buffer

# --------- Streamlit UI ---------
st.set_page_config(page_title="Sistema PRO Vendas Online", layout="wide")
st.title("💎 Sistema PRO Vendas com Supabase")

# Formulário
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

# Filtros
st.subheader("Vendas cadastradas")
col1, col2, col3, col4 = st.columns(4)
with col1:
    filtro_cliente = st.text_input("Filtrar por Cliente")
with col2:
    filtro_tamanho = st.text_input("Filtrar por Tamanho")
with col3:
    filtro_pagamento = st.text_input("Filtrar por Pagamento")
with col4:
    filtro_recebedor = st.text_input("Filtrar por Recebedor")

df = listar_vendas(filtro_cliente, filtro_tamanho, filtro_pagamento, filtro_recebedor)
st.dataframe(df)

# Exportar Excel
if st.button("Exportar Excel"):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("Baixar Excel", buffer, file_name="vendas.xlsx")

# Gerar PDF
if st.button("Gerar PDF"):
    pdf_buffer = gerar_pdf(df)
    st.download_button("Baixar PDF", pdf_buffer, file_name="relatorio_vendas.pdf")

# Gráfico
st.subheader("Vendas por Tamanho")
if not df.empty:
    resumo = df.groupby("tamanho")["quantidade"].sum()
    st.bar_chart(resumo)