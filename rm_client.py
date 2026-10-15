import ssl

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.ssl_ import create_urllib3_context

from config import URL_RM_REST, REST_USER, REST_PASS
from utils import limpar_cpf, padronizar_data


class LegacySSLAdapter(HTTPAdapter):
    """Alguns servidores TOTVS RM on-premise só aceitam cifras TLS legadas."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


def criar_sessao_rm():
    session = requests.Session()
    session.mount("https://", LegacySSLAdapter())
    return session


def buscar_funcionarios_rm():
    """Consulta o RM, remove contratos PJ e deduplica por CPF + data de admissão
    (mantendo sempre o vínculo ativo ou o mais recente)."""
    session = criar_sessao_rm()

    try:
        response = session.get(URL_RM_REST, auth=HTTPBasicAuth(REST_USER, REST_PASS), verify=False)
        response.raise_for_status()

        lista_funcionarios_bruta = response.json()
        print(f"Sucesso! {len(lista_funcionarios_bruta)} registros brutos encontrados.")

        funcionarios_unicos = {}

        for func in lista_funcionarios_bruta:
            cod_tipo = str(func.get("CODTIPO", "")).strip().upper()
            if cod_tipo == "A":
                continue  # ignora contratos PJ

            cpf_chave = limpar_cpf(func.get("CPF", ""))
            data_adm_chave = padronizar_data(func.get("DATAADMISSAO", ""))
            chave = (cpf_chave, data_adm_chave)

            if chave not in funcionarios_unicos:
                funcionarios_unicos[chave] = func
                continue

            func_salvo = funcionarios_unicos[chave]
            demissao_atual_str = func.get("DATADEMISSAO")
            demissao_salvo_str = func_salvo.get("DATADEMISSAO")

            if not demissao_atual_str or str(demissao_atual_str).strip() == "":
                funcionarios_unicos[chave] = func
            elif not demissao_salvo_str or str(demissao_salvo_str).strip() == "":
                continue
            else:
                try:
                    import pandas as pd

                    dem_atual_dt = pd.to_datetime(demissao_atual_str, utc=True)
                    dem_salvo_dt = pd.to_datetime(demissao_salvo_str, utc=True)
                    if dem_atual_dt > dem_salvo_dt:
                        funcionarios_unicos[chave] = func
                except Exception as e:
                    print(f"Aviso: erro ao comparar datas de demissão do CPF {cpf_chave}: {e}")

        lista_funcionarios = list(funcionarios_unicos.values())
        print(f"Após filtros (remoção de PJ e deduplicação), restaram {len(lista_funcionarios)} registros únicos.")
        return lista_funcionarios

    except requests.exceptions.HTTPError as err:
        print(f"Erro de autenticação ou HTTP: {err}")
        return []
    except Exception as e:
        print(f"Erro inesperado ao consultar o RM: {e}")
        return []
