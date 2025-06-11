"""
Histórias Cooperativas – grava desfechos no Google Sheets
"""

import streamlit as st
import cohere, random, re, json, gspread
from google.oauth2.service_account import Credentials

# ──────────────────────────────────────────────────────────────
# CONFIGURAÇÕES BÁSICAS
# ──────────────────────────────────────────────────────────────
AUTORES = [
    "Machado de Assis",
    "Guimarães Rosa",
    "Jorge Amado",
    "Rachel de Queiroz",
    "Lygia Fagundes Telles",
]
CHAVES = [
    "girassol", "oceano", "montanha", "lua", "café",
    "vento", "labirinto", "bússola", "bruma", "neblina",
]

# ──────────────────────────────────────────────────────────────
# 1. LER OS SEGREDOS
# ──────────────────────────────────────────────────────────────
# Cohere
try:
    COHERE_API_KEY = st.secrets["COHERE_API_KEY"]
except KeyError:
    st.error("❌ COHERE_API_KEY faltando em Settings → Secrets.")
    st.stop()

# Google Sheet ID
try:
    SHEET_ID = st.secrets["SHEET_ID"]
except KeyError:
    st.error("❌ SHEET_ID faltando em Settings → Secrets.")
    st.stop()

# Credenciais JSON da Google Service Account
try:
    GSHEET_JSON_RAW = st.secrets["GSHEET_CREDS"]
    GSHEET_CREDS = json.loads(GSHEET_JSON_RAW)
except KeyError:
    st.error("❌ GSHEET_CREDS faltando em Settings → Secrets.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"❌ GSHEET_CREDS não é JSON válido: {e}")
    st.stop()

# ──────────────────────────────────────────────────────────────
# 2. CONECTAR À COHERE
# ──────────────────────────────────────────────────────────────
co = cohere.Client(COHERE_API_KEY)

def gerar_historia(autor: str) -> str:
    prompt = (
        f"(chave:{random.choice(CHAVES)}) "
        f"Escreva três parágrafos de uma história inédita em português, "
        f"imitando o estilo de {autor}. "
        f"Inclua pelo menos um personagem marcante criado por {autor}. "
        "Finalize com um gancho que convide o leitor a concluir a narrativa."
    )
    rsp = co.chat(
        model="command-r",
        message=prompt,
        temperature=1.0,
        p=0.9,
        k=50,
        seed=random.randint(1, 2_000_000_000),
    )
    texto = rsp.text
    texto = re.sub(r'^\s*\(?\s*texto\s*:\s*', '', texto, flags=re.I)
    texto = re.sub(r'Parágrafo\s*\d+\s*:\s*', '', texto, flags=re.I)
    return texto.strip()

# ──────────────────────────────────────────────────────────────
# 3. CONECTAR AO GOOGLE SHEETS (com cache)
# ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando ao Google Sheets…")
def abrir_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_info(GSHEET_CREDS, scopes=scopes)
    gc     = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID).sheet1      # primeira aba

sheet = abrir_sheet()

def gravar(desfecho, historia, autor, email):
    sheet.append_row(
        [autor, historia, desfecho, email],
        value_input_option="RAW"
    )

# ──────────────────────────────────────────────────────────────
# 4. INTERFACE STREAMLIT
# ──────────────────────────────────────────────────────────────
st.title("✍️ Histórias cooperativas – autores clássicos brasileiros")

autor     = st.selectbox("Escolha o autor:", AUTORES)
email     = st.text_input("Seu e-mail (opcional):")
hist_key  = "historia"

if st.button("Gerar história"):
    with st.spinner("Gerando…"):
        st.session_state[hist_key] = gerar_historia(autor)

st.text_area(
    "História:", 
    st.session_state.get(hist_key, ""), 
    height=300, 
    disabled=True
)

desfecho = st.text_area("Seu desfecho:", height=200)

if st.button("Enviar desfecho"):
    if not st.session_state.get(hist_key):
        st.warning("Primeiro gere a história.")
    elif not desfecho.strip():
        st.warning("Digite um desfecho antes de enviar.")
    else:
        try:
            gravar(desfecho.strip(), st.session_state[hist_key], autor, email)
            st.success("Desfecho salvo! O professor já pode ver na planilha.")
        except Exception as e:
            st.error(f"Falhou ao gravar: {e}")
