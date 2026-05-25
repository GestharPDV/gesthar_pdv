import os
import requests
import json
from dotenv import load_dotenv

# 1. Carrega as variáveis do seu arquivo .env
load_dotenv()

USER_ID = os.getenv("USER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Validação simples das credenciais
if not USER_ID or not ACCESS_TOKEN:
    print("Erro: USER_ID ou ACCESS_TOKEN não encontrados no arquivo .env")
    exit()

# 2. Configuração do Endpoint e Headers
url = f"https://api.mercadopago.com/users/{USER_ID}/stores"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 3. Dados da Linda Gestante
payload = {
    "name": "Linda Gestante",
    "external_id": "loja_1",
    "business_hours": {
        "monday": [{"open": "08:00", "close": "19:00"}],
        "tuesday": [{"open": "08:00", "close": "19:00"}],
        "wednesday": [{"open": "08:00", "close": "19:00"}],
        "thursday": [{"open": "08:00", "close": "19:00"}],
        "friday": [{"open": "08:00", "close": "19:00"}],
        "saturday": [{"open": "08:00", "close": "18:00"}]
    },
    "location": {
        "street_number": "438",
        "street_name": "Rua Armando Burlamaque",
        "city_name": "Parnaíba",
        "state_name": "Piauí",
        "latitude": -2.9148395022221756,
        "longitude": -41.767357369384875,
        "reference": "São Francisco da Guarita"
    }
}

def criar_loja():
    try:
        print(f"Enviando requisição para o USER_ID: {USER_ID}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Verifica se a requisição foi bem sucedida
        if response.status_code in [200, 201]:
            data = response.json()
            print("\n✅ Loja criada com sucesso!")
            print(f"ID da Loja (Mercado Pago): {data.get('id')}")
            print(f"Nome: {data.get('name')}")
            print("-" * 30)
            print("Guarde esse ID da Loja, vamos precisar dele para criar o CAIXA.")
        else:
            print(f"\n❌ Erro ao criar loja: {response.status_code}")
            print(f"Detalhes: {response.text}")
            
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    criar_loja()