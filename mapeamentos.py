MAPA_SITUACAO = {
    "A": "ATIVO",
    "D": "INATIVO",
    "Z": "ATIVO",
    "F": "FERIAS",
    **{codigo: "AFASTADO" for codigo in ["E", "I", "L", "M", "O", "P", "R", "S", "T", "U", "V", "X", "W", "C", "K", "N", "G", "Y", "Q"]},
}

MAPA_COR_RACA = {
    "0": "INDIGENA",
    "2": "BRANCO",
    "6": "AMARELO",
    "8": "PARDO",
    "9": "OUTROS",
    "10": "OUTROS",
}

MAPA_SEXO = {
    "M": "MASCULINO",
    "F": "FEMININO",
}

MAPA_ESCOLARIDADE = {
    "1": "ANALFABETO",
    "2": "ENSINO_FUNDAMENTAL_INCOMPLETO",
    "3": "ENSINO_FUNDAMENTAL_COMPLETO",
    "4": "ENSINO_FUNDAMENTAL_COMPLETO",
    "5": "ENSINO_FUNDAMENTAL_COMPLETO",
    "6": "ENSINO_MEDIO_INCOMPLETO",
    "7": "ENSINO_MEDIO_COMPLETO",
    "8": "ENSINO_SUPERIOR_INCOMPLETO",
    "9": "ENSINO_SUPERIOR_COMPLETO",
    "A": "POS_GRADUACAO_INCOMPLETA",
    "B": "POS_GRADUACAO_COMPLETA",
    "C": "MESTRADO_INCOMPLETO",
    "D": "MESTRADO_COMPLETO",
    "E": "DOUTORADO_INCOMPLETO",
    "F": "DOUTORADO_COMPLETO",
    "G": "PHD_INCOMPLETO",
    "H": "PHD_COMPLETO",
}

# Mapeamento ilustrativo: código interno da coligada RM -> código da empresa no SOC
MAPA_EMPRESAS = {
    "1": {"codigo_soc": "EMPRESA_SOC_1", "unidade": "1"},
    "2": {"codigo_soc": "EMPRESA_SOC_2", "unidade": "2"},
    "3": {"codigo_soc": "EMPRESA_SOC_3", "unidade": "3"},
    "4": {"codigo_soc": "EMPRESA_SOC_4", "unidade": "4"},
    "5": {"codigo_soc": "EMPRESA_SOC_5", "unidade": "5"},
    "6": {"codigo_soc": "EMPRESA_SOC_6", "unidade": "6"},
    "7": {"codigo_soc": "EMPRESA_SOC_7", "unidade": "7"},
    "8": {"codigo_soc": "EMPRESA_SOC_8", "unidade": "8"},
    "9": {"codigo_soc": "EMPRESA_SOC_9", "unidade": "9"},
}

EMPRESAS_SOC = list(MAPA_EMPRESAS[k]["codigo_soc"] for k in MAPA_EMPRESAS)

# Depara de campos RM -> SOC
MAPEAMENTO_CAMPOS = {
    "CPF": "CPFFUNCIONARIO",
    "DATAADMISSAO": "DATA_ADMISSAO",
    "SITUACAO": "SITUACAO",
    "NOME": "NOME",
}
