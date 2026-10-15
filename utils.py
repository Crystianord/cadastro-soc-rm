import re
import xml.dom.minidom

import pandas as pd


def padronizar_data(data_str):
    if not data_str:
        return None
    return pd.to_datetime(data_str, utc=True).strftime("%Y-%m-%d")


def limpar_cpf(cpf):
    return re.sub(r"\D", "", str(cpf))


def limpar_telefone(telefone):
    if not telefone:
        return ""
    return re.sub(r"\D", "", str(telefone))


def formatar_data_soc(data_iso):
    """Converte data 'YYYY-MM-DDThh:mm...' para 'DD/MM/YYYY'."""
    if not data_iso:
        return ""
    try:
        data_apenas = data_iso.split("T")[0]
        ano, mes, dia = data_apenas.split("-")
        return f"{dia}/{mes}/{ano}"
    except Exception as e:
        print(f"Erro ao formatar a data '{data_iso}': {e}")
        return ""


def print_debug_response(response):
    print("\n--- DEBUG RESPONSE ---")
    print(f"Status Code: {response.status_code}")

    if response.text and response.text.strip().startswith("<"):
        try:
            dom = xml.dom.minidom.parseString(response.text)
            print("Conteúdo formatado (XML):")
            print(dom.toprettyxml())
        except Exception:
            print("Conteúdo bruto (XML não pôde ser formatado):")
            print(response.text)
    else:
        print("Conteúdo (Texto/JSON):")
        print(response.text)
    print("----------------------\n")
