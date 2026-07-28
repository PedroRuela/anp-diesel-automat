import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta

# Credenciais do Supabase
DB_URL = "postgresql://postgres.dnqhcrcnibuasnczzcmh:JvaB7vd9HEWJo5fj@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

def buscar_diesel(estado):
    """Busca preço de diesel do site"""
    try:
        # Datas
        data_fim = datetime.now().strftime('%Y-%m-%d')
        data_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # URL
        url = f"https://www.loginteli.com.br/?abrangencia=estado&local={estado}&data_inicio={data_inicio}&data_fim={data_fim}&produto=OLEO+DIESEL+S10"
        
        # Web scraping
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        elemento = soup.find('div', class_='valor')
        if elemento:
            valor_str = elemento.text.replace('R$ ', '').replace(',', '.')
            valor = float(valor_str)
            return valor
    except Exception as e:
        print(f"Erro ao buscar {estado}: {e}")
    
    return None

def salvar_no_banco(estado, valor):
    """Salva dados no Supabase"""
    if valor is None:
        return
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        data_inicio = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute(
            "INSERT INTO anp_diesel (estado, produto, data_inicio, valor_media) VALUES (%s, %s, %s, %s)",
            (estado, 'DIESEL S10', data_inicio, valor)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ {estado}: R${valor}")
    except Exception as e:
        print(f"Erro ao salvar {estado}: {e}")

# Estados para atualizar
ESTADOS = ['SP', 'MG', 'RJ', 'BA', 'RS', 'SC', 'PR']

# Executar
print("Iniciando atualização...")
for estado in ESTADOS:
    valor = buscar_diesel(estado)
    salvar_no_banco(estado, valor)

print("✓ Atualização concluída!")
