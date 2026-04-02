import streamlit as st
import pandas as pd
from supabase import create_client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
import matplotlib.pyplot as plt

# 🔑 CONFIGURAÇÃO SUPABASE
SUPABASE_URL = "uodegxbqdpswhyjdckwv"
SUPABASE_KEY = "sb_publishable_S21-ylfyHtSA3-NuqFeF_Q__d1ZWxrI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- CRUD ----------------
def inserir(cliente, tamanho, qtd, valor, pagamento, recebedor):
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

def listar(filtros):
    query = supabase.table("vendas").select("*")

    if filtros["cliente"]:
        query = query.ilike("cliente", f"%{filtros['cliente']}%")
    if filtros["tamanho"]:
        query = query.ilike("tamanho", f"%{filtros['tamanho']}%")
    if filtros["pagamento"]:
        query = query.ilike("pagamento", f"%{filtros['pagamento']}%")
    if filtros["recebedor"]:
        query = query.ilike("recebedor", f"%{filtros['recebedor']}%")

    data = query.order("id", desc=True).execute()
    return pd.DataFrame(data.data)

def excluir(id_venda):
    supabase.table("vendas").delete().eq("id", id_venda).execute()

# ---------------- PDF PRO ----------------
def gerar_pdf(df):
    nome = "relatorio_vendas.pdf"
    c = canvas.Canvas(nome, pagesize=landscape(A4))
    largura, altura = landscape(A4)

    y = altura - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(300, y, "RELATÓRIO DE VENDAS")

    # Cabeçalho azul piscina
    y -= 30
    colunas = ["cliente","tamanho","quantidade","valor_unitario","pagamento","recebedor","total"]
    x = 40

    c.setFont("Helvetica-Bold", 10)
    for col in colunas:
        c.setFillColor(colors.HexColor("#7FDBFF"))
        c.rect(x-2, y-2, 90, 15, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.drawString(x, y, col.upper())
        x += 90

    y -= 20

    # Dados
    qtd_total = 0
    valor_total = 0

    c.setFont("Helvetica", 9)

    for _, row in df.iterrows():
        x = 40
        y -= 15

        for col in colunas:
            c.drawString(x, y, str(row[col]))
            x += 90

        qtd_total += row["quantidade"]
        valor_total += row["total"]

        if y < 50:
            c.showPage()
            y = altura - 40

    # Totais lilás
    y -= 30
    c.setFillColor(colors.HexColor("#5F065F"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Total de itens: {qtd_total}")
    c.drawString(300, y, f"Valor total: R$ {valor_total:.2f}")

    c.save()
    return nome

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="Sistema PRO Vendas", layout="wide")
st.title("💎 Sistema ONLINE PRO de Vendas")

abas = st.tabs(["Cadastro", "Relatórios"])

# -------- CADASTRO --------
with abas[0]:
    with st.form("form_venda", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)

        with c1:
            cliente = st.text_input("Cliente")
            tamanho = st.text_input("Tamanho")

        with c2:
            qtd = st.number_input("Quantidade", min_value=1)
            valor = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")

        with c3:
            pagamento = st.text_input("Pagamento")
            recebedor = st.text_input("Recebedor")

        if st.form_submit_button("Registrar"):
            inserir(cliente, tamanho, qtd, valor, pagamento, recebedor)
            st.success("Venda registrada com sucesso!")

# -------- RELATÓRIOS --------
with abas[1]:
    st.subheader("Filtros")

    f1, f2, f3, f4 = st.columns(4)

    filtros = {
        "cliente": f1.text_input("Cliente"),
        "tamanho": f2.text_input("Tamanho"),
        "pagamento": f3.text_input("Pagamento"),
        "recebedor": f4.text_input("Recebedor")
    }

    df = listar(filtros)

    st.dataframe(df, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Gerar PDF"):
            arquivo = gerar_pdf(df)
            with open(arquivo, "rb") as f:
                st.download_button("Baixar PDF", f, file_name=arquivo)

    with col2:
        if st.button("Exportar Excel"):
            df.to_excel("vendas.xlsx", index=False)
            with open("vendas.xlsx", "rb") as f:
                st.download_button("Baixar Excel", f, file_name="vendas.xlsx")

    with col3:
        if st.button("Gráfico"):
            fig, ax = plt.subplots()
            df.groupby("tamanho")["quantidade"].sum().plot(kind="bar", ax=ax, color="#7FDBFF")
            st.pyplot(fig)

    st.subheader("Excluir venda")
    id_excluir = st.number_input("ID para excluir", min_value=0)
    if st.button("Excluir"):
        excluir(id_excluir)
        st.success("Venda excluída!")