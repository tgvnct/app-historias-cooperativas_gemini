# streamlit_app.py - VERSÃO PARA GOOGLE GEMINI - 14/6/2025

import streamlit as st
import google.generativeai as genai
import random
import re
import os
import gspread
from google.oauth2.service_account import Credentials
from textwrap import dedent

# --- CONSTANTES ---
AUTORES = [
    "Machado de Assis",
    "Guimarães Rosa",
    "Jorge Amado",
    "Rachel de Queiroz",
    "Lygia Fagundes Telles",
    "Itamar Vieira Junior",
    "João Simões Lopes Neto",
]

# --- FUNÇÕES ---

# Função do Google Sheets
def connect_to_gsheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Desfechos das Histórias")
        worksheet = spreadsheet.worksheet("Página1")
        return worksheet
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return None

# Configuração da API do Google Gemini
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Configure GOOGLE_API_KEY nos Secrets do Streamlit.")
    st.stop()

# Função para gerar história usando o Gemini

def gerar_historia(autor: str) -> str:
    # Selecionamos o modelo do Gemini
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
    
    prompt = (
        f"Aja como se você fosse o autor brasileiro {autor}. "
        f"Escreva o início de uma história, em três parágrafos, no estilo inconfundível de {autor}, usando seu vocabulário, ritmo e temas característicos. "
        "A história deve ser em português do Brasil e terminar com uma frase de suspense, um 'gancho' que convide o leitor a continuar a narrativa. "
        "Não adicione títulos ou numeração aos parágrafos."
    )
    
    # Geramos o conteúdo
    response = model.generate_content(prompt)
    
    # Limpamos o texto (se necessário)
    texto = response.text.strip()
    texto = re.sub(r'^\s*\(?\s*texto\s*:\s*', '', texto, flags=re.I)
    texto = re.sub(r'Parágrafo\s*\d+\s*:\s*', '', texto, flags=re.I)
    return texto

# --- INTERFACE E LÓGICA PRINCIPAL 

st.title("✍️ Histórias cooperativas - escreva com grandes nomes da literatura brasileira")

# Inicializa as variáveis de estado da sessão
if 'historia_gerada' not in st.session_state:
    st.session_state.historia_gerada = ""
if 'autor_selecionado' not in st.session_state:
    st.session_state.autor_selecionado = ""
if 'desfecho_usuario' not in st.session_state:
    st.session_state.desfecho_usuario = ""
if 'envio_concluido' not in st.session_state:
    st.session_state.envio_concluido = False

# Lógica de exibição da interface
if not st.session_state.envio_concluido:
    st.write("Escreva junto com autores clássicos do Brasil")
    autor = st.selectbox("Escolha o autor:", AUTORES)

    if st.button("Gerar início da história"):
        with st.spinner("Gerando…"):
            try:
                st.session_state.historia_gerada = gerar_historia(autor)
                st.session_state.autor_selecionado = autor
            except Exception as e:
                st.error(f"Erro na API do Google Gemini: {e}")
                st.session_state.historia_gerada = ""

    if st.session_state.historia_gerada:
        historia_formatada_html = st.session_state.historia_gerada.replace('\n', '<br>')
        st.markdown(f"""
        <div style="background-color: transparent; border: 1px solid #cccccc; padding: 15px; border-radius: 5px; color: #000000; font-family: 'Source Sans Pro', sans-serif; font-size: 16px; line-height: 1.6;">
            {historia_formatada_html}
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.write("Agora é a sua vez! Continue a história.")
        nome_usuario = st.text_input("Seu nome:")
        desfecho = st.text_area("Seu desfecho:", height=150)

        if st.button("Enviar e ver história completa"):
            if nome_usuario and desfecho:
                with st.spinner("Enviando seu desfecho..."):
                    worksheet = connect_to_gsheet()
                    if worksheet:
                        nova_linha = [st.session_state.autor_selecionado, nome_usuario, st.session_state.historia_gerada, desfecho]
                        worksheet.append_row(nova_linha)
                        
                        st.session_state.desfecho_usuario = desfecho
                        st.session_state.envio_concluido = True
                        st.rerun()
            else:
                st.warning("Por favor, preencha seu nome e o desfecho antes de enviar.")
else:
    st.success("Sua história foi enviada e salva com sucesso!")
    st.header("Confira a história completa:")

    texto_final = (
        st.session_state.historia_gerada + 
        "\n\n*Seu desfecho:*\n\n" + 
        f"**{st.session_state.desfecho_usuario}**"
    )
    
    st.markdown(texto_final)
    
    st.divider()

    if st.button("Escrever outra história"):
        st.session_state.historia_gerada = ""
        st.session_state.autor_selecionado = ""
        st.session_state.desfecho_usuario = ""
        st.session_state.envio_concluido = False
        st.rerun()
