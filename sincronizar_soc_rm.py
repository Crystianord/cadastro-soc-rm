import re
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import requests

from config import USER_SOC, PASS_SOC, SOC_CODIGO_EMPRESA_PRINCIPAL, SOC_CODIGO_RESPONSAVEL, URL_SOC_SOAP_INSERT
from db_logger import logger, salvar_log_db, init_db, TIMESTAMP_EXECUCAO
from mapeamentos import MAPA_SITUACAO, MAPA_COR_RACA, MAPA_SEXO, MAPA_ESCOLARIDADE, MAPA_EMPRESAS, EMPRESAS_SOC
from rm_client import buscar_funcionarios_rm, criar_sessao_rm
from soc_client import carregar_base_soc, get_soap_security
from utils import limpar_cpf, limpar_telefone, padronizar_data, formatar_data_soc


def montar_base_soc(session):
    base_soc_geral = {}
    for empresa in EMPRESAS_SOC:
        print(f"Processando empresa {empresa.strip()}...")
        dados_empresa = carregar_base_soc(session, empresa)
        base_soc_geral.update(dados_empresa)
    return base_soc_geral


def montar_dataframe_soc(base_soc_geral):
    lista_registros = list(base_soc_geral.values())
    df_soc = pd.DataFrame(lista_registros)
    print(df_soc.head())
    if "CODIGOEMPRESA" in df_soc:
        contagem = df_soc["CODIGOEMPRESA"].value_counts()
        print(contagem, "Registros nas empresas")
        df_soc = df_soc.set_index(["cpf_limpo", "data_limpa", "nome_limpo"])
    else:
        print("A coluna 'CODIGOEMPRESA' não foi encontrada no DataFrame. Verifique os dados retornados do SOC.")
    return df_soc


def _normalizar_funcionario(funcionario):
    funcionario["EMISSAO_RG"] = formatar_data_soc(funcionario.get("EMISSAO_RG"))
    funcionario["DTNASCIMENTO"] = formatar_data_soc(funcionario.get("DTNASCIMENTO"))
    funcionario["DATAADMISSAO"] = formatar_data_soc(funcionario.get("DATAADMISSAO"))
    funcionario["DATADEMISSAO"] = formatar_data_soc(funcionario.get("DATADEMISSAO"))
    funcionario["DT_SITUACAO_VIGENTE"] = formatar_data_soc(funcionario.get("DT_SITUACAO_VIGENTE"))

    funcionario["CEP"] = re.sub(r"\D", "", str(funcionario.get("CEP", "")))

    cod_situacao_rm = str(funcionario.get("NOVASITUACAO", "")).strip().upper()
    funcionario["NOVASITUACAO"] = MAPA_SITUACAO.get(cod_situacao_rm, "OUTROS")

    cod_raca_rm = str(funcionario.get("CODCORRACA", "")).strip()
    funcionario["CODCORRACA"] = MAPA_COR_RACA.get(cod_raca_rm, "")

    sexo_rm = str(funcionario.get("SEXO", "")).strip().upper()
    funcionario["SEXO"] = MAPA_SEXO.get(sexo_rm, "NAO_INFORMADO")

    return funcionario


def _montar_envelope_soc(funcionario, codigo_empresa_soc, codigo_unidade, escolaridade_soc, telefones, endereco_formatado):
    sec = get_soap_security(USER_SOC, PASS_SOC)
    telcelular_limpo, telresidencial_limpo, telcomercial_limpo = telefones

    return sec, f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://services.soc.age.com/">
