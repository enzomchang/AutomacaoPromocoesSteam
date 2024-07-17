""" AUTOMAÇÃO PARA PEGAR AS PRINCIPAIS PROMOÇÕES DA STEAM NA SEMANA E ENVIAR EM FORMA DE PLANILHA PARA O E-MAIL AUTOMATIZADO."""

""" Código agendado para executar automaticamente toda segunda feira 12:00 pelo Github Actions """

"""
Meu objetivo é pegar as seguintes informações da Steam:
Nome do Jogo
Preço Anterior do Jogo
Preço novo do Jogo
Porcentagem de Desconto
Data de Lançamento 
Url do Jogo
"""

"""
1o passo: Realizar os clickes com selenium

2o passo: Realizar o Webscraping da página

3o passo: Transformar os dados em planilha

4o passo: Configurar e-mail automático

5o passo: Agendar para executar codigo em python automaticamente (semanalmente toda segunda feira 12:00)

"""

"""

### Mudanças necessárias para cada usuário: ( Estou sinalizando no código ) ###

- Mudar de acordo com o e-mail que você quer que receba as promoções

- Mudar o caminho do dataframe que será salvo para enviar por anexo

- Agendar a tarefa de acordo com o que você quer que seja realizado o webscraping

"""

##############################
### Instalações Essenciais ###
##############################

# pip install pandas
# pip install selenium
# pip install webdriver-manager
# pip install scrapy
# pip install schedule

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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os

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

# Enviar o arquivo por email usando SMTP
def enviar_email():
    tabela_html = criar_tabela_html(df)
    fromaddr = os.getenv('EMAIL_USER')
    toaddr = os.getenv('EMAIL_TO') # Mudar de acordo com o e-mail que você quer que receba as promoções
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Promoções Semanais da Steam"

    body = f"""
    <p>Olá,</p>
    <p>Segue o relatório atualizado das promoções semanais da Steam na planilha em anexo e na tabela abaixo:</p>
    {tabela_html}
    """
    msg.attach(MIMEText(body, 'html'))

    filename = output_path
    attachment = open(filename, "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename= {filename.split("/")[-1]}')

    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, os.getenv('EMAIL_PASS'))
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
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

# Salvar o DataFrame em um arquivo Excel
df.to_excel(output_path, index=False)

# Chamar Função enviar e-mail
enviar_email()
