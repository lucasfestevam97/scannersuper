import streamlit as st
import pandas as pd
import cv2
from pyzbar.pyzbar import decode
import numpy as np

# Configuração da página do App
st.set_page_config(page_title="Scanner de Preços", page_icon="🛒", layout="centered")
st.title("🛒 Protótipo: Scanner de Supermercado")

# 1. CARREGAR O BANCO DE DADOS (Seu arquivo Excel)
@st.cache_data
def carregar_dados():
    try:
        # Lê a planilha que seu scraper gerou
        df = pd.read_excel('banco_de_dados_app.xlsx')
        # Garante que o código de barras seja tratado como texto/string
        df['Código de Barras'] = df['Código de Barras'].astype(str)
        return df
    except Exception:
        st.error("Erro: Não encontrei o arquivo 'banco_de_dados_app.xlsx'. Verifique a pasta.")
        return pd.DataFrame(columns=["Nome", "Preço (R$)", "Código de Barras"])

df_produtos = carregar_dados()

# 2. INICIALIZAR O CARRINHO DE COMPRAS na memória do app
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

# 3. INTERFACE: SCANNER DE CÓDIGO DE BARRAS
st.header("📸 Escanear Produto")
# Ativa a câmera integrada do dispositivo
imagem_camera = st.camera_input("Aponte o código de barras para a câmera")

codigo_detectado = None

if imagem_camera:
    # Converte a foto da câmera para um formato que o Python entende (OpenCV)
    bytes_data = imagem_camera.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    # Tenta decodificar códigos de barras na imagem
    codigos = decode(cv2_img)
    
    if codigos:
        codigo_detectado = codigos[0].data.decode('utf-8')
        st.success(f"Código detectado com sucesso: **{codigo_detectado}**")
    else:
        st.warning("Nenhum código de barras nítido foi detectado. Tente aproximar ou focar melhor.")

# --- CAMPO MANUAL PARA TESTES ---
# Se a câmera falhar no computador, você pode digitar o código (ex: 2253) para testar o app
codigo_manual = st.text_input("Ou digite o código manualmente para testar:")
if codigo_manual:
    codigo_detectado = codigo_manual.strip()

# 4. BUSCA NO BANCO DE DADOS E OPÇÃO DE ADICIONAR
if codigo_detectado:
    # Procura o código correspondente na tabela
    produto_encontrado = df_produtos[df_produtos['Código de Barras'] == str(codigo_detectado)]
    
    if not produto_encontrado.empty:
        # Extrai as informações se o produto existir
        nome_prod = produto_encontrado.iloc[0]['Nome']
        preco_base = float(produto_encontrado.iloc[0]['Preço (R$)'])
        
        st.info(f"**Produto Localizado:** {nome_prod}")
        
        # Campo para o usuário confirmar ou alterar o preço (caso tenha mudado na gôndola)
        preco_final = st.number_input("Confirmar preço unitário (R$):", value=preco_base, step=0.01)
        quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1)
        
        if st.button("➕ Adicionar ao Carrinho"):
            # Adiciona o item ao carrinho temporário
            st.session_state.carrinho.append({
                "Nome": nome_prod,
                "Preço Un.": preco_final,
                "Qtd": quantidade,
                "Total": preco_final * quantidade
            })
            st.toast(f"{nome_prod} adicionado!")
    else:
        st.error("Produto não cadastrado no banco de dados do app.")
        # Opção de cadastrar um produto novo na hora se quiser
        novo_nome = st.text_input("Nome do produto novo:")
        novo_preco = st.number_input("Preço do produto novo:", min_value=0.0, step=0.1)
        if st.button("📝 Cadastrar e Adicionar"):
            st.session_state.carrinho.append({
                "Nome": novo_nome,
                "Preço Un.": novo_preco,
                "Qtd": 1,
                "Total": novo_preco
            })

# 5. EXIBIÇÃO DO CARRINHO DE COMPRAS E VALOR TOTAL
st.write("---")
st.header("🛒 Seu Carrinho de Compras")

if st.session_state.carrinho:
    # Transforma o carrinho em tabela para mostrar na tela
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.dataframe(df_carrinho, use_container_width=True)
    
    # Calcula a soma total de todos os produtos adicionados
    valor_total_compra = df_carrinho['Total'].sum()
    
    # Destaca o valor final na tela
    st.metric(label="VALOR FINAL DA COMPRA", value=f"R$ {valor_total_compra:.2f}")
    
    if st.button("🗑️ Limpar Carrinho"):
        st.session_state.carrinho = []
        st.rerun()
else:
    st.write("*Seu carrinho está vazio. Escaneie um produto para começar!*")