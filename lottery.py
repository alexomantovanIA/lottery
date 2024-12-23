import streamlit as st
import pandas as pd
import plotly.express as px
import random
from io import BytesIO
from reportlab.pdfgen import canvas

# Função para carregar e processar o arquivo Excel
def load_data(file_path):
    df = pd.read_excel(file_path, sheet_name='mega_sena_www.asloterias.com.br', engine='openpyxl', skiprows=5)
    df.columns = ['Concurso', 'Data', 'Bola 1', 'Bola 2', 'Bola 3', 'Bola 4', 'Bola 5', 'Bola 6']
    df['Concurso'] = pd.to_numeric(df['Concurso'], errors='coerce')
    df = df.dropna(subset=['Concurso'])
    df['Concurso'] = df['Concurso'].astype(int)
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce', dayfirst=True)
    return df

# Carregar os dados uma vez e calcular a frequência
data = load_data("database.xlsx")

# Frequência de números sorteados
bolas = data[['Bola 1', 'Bola 2', 'Bola 3', 'Bola 4', 'Bola 5', 'Bola 6']].values.flatten()
bolas_df = pd.DataFrame(bolas, columns=['Número'])
frequencia = bolas_df['Número'].value_counts().reset_index()
frequencia.columns = ['Número', 'Frequência']

# Configuração do título e descrição do dashboard
st.title("Mega-Sena da Virada")
st.write("Explore dados históricos, analise estratégias e gere sugestões para o próximo sorteio!")

# Inicializar session_state para controlar a página atual
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "inicio"

# Sidebar para navegação entre páginas
pagina = st.sidebar.radio(
    "Menu",
    options=["Página Inicial", "Dashboard"]
)

# Alterar a página exibida com base na escolha
if pagina == "Página Inicial":
    st.session_state.pagina_atual = "inicio"
else:
    st.session_state.pagina_atual = "dashboard"

# Escolha da fonte do arquivo
if pagina == "Dashboard":
    st.sidebar.header("Escolha a Fonte dos Dados")
    data_source = st.sidebar.radio(
        "Como deseja carregar os dados?",
        options=["Carregar Arquivo da Pasta do Projeto", "Importar Arquivo via Upload"]
    )

    # Variável para armazenar o DataFrame
    data = None

    # Opção 1: Carregar o arquivo diretamente da pasta do projeto
    if data_source == "Carregar Arquivo da Pasta do Projeto":
        file_path = "database.xlsx"
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
    
