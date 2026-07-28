import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta

DB_URL = "postgresql://postgres.dnqhcrcnibuasnczzcmh:JvaB7vd9HEWJo5fj@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

ESTADOS = ['SP', 'MG', 'RJ', 'BA', 'RS', 'SC', 'PR', 'GO', 'MT', 'PE', 'ES', 'CE']

def buscar_diesel(estado, data_inicio, data_fim):
    """Busca preço de diesel do site para um período específico"""
    try:
        url = f"https://www.loginteli.com.br/?abrangencia=estado&local={estado}&data_inicio={data_inicio}&data_fim={data_fim}&produto=OLEO+DIESEL+S10"
        
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        elemento = soup.find('div', class_='valor')
        
        if elemento:
            valor_str = elemento.text.strip().replace('R$ ', '').replace(',', '.')
            return float(valor_str)
    except Exception as e:
        print(f"Erro ao buscar {estado} ({data_inicio} a {data_fim}): {e}")
    
    return None

def upsert_no_banco(estado, data_inicio, valor):
    """Insere ou atualiza (upsert) no Supabase"""
    if valor is None:
        return
    
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        semana_ano = data_inicio.strftime('%G-%V')  # formato ISO: ano-semana
        
        cursor.execute("""
            INSERT INTO anp_diesel (estado, produto, data_inicio, valor_media, semana_ano)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (estado, semana_ano)
            DO UPDATE SET valor_media = EXCLUDED.valor_media, data_atualizacao = CURRENT_TIMESTAMP
        """, (estado, 'DIESEL S10', data_inicio.strftime('%Y-%m-%d'), valor, semana_ano))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ {estado} | Semana {semana_ano}: R${valor}")
    except Exception as e:
        print(f"Erro ao salvar {estado}: {e}")

# Executar: buscar últimas 8 semanas para cada estado
print("Iniciando atualização (últimas 8 semanas)...")

for semanas_atras in range(8):
    data_fim = datetime.now() - timedelta(weeks=semanas_atras)
    data_inicio = data_fim - timedelta(days=6)
    
    for estado in ESTADOS:
        valor = buscar_diesel(
            estado, 
            data_inicio.strftime('%Y-%m-%d'), 
            data_fim.strftime('%Y-%m-%d')
        )
        upsert_no_banco(estado, data_inicio, valor)

print("✓ Atualização concluída!")
