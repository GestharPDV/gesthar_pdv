import os
import requests
import json
from dotenv import load_dotenv

# 1. Carrega as variáveis do seu arquivo .env
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# --- AJUSTE ESTES VALORES ---
STORE_ID_MP = 82183682  # O ID numérico do Mercado Pago
EXTERNAL_STORE_ID = "loja_1" # O external_id que você deu para a loja
# ----------------------------

url = "https://api.mercadopago.com/pos"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# Dados do Caixa para a Linda Gestante
payload = {
    "name": "Caixa Principal Linda Gestante",
    "store_id": STORE_ID_MP,        # ID da loja no Mercado Pago
    "external_store_id": EXTERNAL_STORE_ID, # Seu ID de controle da loja
    "external_id": "CAIXA01",           # Seu ID de controle para este caixa
    "fixed_amount": True,
}

def criar_caixa():
    try:
        print(f"Criando caixa para a loja {STORE_ID_MP}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("\n✅ Caixa criado com sucesso!")
            print(f"ID do Caixa (Mercado Pago): {data.get('id')}")
            print(f"Nome do Caixa: {data.get('name')}")
            print("-" * 30)
            print("PRÓXIMO PASSO:")
            print("Agora você deve ligar o seu terminal Point e associá-lo a este caixa.")
        else:
            print(f"\n❌ Erro ao criar caixa: {response.status_code}")
            print(f"Detalhes: {response.text}")
            
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    criar_caixa()