####################################################################################################################################
##### AUTOMAÇÃO PARA PEGAR AS PRINCIPAIS PROMOÇÕES DA STEAM NA SEMANA E ENVIAR EM FORMA DE PLANILHA PARA O E-MAIL AUTOMATIZADO #####
####################################################################################################################################

""" Código agendado para executar automaticamente toda segunda feira 12:00 pelo *Github Actions* """

### SECRETS QUE PRECISARÃO SER DEFINIDAS PELO USUÁRIO ###
"""
EMAIL_USER=seu_email@outlook.com
EMAIL_TO=destinatario@example.com
OUTPUT_PATH=outputs/promocoes_steam.xlsx
SENDGRID_API_KEY=SG.seu_sendgrid_api_key
"""

"""
Meu objetivo é pegar as seguintes informações da Steam:
* Nome do Jogo
* Preço Anterior do Jogo
* Preço novo do Jogo
* Porcentagem de Desconto
* Data de Lançamento 
* Url do Jogo
"""

"""
1o passo: Realizar os clickes com selenium

2o passo: Realizar o Webscraping da página

3o passo: Transformar os dados em planilha

4o passo: Configurar e-mail automático

5o passo: Agendar para executar codigo em python automaticamente (semanalmente toda segunda feira 12:00)

"""

##############################
### Instalações Essenciais ###
##############################

# pip install pandas
# pip install selenium
# pip install webdriver-manager
# pip install scrapy
# pip install schedule
# pip install sendgrid
# pip install openpyxl

##############################
### Bibliotecas Essenciais ###
##############################

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import time
import os
import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import openpyxl

""" DESCOMENTAR SE FOR TESTAR LOCALMENTE COM UM ARQUIVO .env"""
#from dotenv import load_dotenv
# Carregar variáveis de ambiente do arquivo .env
#load_dotenv()

# Verificar se as variáveis estão carregadas
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_TO = os.getenv('EMAIL_TO')
OUTPUT_PATH = os.getenv('OUTPUT_PATH')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

# Garantir que o diretório de saída exista
output_dir = os.path.dirname(OUTPUT_PATH)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

##############################
###### Funções Projeto #######
##############################

# Para fazer o download do webdriver chamado chromedriver para integrar o python com o navegador google chrome de forma dinâmica, vou utilizar o webdriver-manager:

""" Abrir o Navegador """

# Instalando o ChromeDriverManager (identificando automaticamente a versão do google drive atual)
servico = Service(ChromeDriverManager().install())

# Utilizando o webdriver instalado
navegador = webdriver.Chrome(service=servico)

# Abrindo o Site da Steam (já na aba de promoções)
navegador.get("https://store.steampowered.com/specials#tab=TopSellers")

# Esperando para carregar a página
time.sleep(5)

# Definindo o dicionário para armazenar os dados
dic_produtos = {'nome_jogo': [], 'preco_anterior': [], 'preco_novo': [], 'desconto': [], 'data_lancamento': [], 'url_jogo': []}
count = 0
limite = 150 # Limitando a quantidade de jogos para pegar apenas os 150 primeiros