elif pagina == "Página Inicial":
    # Inicializar session_state para armazenar os jogos selecionados
    if "jogos_selecionados" not in st.session_state:
        st.session_state.jogos_selecionados = []

    # Cálculo dos jogos padrão
    st.subheader("Jogos Padrão")

    # Jogo com maior probabilidade
    jogo_maior_probabilidade = sorted(frequencia.nlargest(6, 'Frequência')['Número'].sort_values().tolist())
    st.write(f"**Jogo com maior probabilidade:** {', '.join(map(str, jogo_maior_probabilidade))}")
    if st.button("Adicionar Jogo com Maior Probabilidade"):
        if jogo_maior_probabilidade not in st.session_state.jogos_selecionados:
            st.session_state.jogos_selecionados.append(jogo_maior_probabilidade)
            st.success("Jogo com maior probabilidade adicionado!")

    # Jogo com menor probabilidade (excluindo números que nunca apareceram)
    jogo_menor_probabilidade = sorted(frequencia[frequencia['Frequência'] > 0].nsmallest(6, 'Frequência')['Número'].sort_values().tolist())
    st.write(f"**Jogo com menor probabilidade:** {', '.join(map(str, jogo_menor_probabilidade))}")
    if st.button("Adicionar Jogo com Menor Probabilidade"):
        if jogo_menor_probabilidade not in st.session_state.jogos_selecionados:
            st.session_state.jogos_selecionados.append(jogo_menor_probabilidade)
            st.success("Jogo com menor probabilidade adicionado!")

    # Exibir os jogos selecionados até agora
    st.write("**Jogos Selecionados:**")
    for i, jogo in enumerate(st.session_state.jogos_selecionados, start=1):
        st.write(f"Jogo {i}: {', '.join(map(str, jogo))}")

    # Simulação de jogos para o próximo sorteio
    st.subheader("Simulação de Números para o Próximo Sorteio")

    def gerar_numeros_simulados_unicos(frequencia, n=6):
        """Gera números simulados sem repetição com base na frequência ponderada."""
        numeros = frequencia['Número'].tolist()
        pesos = frequencia['Frequência'].tolist()
        
        # Expandir a lista de números conforme as suas frequências para criar uma distribuição ponderada
        numeros_expandidos = [numero for numero, peso in zip(numeros, pesos) for _ in range(peso)]
        
        # Garantir que há números suficientes para gerar o jogo
        if len(set(numeros_expandidos)) < n:
            raise ValueError("Não há números suficientes para gerar uma amostra única com a quantidade solicitada.")
        
        # Garantir números únicos e converter para lista antes de usar random.sample
        return sorted(random.sample(list(set(numeros_expandidos)), n))

    # Inicializar lista de jogos simulados na sessão, se ainda não existir
    if "jogos_simulados" not in st.session_state:
        st.session_state.jogos_simulados = []

    # Usuário solicita a quantidade total de jogos desejados
    qtd_jogos_desejados = st.number_input(
        "Quantos jogos você quer simular?", min_value=1, max_value=50, value=1
    )

    # Calcular a quantidade de jogos que precisa ser gerada
    qtd_jogos_existentes = len(st.session_state.jogos_simulados)
    qtd_jogos_a_gerar = max(0, qtd_jogos_desejados - qtd_jogos_existentes)

    # Gerar apenas a quantidade necessária de jogos adicionais
    for _ in range(qtd_jogos_a_gerar):
        try:
            jogo = gerar_numeros_simulados_unicos(frequencia)
            st.session_state.jogos_simulados.append(jogo)
        except ValueError as e:
            st.error(f"Erro ao gerar jogo: {str(e)}")
            break

    # Exibir todos os jogos simulados
    st.write("**Jogos Simulados:**")
    for i, jogo in enumerate(st.session_state.jogos_simulados, start=1):
        st.write(f"Jogo {i}: {', '.join(map(str, jogo))}")

    # Exportar os jogos simulados como CSV
    st.subheader("Exportar Jogos Selecionados e Simulados")

    # Combinar os jogos selecionados e simulados para exportação
    todos_jogos = st.session_state.jogos_selecionados + st.session_state.jogos_simulados

    # Criar um DataFrame para exportação
    exportar_df = pd.DataFrame(todos_jogos, columns=[f"Bola {i+1}" for i in range(6)])

    # Baixar como CSV
    csv = exportar_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar Jogos Selecionados e Simulados em CSV",
        data=csv,
        file_name='jogos_selecionados_e_simulados.csv',
        mime='text/csv',
    )

    # Baixar como PDF
    def gerar_pdf(todos_jogos_df):
        pdf_buffer = BytesIO()  # Buffer de memória para armazenar o PDF
        pdf = canvas.Canvas(pdf_buffer)

        pdf.setFont("Helvetica", 12)
        y = 800  # Coordenada Y inicial

        for index, row in todos_jogos_df.iterrows():
            numeros = ", ".join(map(str, row.tolist()))  # Converte os números da linha para string
            pdf.drawString(50, y, f"Jogo {index + 1}: {numeros}")
            y -= 20  # Move a próxima linha para baixo

            if y < 50:  # Adiciona uma nova página se o espaço acabar
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = 800

        pdf.save()
        pdf_buffer.seek(0)  # Garante que o ponteiro esteja no início do buffer
        return pdf_buffer.getvalue()

    # Configurar botão de download no Streamlit
    pdf_bytes = gerar_pdf(exportar_df)
    st.download_button(
        label="Baixar Jogos Selecionados e Simulados em PDF",
        data=pdf_bytes,
        file_name="jogos_selecionados_e_simulados.pdf",
        mime="application/pdf"
    )


    # Estratégias de seleção manual
    st.subheader("Simulação de Estratégias")
    st.write("Escolha os números manualmente para verificar frequência e probabilidade.")
    numeros_escolhidos = st.multiselect("Selecione até 6 números:", options=frequencia['Número'].sort_values(), max_selections=6)

    if len(numeros_escolhidos) > 0:
        # Filtrar frequências dos números escolhidos e remover índice
        frequencias_escolhidas = frequencia[frequencia['Número'].isin(numeros_escolhidos)].reset_index(drop=True)

        # Converter DataFrame para HTML sem índices
        html_table = frequencias_escolhidas[['Número', 'Frequência']].to_html(index=False)

        # Exibir tabela no Streamlit sem a coluna de índice
        st.markdown(html_table, unsafe_allow_html=True)

        # Gráfico das frequências dos números escolhidos
        fig2 = px.bar(frequencias_escolhidas, x='Número', y='Frequência', title="Frequência dos Números Escolhidos")
        st.plotly_chart(fig2)
