# streamlit_app.py
import streamlit as st
import cohere, random, re, os

# ─── LISTA DE AUTORES ────────────────────────────────────────────
AUTORES = [
    "Machado de Assis",
    "Guimarães Rosa",
    "Jorge Amado",
    "Rachel de Queiroz",
    "Lygia Fagundes Telles",
]

# Palavras-chave ocultas para variar o prompt (evita repetição)
CHAVES = ["girassol", "oceano", "montanha", "lua", "café",
          "vento", "labirinto", "bússola", "bruma", "neblina"]

# ─── LE CHAVE DA COHERE ──────────────────────────────────────────
API_KEY = st.secrets.get("COHERE_API_KEY") or os.getenv("COHERE_API_KEY")
if not API_KEY:
    st.error("⚠️ Configure COHERE_API_KEY em Settings → Secrets e recarregue.")
    st.stop()
co = cohere.Client(API_KEY)

# ─── FUNÇÃO QUE GERA A HISTÓRIA ─────────────────────────────────
def gerar_historia(autor: str) -> str:
    prompt = (
        f"Você é um autor brasileiro famoso chamado {autor}. "
        f"Escreva três parágrafos de uma história curta, com personagens icônicos do estilo de {autor}. "
        "Use português do Brasil, nenhuma palavra em outro idioma, linguagem literária e termine com um gancho para o leitor concluir. "
        "Não adicione títulos nem numere os parágrafos."
    )
    rsp = co.chat(
        model="command-r",
        message=prompt,
        temperature=1.0,
        p=0.9,
        k=50,
        seed=random.randint(1, 2_000_000_000),
    )
    texto = rsp.text.strip()
    texto = re.sub(r'^\s*\(?\s*texto\s*:\s*', '', texto, flags=re.I)      # tira “texto:”
    texto = re.sub(r'Parágrafo\s*\d+\s*:\s*',  '', texto, flags=re.I)      # tira “Parágrafo 1:”
    return texto

# ─── INTERFACE STREAMLIT ────────────────────────────────────────
st.title("✍️ Histórias cooperativas – escreva junto com autores clássicos do Brasil")

autor = st.selectbox("Escolha o autor:", AUTORES)

if st.button("Gerar história"):
    with st.spinner("Gerando…"):
        try:
            st.text_area("História:", gerar_historia(autor), height=300)
        except Exception as e:
            st.error(f"Erro: {e}")

desfecho = st.text_area("Seu desfecho:", height=200)
if st.button("Enviar desfecho"):
    st.success("Obrigado! (esta demo não salva o texto)")