# Webscraping da página para pegar os dados das promoções
# Função para rolar a página até o final e clicar no botão "Exibir mais" se disponível
def rolar_e_carregar_mais():
    global count
    while count < limite:
        try:
            # Rolar até o fim da página
            navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Tentar encontrar e clicar no botão "Exibir mais"
            botao_exibir_mais = navegador.find_element(By.XPATH, '//button[text()="Exibir mais"]')
            botao_exibir_mais.click()
            time.sleep(5)  # Esperar carregar novos elementos
        except NoSuchElementException:
            # Se o botão "Exibir mais" não for encontrado, sair do loop
            break
        except ElementClickInterceptedException:
            # Se o clique no botão for interceptado, tentar novamente
            time.sleep(2)

        # Coletar os elementos de promoção
        produtos = navegador.find_elements(By.CLASS_NAME, 'v9uRg57bwOaPsvAnkXESO')

        # Iterar sobre os produtos para coletar os dados
        for produto in produtos[count:]:
            if count >= limite:
                break
            try:
                nome_jogo = produto.find_element(By.CLASS_NAME, 'StoreSaleWidgetTitle').text
                preco_anterior = produto.find_element(By.CLASS_NAME, '_3fFFsvII7Y2KXNLDk_krOW').text
                preco_novo = produto.find_element(By.CLASS_NAME, '_3j4dI1yA7cRfCvK8h406OB').text
                desconto = produto.find_element(By.CLASS_NAME, 'cnkoFkzVCby40gJ0jGGS4').text
                data_lancamento = produto.find_element(By.CLASS_NAME, '_1qvTFgmehUzbdYM9cw0eS7').text
                url_jogo = produto.find_element(By.TAG_NAME, 'a').get_attribute('href')

                # Verificar se os dados não estão vazios antes de adicioná-los ao dicionário
                if all([nome_jogo, preco_anterior, preco_novo, desconto, data_lancamento, url_jogo]):
                    dic_produtos['nome_jogo'].append(nome_jogo)
                    dic_produtos['preco_anterior'].append(preco_anterior)
                    dic_produtos['preco_novo'].append(preco_novo)
                    dic_produtos['desconto'].append(desconto)
                    dic_produtos['data_lancamento'].append(data_lancamento)
                    dic_produtos['url_jogo'].append(url_jogo)
                    
                    count += 1
            except Exception as e:
                print(f"Erro ao coletar dados do produto: {e}")

# Criar uma tabela HTML para o corpo do e-mail
def criar_tabela_html(df):
    tabela_html = """
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th>Nome do Jogo</th>
            <th>Preço Anterior</th>
            <th>Preço Novo</th>
            <th>Desconto</th>
            <th>Data de Lançamento</th>
            <th>URL do Jogo</th>
        </tr>
    """
    for index, row in df.iterrows():
        tabela_html += f"""
        <tr>
            <td>{row['nome_jogo']}</td>
            <td>{row['preco_anterior']}</td>
            <td>{row['preco_novo']}</td>
            <td>{row['desconto']}</td>
            <td>{row['data_lancamento']}</td>
            <td><a href="{row['url_jogo']}">Link</a></td>
        </tr>
        """
    tabela_html += "</table>"
    return tabela_html

# Enviar o arquivo por email usando SendGrid
def enviar_email():
    tabela_html = criar_tabela_html(df)
    sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
    from_email = os.getenv('EMAIL_USER')
    to_email = os.getenv('EMAIL_TO')
    subject = "Promoções Semanais da Steam"
    content = f"""
    <p>Olá,</p>
    <p>Segue o relatório atualizado das promoções semanais da Steam na planilha em anexo e na tabela abaixo:</p>
    {tabela_html}
    """
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    with open(OUTPUT_PATH, 'rb') as f:
        file_data = f.read()
        encoded_file = base64.b64encode(file_data).decode()

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName('promocoes_steam.xlsx'),
        FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        Disposition('attachment')
    )
    message.attachment = attachedFile
    sg.send(message)
    print("Email enviado!")

##############################
##### Programa Principal #####
##############################

# Chamar a função para rolar e carregar mais itens
rolar_e_carregar_mais()

# Fechar o navegador
navegador.quit()

# Converter o dicionário para um DataFrame do Pandas
df = pd.DataFrame(dic_produtos)

# Obter o caminho de saída da variável de ambiente
output_path = os.getenv('OUTPUT_PATH')

# Garantir que o diretório de saída exista
output_dir = os.path.dirname(output_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Verificar se o caminho de saída está correto
print(f"Salvando o arquivo em: {output_path}")

# Salvar o DataFrame em um arquivo Excel
df.to_excel(output_path, index=False, engine='openpyxl')

# Chamar Função enviar e-mail
enviar_email()