<soapenv:Header>
<wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
<wsu:Timestamp wsu:Id="TS-1">
<wsu:Created>{sec['created']}</wsu:Created>
<wsu:Expires>{sec['expires']}</wsu:Expires>
</wsu:Timestamp>
<wsse:UsernameToken wsu:Id="User-1">
<wsse:Username>{sec['username']}</wsse:Username>
<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">{sec['digest']}</wsse:Password>
<wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">{sec['nonce']}</wsse:Nonce>
<wsu:Created>{sec['created']}</wsu:Created>
</wsse:UsernameToken>
</wsse:Security>
</soapenv:Header>
<soapenv:Body>
<ser:importacaoFuncionario>
<Funcionario>
<criarFuncionario>true</criarFuncionario>
<atualizarFuncionario>true</atualizarFuncionario>
<criarUnidade>false</criarUnidade>
<atualizarUnidade>false</atualizarUnidade>
<criarSetor>false</criarSetor>
<atualizarSetor>false</atualizarSetor>
<criarCargo>false</criarCargo>
<atualizarCargo>false</atualizarCargo>
<criarCentroCusto>false</criarCentroCusto>
<atualizarCentroCusto>false</atualizarCentroCusto>
<criarMotivoLicenca>false</criarMotivoLicenca>
<atualizarMotivoLicenca>false</atualizarMotivoLicenca>
<criarTurno>false</criarTurno>
<atualizarTurno>false</atualizarTurno>
<criarUnidadeContratante>false</criarUnidadeContratante>
<criarHistorico>true</criarHistorico>
<funcionarioWsVo>
<chaveProcuraFuncionario>CPF_DATA_ADMISSAO</chaveProcuraFuncionario>
<cpf>{funcionario.get('CPF', '')}</cpf>
<tipoBuscaEmpresa>CODIGO_SOC</tipoBuscaEmpresa>
<codigoEmpresa>{codigo_empresa_soc}</codigoEmpresa>
<nomeFuncionario>{funcionario.get('NOME', '')}</nomeFuncionario>
<matricula>{funcionario.get('CHAPA', '')}</matricula>
<matriculaRh>{funcionario.get('MATRICULAESOCIAL', '')}</matriculaRh>
<dataNascimento>{funcionario.get('DTNASCIMENTO', '')}</dataNascimento>
<dataUltimaMovimentacao>{funcionario.get('DT_SITUACAO_VIGENTE', '')}</dataUltimaMovimentacao>
<dataAdmissao>{funcionario.get('DATAADMISSAO', '')}</dataAdmissao>
<dataDemissao>{funcionario.get('DATADEMISSAO', '')}</dataDemissao>
<situacao>{funcionario.get('NOVASITUACAO', '')}</situacao>
<sexo>{funcionario.get('SEXO', '')}</sexo>
<estadoCivil>{funcionario.get('ESTADOCIVIL', '')}</estadoCivil>
<remuneracaoMensal>{funcionario.get('SALARIO', '')}</remuneracaoMensal>
<tipoContratacao>{funcionario.get('TPCONTRATACAO', '')}</tipoContratacao>
<regimeTrabalho>{funcionario.get('REGIMECONTRATACAO', '')}</regimeTrabalho>
<pis>{funcionario.get('PIS', funcionario.get('NIT', ''))}</pis>
<rg>{funcionario.get('RG', '')}</rg>
<rgOrgaoEmissor>{funcionario.get('ORGAEMISSORRG', '')}</rgOrgaoEmissor>
<rgUf>{funcionario.get('UFRG', '')}</rgUf>
<rgDataEmissao>{funcionario.get('EMISSAO_RG', '')}</rgDataEmissao>
<ufCtps>{funcionario.get('UFCTPS', '')}</ufCtps>
<email>{funcionario.get('EMAILPESSOAsimL', '')}</email>
<nomePai>{funcionario.get('NOMEPAI', '')}</nomePai>
<nomeMae>{funcionario.get('NOMEMAE', '')}</nomeMae>
<naturalidade>{funcionario.get('NATURALIDADE', '')}</naturalidade>
<cor>{funcionario.get('CODCORRACA', '')}</cor>
<gfip>{funcionario.get('GFIP', '0')}</gfip>
<escolaridade>{escolaridade_soc}</escolaridade>
<grauInstrucao>{escolaridade_soc}</grauInstrucao>
<endereco>{endereco_formatado}</endereco>
<bairro>{funcionario.get('BAIRRO', '')}</bairro>
<cidade>{funcionario.get('CIDADE', '')}</cidade>
<estado>{funcionario.get('ESTADO', '')}</estado>
<cep>{funcionario.get('CEP', '')}</cep>
<telefoneCelular>{telcelular_limpo}</telefoneCelular>
<telefoneResidencial>{telresidencial_limpo}</telefoneResidencial>
<telefoneComercial>{telcomercial_limpo}</telefoneComercial>
<codigoCategoriaESocial>{funcionario.get('CODCATEGORIAESOCIAL', '')}</codigoCategoriaESocial>
</funcionarioWsVo>
<unidadeWsVo>
<tipoBusca>CODIGO_RH</tipoBusca>
<codigoRh>{codigo_unidade}</codigoRh>
</unidadeWsVo>
<setorWsVo>
<tipoBusca>CODIGO_RH</tipoBusca>
<codigoRh>{funcionario.get('CODSECAO', '')}</codigoRh>
<nome>{funcionario.get('SECAO', '')}</nome>
</setorWsVo>
<cargoWsVo>
<tipoBusca>CODIGO_RH</tipoBusca>
<codigoRh>{funcionario.get('CODFUNCAO', '')}</codigoRh>
<cbo>{funcionario.get('CBO', '')}</cbo>
</cargoWsVo>
<identificacaoWsVo>
<chaveAcesso>{PASS_SOC}</chaveAcesso>
<codigoEmpresaPrincipal>{SOC_CODIGO_EMPRESA_PRINCIPAL}</codigoEmpresaPrincipal>
<codigoResponsavel>{SOC_CODIGO_RESPONSAVEL}</codigoResponsavel>
<codigoUsuario>{USER_SOC}</codigoUsuario>
</identificacaoWsVo>
</Funcionario>
</ser:importacaoFuncionario>
</soapenv:Body>
</soapenv:Envelope>"""


def _enviar_funcionario(session, funcionario, soap_envelope, cod_coligada_rm):
    headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '""'}

    try:
        res_envio = session.post(URL_SOC_SOAP_INSERT, data=soap_envelope.encode("utf-8"), headers=headers)

        xml_sem_ns = res_envio.text.replace('xmlns="http://services.soc.age.com/"', "").replace("ns2:", "")
        root = ET.fromstring(xml_sem_ns)
        descricao_erro = root.find(".//descricaoErro")

        if res_envio.status_code == 200:
            tem_erro_xml = descricao_erro is not None and descricao_erro.text
            status = "ERRO" if tem_erro_xml else "SUCESSO"
            mensagem = f"Erro no XML: {descricao_erro.text}" if tem_erro_xml else "Processado com sucesso"

            salvar_log_db({
                "Data/Hora": datetime.now(),
                "Status": status,
                "Empresa": cod_coligada_rm,
                "Chapa": funcionario.get("CHAPA", ""),
                "Nome": funcionario.get("NOME", ""),
                "CPF": funcionario.get("CPF", ""),
                "Codigo_HTTP": 200,
                "Mensagem_SOC": mensagem,
                "Resposta_SOC": f"200 - {res_envio.text}",
            })

            log_fn = logger.error if tem_erro_xml else logger.info
            log_fn(f"[{cod_coligada_rm}] {funcionario.get('NOME','')} (CPF {funcionario.get('CPF','')}) - {mensagem}")
        else:
            mensagem = res_envio.text[:500]
            salvar_log_db({
                "Data/Hora": datetime.now(),
                "Status": "ERRO",
                "Empresa": cod_coligada_rm,
                "Chapa": funcionario.get("CHAPA", ""),
                "Nome": funcionario.get("NOME", ""),
                "CPF": funcionario.get("CPF", ""),
                "Codigo_HTTP": res_envio.status_code,
                "Mensagem_SOC": mensagem,
                "Resposta_SOC": f"{res_envio.status_code} - {res_envio.text}",
            })
            logger.error(f"[{cod_coligada_rm}] {funcionario.get('NOME','')} (CPF {funcionario.get('CPF','')}) - HTTP {res_envio.status_code}: {mensagem}")

    except requests.exceptions.RequestException as e:
        salvar_log_db({
            "Data/Hora": datetime.now(),
            "Status": "ERRO",
            "Empresa": cod_coligada_rm,
            "Chapa": funcionario.get("CHAPA", ""),
            "Nome": funcionario.get("NOME", ""),
            "CPF": funcionario.get("CPF", ""),
            "Codigo_HTTP": "N/A",
            "Mensagem_SOC": str(e),
            "Resposta_SOC": "N/A - Falha de rede, sem resposta do servidor",
        })
        logger.error(f"[{cod_coligada_rm}] {funcionario.get('NOME','')} (CPF {funcionario.get('CPF','')}) - Falha de rede: {e}")
    except Exception as e:
        salvar_log_db({
            "Data/Hora": datetime.now(),
            "Status": "ERRO",
            "Empresa": cod_coligada_rm,
            "Chapa": funcionario.get("CHAPA", ""),
            "Nome": funcionario.get("NOME", ""),
            "CPF": funcionario.get("CPF", ""),
            "Codigo_HTTP": "N/A",
            "Mensagem_SOC": str(e),
            "Resposta_SOC": "N/A - Erro interno no processamento",
        })
        logger.error(f"[{cod_coligada_rm}] {funcionario.get('NOME','')} (CPF {funcionario.get('CPF','')}) - Erro interno: {e}")


def executar_sincronizacao():
    init_db()

    session = criar_sessao_rm()
    lista_funcionarios = buscar_funcionarios_rm()

    base_soc_geral = montar_base_soc(session)
    df_soc = montar_dataframe_soc(base_soc_geral)

    for funcionario in lista_funcionarios:
        funcionario = _normalizar_funcionario(funcionario)

        telefones = (
            limpar_telefone(funcionario.get("TEL_CELULAR")),
            limpar_telefone(funcionario.get("TEL_RESIDENCIAL")),
            limpar_telefone(funcionario.get("TEL_COMERCIAL")),
        )
        endereco_formatado = str(funcionario.get("ENDERECO", ""))[:100].replace("&", "&amp;")

        cod_coligada_rm = str(funcionario.get("CODCOLIGADA"))
        dados_empresa = MAPA_EMPRESAS.get(cod_coligada_rm, {"codigo_soc": "DEFAULT_OU_ERRO", "unidade": "0"})

        if dados_empresa["codigo_soc"] == "DEFAULT_OU_ERRO":
            print(f"Aviso: código de empresa {cod_coligada_rm} não mapeado para o SOC.")
            continue

        cod_escolaridade = str(funcionario.get("CODESCOLARIDADE", "")).strip()
        escolaridade_soc = MAPA_ESCOLARIDADE.get(cod_escolaridade, "OUTROS")

        raw_cpf = funcionario.get("CPF")
        raw_data = funcionario.get("DATAADMISSAO")

        if raw_cpf and raw_data:
            chave_busca = (limpar_cpf(raw_cpf), padronizar_data(raw_data))
        else:
            chave_busca = None
            mensagem = funcionario.get("mensagemRetorno", "Registro inválido ou vazio")
            print(f"Aviso: {mensagem}")

        if chave_busca in df_soc.index:
            print(f"Registro encontrado para {funcionario['NOME']} CPF: {funcionario['CPF']}. Seguindo com o envio.")
            _, soap_envelope = _montar_envelope_soc(
                funcionario,
                dados_empresa["codigo_soc"],
                dados_empresa["unidade"],
                escolaridade_soc,
                telefones,
                endereco_formatado,
            )
            _enviar_funcionario(session, funcionario, soap_envelope, cod_coligada_rm)
        else:
            salvar_log_db({
                "Data/Hora": datetime.now(),
                "Status": "IGNORADO",
                "Empresa": cod_coligada_rm,
                "Chapa": funcionario.get("CHAPA", ""),
                "Nome": funcionario.get("NOME", ""),
                "CPF": funcionario.get("CPF", ""),
                "Codigo_HTTP": "N/A",
                "Mensagem_SOC": "Não consta na base do SOC",
                "Resposta_SOC": "",
            })
            logger.info(f"[{cod_coligada_rm}] {funcionario.get('NOME','')} (CPF {funcionario.get('CPF','')}) - Ignorado: não consta na base do SOC")

    logger.info(f"===== Fim do processamento: {TIMESTAMP_EXECUCAO} =====")
    print("\nProcessamento concluído. Logs gravados na tabela LogIntegracaoSOC.")
