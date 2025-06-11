import streamlit as st, cohere, random, re, json, gspread
from google.oauth2.service_account import Credentials

# ─── IA Cohere ───────────────────────────────────────────────────────────
AUTORES = ["Machado de Assis","Guimarães Rosa","Jorge Amado",
           "Rachel de Queiroz","Lygia Fagundes Telles"]
CHAVES  = ["girassol","oceano","montanha","lua","café",
           "vento","labirinto","bússola","bruma","neblina"]
co = cohere.Client(st.secrets["COHERE_API_KEY"])

def gerar_historia(autor):
    prompt = (f"(chave:{random.choice(CHAVES)}) "
              f"Escreva três parágrafos de uma história inédita em português, "
              f"imitando o estilo de {autor}. "
              f"Inclua pelo menos um personagem marcante criado por {autor}. "
              "Finalize com um gancho que convide o leitor a concluir a narrativa.")
    r = co.chat(model="command-r", message=prompt,
                temperature=1.0, p=0.9, k=50,
                seed=random.randint(1,2_000_000_000))
    texto = re.sub(r'^\s*\(?\s*texto\s*:\s*','', r.text, flags=re.I)
    texto = re.sub(r'Parágrafo\s*\d+\s*:\s*','', texto, flags=re.I)
    return texto.strip()

# ─── Conexão Sheets (cacheada) ───────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando ao Google Sheets…")
def abrir_sheet():
    creds_dict = json.loads(st.secrets["GSHEET_CREDS"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc     = gspread.authorize(creds)
    return gc.open_by_key(st.secrets["SHEET_ID"]).sheet1   # primeira aba
sheet = abrir_sheet()

def gravar(desfecho, historia, autor, email):
    sheet.append_row(
        [autor, historia, desfecho, email],
        value_input_option="RAW"
    )

# ─── Interface ───────────────────────────────────────────────────────────
st.title("✍️ Histórias cooperativas – autores clássicos brasileiros")

autor = st.selectbox("Escolha o autor:", AUTORES)
email = st.text_input("Seu e-mail (opcional):")

if "historia" not in st.session_state:
    st.session_state.historia = ""

if st.button("Gerar história"):
    with st.spinner("Gerando…"):
        st.session_state.historia = gerar_historia(autor)

st.text_area("História:", st.session_state.historia, height=300, disabled=True)
desfecho = st.text_area("Seu desfecho:", height=200)

if st.button("Enviar desfecho"):
    if not st.session_state.historia:
        st.warning("Primeiro gere a história.")
    elif not desfecho.strip():
        st.warning("Digite um desfecho antes de enviar.")
    else:
        try:
            gravar(desfecho.strip(), st.session_state.historia, autor, email)
            st.success("Desfecho salvo! O professor já pode ver na planilha.")
        except Exception as e:
            st.error(f"Falhou ao gravar: {e}")
