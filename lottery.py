import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import random
import datetime
from io import BytesIO
from fpdf import FPDF
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

# Função para carregar e processar o arquivo Excel
def load_data(file_path):
    df = pd.read_excel(file_path, sheet_name='mega_sena_www.asloterias.com.br', engine='openpyxl', skiprows=5)
    df.columns = ['Concurso', 'Data', 'Bola 1', 'Bola 2', 'Bola 3', 'Bola 4', 'Bola 5', 'Bola 6']
    df['Concurso'] = pd.to_numeric(df['Concurso'], errors='coerce')
    df = df.dropna(subset=['Concurso'])
    df['Concurso'] = df['Concurso'].astype(int)
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    return df

# Função para processar os dados e criar variáveis binárias para Machine Learning
def processar_dados_ml(df):
    cols = ['Bola 1', 'Bola 2', 'Bola 3', 'Bola 4', 'Bola 5', 'Bola 6']
    # Criar colunas binárias indicando a presença de cada número nos sorteios
    for i in range(1, 61):
        df[f"Num_{i}"] = df[cols].apply(lambda row: 1 if i in row.values else 0, axis=1)
    return df.drop(columns=cols)

# Função de treinamento e previsão de Machine Learning
def modelo_previsao(df):
    X = df.drop(columns=['Concurso'])  # Remover a coluna Concurso, pois ela não é relevante para a previsão
    X = X.astype(int)  # Garantir que todas as colunas sejam inteiras (binárias)

    # Criar rótulos (y) com base na presença dos números sorteados
    # Exemplo simples: Para cada número, preveja a probabilidade de ele aparecer no próximo concurso.
    # Aqui, estamos apenas usando a soma dos números sorteados como exemplo.
    y = X.shift(-1, axis=0).sum(axis=1)  # Usamos a soma dos números sorteados no próximo concurso como rótulo

    # Remover a última linha de 'y' porque não temos rótulo para ela
    X = X[:-1]
    y = y[:-1]

    # Divisão dos dados em treinamento e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Treinar o modelo de árvore de decisão
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)

    # Fazer previsões
    y_pred = model.predict(X_test)

    # Calcular precisão
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy

# Função de previsão dos próximos números
def prever_numeros(modelo, df):
    # Remover a coluna 'Concurso' e 'Data', mas garantir que todas as colunas numéricas sejam mantidas
    df_ml = df.drop(columns=['Concurso', 'Data'])
    
    # Verifique as colunas em df_ml e no modelo treinado
    print(f"Colunas em df_ml: {df_ml.columns}")
    print(f"Modelo espera {modelo.n_features_in_} características.")
    
    # Verificar se o número de colunas coincide com o número esperado pelo modelo
    if df_ml.shape[1] != modelo.n_features_in_:
        print(f"Erro: número de colunas em df_ml ({df_ml.shape[1]}) não coincide com o esperado pelo modelo ({modelo.n_features_in_}).")
        # Aqui, adicione um código para ajustar as colunas conforme necessário
        return None

    # Certificar-se de que estamos apenas passando dados numéricos para o modelo
    X = df_ml.astype(int)
    
    # Prevendo para o último concurso
    pred = modelo.predict([X.iloc[-1].values])  # Prevendo para o último concurso
    return pred

# Configuração do título e descrição do dashboard
st.title("Dashboard Avançado da Mega-Sena")
st.write("Explore dados históricos, analise estratégias e gere sugestões para o próximo sorteio!")

# Escolha da fonte do arquivo
st.sidebar.header("Escolha a Fonte dos Dados")
data_source = st.sidebar.radio(
    "Como deseja carregar os dados?",
    options=["Carregar Arquivo da Pasta do Projeto", "Importar Arquivo via Upload"]
)

# Variável para armazenar o DataFrame
data = None

# Opção 1: Carregar o arquivo diretamente da pasta do projeto
if data_source == "Carregar Arquivo da Pasta do Projeto":
    file_path = "mega_sena_asloterias_ate_concurso_2805_crescente.xlsx"
    try:
        data = load_data(file_path)
        st.success(f"Arquivo carregado com sucesso da pasta: {file_path}")
    except FileNotFoundError:
        st.error("Arquivo não encontrado na pasta do projeto. Certifique-se de que o arquivo está no local correto.")

# Opção 2: Importar via upload no Streamlit
elif data_source == "Importar Arquivo via Upload":
    uploaded_file = st.file_uploader("Escolha o arquivo .xlsx", type=["xlsx"])
    if uploaded_file is not None:
        data = load_data(uploaded_file)
        st.success("Arquivo carregado com sucesso via upload!")

