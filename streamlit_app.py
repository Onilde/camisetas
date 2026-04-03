import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ----------- CONFIGURAÇÃO SUPABASE -----------

SUPABASE_URL = "https://uodegxbqdpswhyjdckwv.supabase.co"  # <--- substitua aqui
SUPABASE_KEY = "<sb_publishable_S21-ylfyHtSA3-NuqFeF_Q__d1ZWxrI>"                   # <--- substitua aqui

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------- FUNÇÕES DE DADOS -----------

def registrar_venda(cliente, tamanho, quantidade, valor_unitario, pagamento, recebedor):
    total = quantidade * valor_unitario
    data = {
        "cliente": cliente,
        "tamanho": tamanho,
        "quantidade": quantidade,
        "valor_unitario": valor_unitario,
        "pagamento": pagamento,
        "recebedor": recebedor,
        "total": total
    }
    response = supabase.table("vendas").insert(data).execute()
    if response.error:
        st.error(f"Erro ao registrar venda: {response.error.message}")
    else:
        st.success("Venda registrada com sucesso!")

def listar_vendas(filtro_cliente="", filtro_tamanho="", filtro_pagamento="", filtro_recebedor=""):
    query = supabase.table("vendas").select("*")
    if filtro_cliente:
        query = query.ilike("cliente", f"%{filtro_cliente}%")
    if filtro_tamanho:
        query = query.ilike("tamanho", f"%{filtro_tamanho}%")
    if filtro_pagamento:
        query = query.ilike("pagamento", f"%{filtro_pagamento}%")
    if filtro_recebedor:
        query = query.ilike("recebedor", f"%{filtro_recebedor}%")

    response = query.order("id", desc=True).execute()
    if response.error:
        st.error(f"Erro ao buscar vendas: {response.error.message}")
        return pd.DataFrame()
    return pd.DataFrame(response.data)

# ----------- UI STREAMLIT -----------

st.title("💎 Sistema PRO de Vendas com Supabase")

with st.form("form_venda", clear_on_submit=True):
    cliente = st.text_input("Cliente")
    tamanho = st.text_input("Tamanho")
    quantidade = st.number_input("Quantidade", min_value=1, step=1)
    valor_unitario = st.number_input("Valor Unitário", min_value=0.0, step=0.01, format="%.2f")
    pagamento = st.text_input("Pagamento")
    recebedor = st.text_input("Recebedor")
    submitted = st.form_submit_button("Registrar Venda")
    if submitted:
        registrar_venda(cliente, tamanho, quantidade, valor_unitario, pagamento, recebedor)

st.subheader("Vendas Cadastradas")

filtro_cliente = st.text_input("Filtrar por Cliente")
filtro_tamanho = st.text_input("Filtrar por Tamanho")
filtro_pagamento = st.text_input("Filtrar por Pagamento")
filtro_recebedor = st.text_input("Filtrar por Recebedor")

df_vendas = listar_vendas(filtro_cliente, filtro_tamanho, filtro_pagamento, filtro_recebedor)
st.dataframe(df_vendas)