import base64
import hashlib
import html
import secrets
from datetime import datetime, timedelta

import pprint
import xmltodict

from config import SOC_CODIGO, SOC_CHAVE, URL_SOC_SOAP_CONSULTA
from utils import limpar_cpf, padronizar_data, print_debug_response


def get_soap_security(username, password):
    """Gera os tokens de segurança WS-Security necessários para o SOC."""
    created = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    expires = (datetime.utcnow() + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

    nonce_raw = secrets.token_bytes(16)
    nonce_base64 = base64.b64encode(nonce_raw).decode("utf-8")

    sha1 = hashlib.sha1()
    sha1.update(nonce_raw + created.encode("utf-8") + password.encode("utf-8"))
    password_digest = base64.b64encode(sha1.digest()).decode("utf-8")

    return {
        "created": created,
        "expires": expires,
        "nonce": nonce_base64,
        "digest": password_digest,
        "username": username,
    }


def carregar_base_soc(session, empresa):
    """Consulta a base de funcionários pendentes/ativos de uma empresa no SOC."""
    params_dict = {
        "empresa": empresa,
        "codigo": SOC_CODIGO,
        "chave": SOC_CHAVE,
        "tipoSaida": "xml",
        "setor": "todos",
        "empresaTrabalho": empresa,
        "parametroData": "false",
        "dataInicio": "",
        "dataFim": "",
    }
    params_str = str(params_dict).replace("'", "'").replace(" ", "")

    xml_full = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://services.soc.age.com/">
   <soapenv:Header/>
   <soapenv:Body>
      <ser:exportaDadosWs>
         <arg0>
            <parametros>{params_str}</parametros>
         </arg0>
      </ser:exportaDadosWs>
   </soapenv:Body>
</soapenv:Envelope>"""

    headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""}

    response = session.post(URL_SOC_SOAP_CONSULTA, data=xml_full.encode("utf-8"), headers=headers, verify=False)
    print(f"Status Code: {response.status_code}")

    base_soc_local = {}

    if response.status_code != 200:
        print(f"Erro: {response.text}")
        return base_soc_local

    print_debug_response(response)

    dados_soap = xmltodict.parse(response.text)
    pprint.pprint(dados_soap)
    xml_interno_string = dados_soap["soap:Envelope"]["soap:Body"]["ns2:exportaDadosWsResponse"]["return"]["retorno"]
    xml_real = html.unescape(xml_interno_string)
    dados_internos = xmltodict.parse(xml_real)
    registros = dados_internos["root"]["record"]
    if not isinstance(registros, list):
        registros = [registros]

    for reg in registros:
        raw_cpf = reg.get("CPFFUNCIONARIO")
        raw_data = reg.get("DATA_ADMISSAO")
        raw_situacao = reg.get("NOVASITUACAO")
        raw_nome = reg.get("NOME")

        if raw_situacao and raw_situacao.strip().lower() == "pendente":
            if raw_cpf and raw_nome:
                cpf_limpo = limpar_cpf(raw_cpf)
                nome = raw_nome.strip().upper()
                data_limpa = padronizar_data(raw_data)
                reg["cpf_limpo"] = cpf_limpo
                reg["nome_limpo"] = nome
                reg["data_limpa"] = data_limpa
                reg["empresa"] = empresa
                base_soc_local[(cpf_limpo, nome)] = reg
            else:
                mensagem = reg.get("mensagemRetorno", "Registro inválido ou vazio com situação Pendente")
                print(f"Aviso para empresa {empresa}: {mensagem}")
            continue

        print(f"Registro para {raw_nome} com situação '{raw_situacao}' ignorado (não é Pendente).")

        if raw_cpf and raw_data:
            cpf_limpo = limpar_cpf(raw_cpf)
            data_limpa = padronizar_data(raw_data)
            nome = raw_nome.strip().upper()
            reg["cpf_limpo"] = cpf_limpo
            reg["data_limpa"] = data_limpa
            reg["nome_limpo"] = nome
            reg["empresa"] = empresa
            base_soc_local[(cpf_limpo, data_limpa)] = reg
        else:
            mensagem = reg.get("mensagemRetorno", "Registro inválido ou vazio")
            print(f"Aviso para empresa {empresa}: {mensagem}")

    return base_soc_local