# Processar os dados se estiverem disponíveis
if data is not None:
    # Filtros Interativos
    st.sidebar.header("Filtros")
    min_concurso = st.sidebar.number_input("Concurso Inicial", min_value=int(data['Concurso'].min()), max_value=int(data['Concurso'].max()), value=int(data['Concurso'].min()))
    max_concurso = st.sidebar.number_input("Concurso Final", min_value=int(data['Concurso'].min()), max_value=int(data['Concurso'].max()), value=int(data['Concurso'].max()))
    start_date = st.sidebar.date_input("Data Inicial", value=data['Data'].min())
    end_date = st.sidebar.date_input("Data Final", value=data['Data'].max())

    # Aplicar filtros
    data_filtered = data[
        (data['Concurso'] >= min_concurso) & 
        (data['Concurso'] <= max_concurso) & 
        (data['Data'] >= pd.to_datetime(start_date)) & 
        (data['Data'] <= pd.to_datetime(end_date))
    ]
    st.write(f"Exibindo resultados do concurso {min_concurso} ao {max_concurso} entre {start_date} e {end_date}.")
    st.dataframe(data_filtered)

    # Frequência de números sorteados
    bolas = data_filtered[['Bola 1', 'Bola 2', 'Bola 3', 'Bola 4', 'Bola 5', 'Bola 6']].values.flatten()
    bolas_df = pd.DataFrame(bolas, columns=['Número'])
    frequencia = bolas_df['Número'].value_counts().reset_index()
    frequencia.columns = ['Número', 'Frequência']

    st.subheader("Frequência de Cada Número")
    fig1 = px.bar(frequencia, x='Número', y='Frequência', title="Números Mais Sorteados")
    st.plotly_chart(fig1)

    # Simulação de jogos para o próximo sorteio
    st.subheader("Simulação de Números para o Próximo Sorteio")
    
    def gerar_numeros_simulados(frequencia, n=6):
        """Gera números simulados com base na frequência ponderada"""
        numeros = frequencia['Número'].tolist()
        pesos = frequencia['Frequência'].tolist()
        return random.choices(numeros, weights=pesos, k=n)

    # Usuário solicita a quantidade de jogos
    qtd_jogos = st.number_input("Quantos jogos você quer simular?", min_value=1, max_value=50, value=1)
    simulados = [sorted(gerar_numeros_simulados(frequencia)) for _ in range(qtd_jogos)]
    for i, jogo in enumerate(simulados):
        st.write(f"Jogo {i + 1}: {', '.join(map(str, jogo))}")
    
    # Exportar os jogos simulados como CSV
    st.subheader("Exportar Jogos Simulados")
    
    simulados_df = pd.DataFrame(simulados, columns=[f"Bola {i+1}" for i in range(6)])
    
    # Baixar como CSV
    csv = simulados_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar Jogos em CSV",
        data=csv,
        file_name='jogos_simulados.csv',
        mime='text/csv',
    )

    # Função para gerar o PDF
    def gerar_pdf(df):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)  # Configurar quebra automática de página
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Adicionar cabeçalho
        pdf.cell(200, 10, txt="Jogos Simulados - Mega-Sena", ln=True, align='C')

        # Adicionar os jogos simulados
        for index, row in df.iterrows():
            linha = f"Jogo {index + 1}: {', '.join(map(str, row.values))}"
            pdf.cell(0, 10, txt=linha, ln=True)  # Escreve cada jogo no PDF

        # Gravar o conteúdo no buffer de memória
        pdf_output = BytesIO()
        pdf.output(pdf_output)  # Aqui passamos o buffer de memória
        pdf_output.seek(0)  # Garante que o ponteiro está no início do buffer

        return pdf_output.getvalue()  # Retorna os bytes do PDF gerado

    pdf_bytes = gerar_pdf(simulados_df)
    st.download_button(
        label="Baixar Jogos em PDF",
        data=pdf_bytes,
        file_name="jogos_simulados.pdf",
        mime="application/pdf",
    )

    # Treinamento do modelo ML
    df_ml = processar_dados_ml(data_filtered)
    modelo, accuracy = modelo_previsao(df_ml)

    st.write(f"Precisão do modelo de Machine Learning: {accuracy:.2f}")

    # Previsão dos próximos números
    numeros_previstos = prever_numeros(modelo, df_ml)

    # Verificar se a previsão retornou None
    if numeros_previstos is None:
        st.write("Erro ao prever os próximos números. Verifique os dados de entrada.")
    else:
        st.write(f"Os próximos números previstos pelo modelo são: {', '.join(map(str, numeros_previstos))}")

    # Estratégias de seleção manual
    st.subheader("Simulação de Estratégias")
    st.write("Escolha os números manualmente para verificar frequência e probabilidade.")
    numeros_escolhidos = st.multiselect("Selecione até 6 números:", options=frequencia['Número'].sort_values(), max_selections=6)

    if len(numeros_escolhidos) > 0:
        frequencias_escolhidas = frequencia[frequencia['Número'].isin(numeros_escolhidos)]
        st.write(frequencias_escolhidas)

        # Gráfico das frequências dos números escolhidos
        fig2 = px.bar(frequencias_escolhidas, x='Número', y='Frequência', title="Frequência dos Números Escolhidos")
        st.plotly_chart(fig2)
