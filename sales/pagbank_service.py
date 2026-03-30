from datetime import timedelta
import uuid
import re
from decimal import Decimal, ROUND_HALF_UP
from django.utils.dateparse import parse_datetime
from django.utils import timezone

import requests
from django.conf import settings


class PagBankSandboxService:
    def __init__(self, api_token=None):
        self.api_token = api_token or settings.PAGBANK_API_TOKEN
        self.url = f"{settings.PAGBANK_SANDBOX_BASE_URL.rstrip('/')}/orders"

    def _headers(self):
        return {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "x-idempotency-key": str(uuid.uuid4()),
        }

    def _post(self, payload):
        try:
            response = requests.post(
                self.url,
                headers=self._headers(),
                json=payload,
                timeout=20,
            )
            try:
                body = response.json()
            except ValueError:
                body = {"message": response.text}
            return response.status_code, body
        except requests.RequestException as exc:
            return 500, {"message": str(exc)}

    @staticmethod
    def _digits(value):
        return re.sub(r"\D", "", str(value or ""))

    @staticmethod
    def _to_cents(value):
        normalized = Decimal(str(value or 0)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cents = int(normalized * 100)
        return cents if cents > 0 else 1

    def _build_customer_payload(self, customer):
        default_customer = {
            "name": "Comprador Sandbox",
            "email": "comprador.sandbox@gesthar.local",
            "tax_id": "03041613069",
            "phone": {"country": "55", "area": "11", "number": "999999999", "type": "MOBILE"},
            "address": {
                "street": "Avenida Paulista",
                "number": "1000",
                "postal_code": "01310923",
                "locality": "Bela Vista",
                "city": "Sao Paulo",
                "region": "SP",
                "region_code": "SP",
                "country": "Brasil",
            },
        }

        if not customer:
            return default_customer

        tax_id = self._digits(getattr(customer, "cpf_cnpj", ""))
        if len(tax_id) not in (11, 14):
            tax_id = default_customer["tax_id"]

        name = (getattr(customer, "name", "") or "").strip()[:60] or default_customer["name"]
        email = (getattr(customer, "email", "") or "").strip()[:60] or default_customer["email"]

        phone_digits = self._digits(getattr(customer, "phone", ""))
        if phone_digits.startswith("55") and len(phone_digits) > 11:
            phone_digits = phone_digits[2:]

        if len(phone_digits) >= 10:
            area = phone_digits[:2]
            number = phone_digits[2:11]
        else:
            area = default_customer["phone"]["area"]
            number = default_customer["phone"]["number"]

        address_obj = customer.addresses.first() if hasattr(customer, "addresses") else None
        if address_obj:
            postal_code = self._digits(getattr(address_obj, "cep", "")) or default_customer["address"]["postal_code"]
            city = (getattr(address_obj, "city", "") or "").strip() or default_customer["address"]["city"]
            state = (getattr(address_obj, "state", "") or "").strip().upper()[:2] or default_customer["address"]["region"]
            locality = (getattr(address_obj, "neighborhood", "") or "").strip() or default_customer["address"]["locality"]
            street = (getattr(address_obj, "street", "") or "").strip() or default_customer["address"]["street"]
            number_address = (getattr(address_obj, "number", "") or "").strip() or default_customer["address"]["number"]

            address_payload = {
                "street": street,
                "number": number_address,
                "postal_code": postal_code,
                "locality": locality,
                "city": city,
                "region": state,
                "region_code": state,
                "country": "Brasil",
            }
        else:
            address_payload = default_customer["address"]

        return {
            "name": name,
            "email": email,
            "tax_id": tax_id,
            "phone": {"country": "55", "area": area, "number": number, "type": "MOBILE"},
            "address": address_payload,
        }

    def _base_payload(self, customer_data, amount_cents, reference_id):
        return {
            "reference_id": reference_id,
            "customer": {
                "name": customer_data["name"],
                "email": customer_data["email"],
                "tax_id": customer_data["tax_id"],
                "phones": [customer_data["phone"]],
            },
            "items": [
                {
                    "reference_id": "ITEM01",
                    "name": "Venda PDV",
                    "quantity": 1,
                    "unit_amount": amount_cents,
                }
            ],
        }

    def criar_boleto(self, customer=None, amount=None):
        if not self.api_token:
            return 400, {"message": "Token do PagBank não configurado."}

        due_date = (timezone.localdate() + timedelta(days=3)).isoformat()
        reference_id = f"sandbox-{uuid.uuid4().hex[:12]}"
        customer_data = self._build_customer_payload(customer)
        amount_cents = self._to_cents(amount)

        payload = self._base_payload(customer_data, amount_cents, reference_id)
        payload["charges"] = [
            {
                "reference_id": f"charge-{reference_id}",
                "amount": {"value": amount_cents, "currency": "BRL"},
                "payment_method": {
                    "type": "BOLETO",
                    "boleto": {
                        "due_date": due_date,
                        "holder": {
                            "name": customer_data["name"],
                            "email": customer_data["email"],
                            "tax_id": customer_data["tax_id"],
                            "address": customer_data["address"],
                        },
                    },
                },
            }
        ]
        return self._post(payload)

    def criar_pix(self, customer=None, amount=None):
        if not self.api_token:
            return 400, {"message": "Token do PagBank não configurado."}

        expiration_date = (
            timezone.localdate() + timedelta(days=1)
        ).isoformat() + "T23:59:59-03:00"

        reference_id = f"sandbox-{uuid.uuid4().hex[:12]}"
        customer_data = self._build_customer_payload(customer)
        amount_cents = self._to_cents(amount)

        payload = self._base_payload(customer_data, amount_cents, reference_id)
        payload["qr_codes"] = [
            {
                "amount": {"value": amount_cents},
                "expiration_date": expiration_date,
            }
        ]
        return self._post(payload)

    @staticmethod
    def extrair_dados_boleto(response_json):
        charge = (response_json.get("charges") or [{}])[0]
        payment_method = charge.get("payment_method", {})
        boleto = payment_method.get("boleto", {})

        links = charge.get("links") or []
        pdf_link = ""
        for link in links:
            if link.get("media") == "application/pdf":
                pdf_link = link.get("href")
                break

        return {
            "order_id": response_json.get("id", ""),
            "status": charge.get("status", ""),
            "barcode": boleto.get("formatted_barcode") or boleto.get("barcode") or "",
            "pdf_url": pdf_link,
        }

    @staticmethod
    def extrair_dados_pix(response_json):
        qr_code = (response_json.get("qr_codes") or [{}])[0]
        links = qr_code.get("links") or []

        png_url = ""
        for link in links:
            href = link.get("href", "")
            media = link.get("media", "")
            if "image/png" in media or href.lower().endswith(".png"):
                png_url = href
                break

        if not png_url and links:
            png_url = links[0].get("href", "")

        return {
            "order_id": response_json.get("id", ""),
            "png_url": png_url,
            "copy_paste": qr_code.get("text", ""),
        }

    @staticmethod
    def extrair_gateway_boleto(response_json):
        charge = (response_json.get("charges") or [{}])[0]
        payment_method = charge.get("payment_method", {})
        boleto = payment_method.get("boleto", {})

        links = charge.get("links") or []
        pdf_link = ""
        for link in links:
            if link.get("media") == "application/pdf":
                pdf_link = link.get("href", "")
                break

        due_date = boleto.get("due_date") or timezone.localdate().isoformat()

        return {
            "metodo": "boleto",
            "charge_id": response_json.get("id", ""),
            "provider_payment_id": boleto.get("id", ""),
            "barcode": boleto.get("barcode", ""),
            "linha_digitavel": boleto.get("formatted_barcode", ""),
            "url_pdf": pdf_link,
            "qr_code_texto": "",
            "qr_code_base64": "",
            "url_qrcode": "",
            "data_vencimento": due_date,
            "expirado_em": None,
        }

    @staticmethod
    def extrair_gateway_pix(response_json):
        qr_code = (response_json.get("qr_codes") or [{}])[0]
        links = qr_code.get("links") or []

        url_qrcode = ""
        qr_code_base64 = ""
        for link in links:
            href = link.get("href", "")
            media = (link.get("media") or "").lower()
            if ("image/png" in media or href.lower().endswith(".png")) and not url_qrcode:
                url_qrcode = href
            elif not qr_code_base64:
                qr_code_base64 = href

        expiration_date = qr_code.get("expiration_date")
        expirado_em = parse_datetime(expiration_date) if expiration_date else None
        data_vencimento = expirado_em.date() if expirado_em else timezone.localdate()

        return {
            "metodo": "pix",
            "charge_id": response_json.get("id", ""),
            "provider_payment_id": qr_code.get("id", ""),
            "barcode": "",
            "linha_digitavel": "",
            "url_pdf": "",
            "qr_code_texto": qr_code.get("text", ""),
            "qr_code_base64": qr_code_base64,
            "url_qrcode": url_qrcode,
            "data_vencimento": data_vencimento,
            "expirado_em": expirado_em,
        }
