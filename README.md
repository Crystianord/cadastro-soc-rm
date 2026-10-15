# Cadastro SOC x TOTVS RM — Sincronização de Funcionários

Automação que sincroniza o cadastro de funcionários do **TOTVS RM** com o
**SOC** (Software Integrado de Gestão Ocupacional), eliminando o cadastro
manual duplicado entre os dois sistemas.

## O que o projeto faz

1. Consulta via REST os funcionários ativos no TOTVS RM, filtra contratos PJ
   e deduplica registros (mesmo CPF + data de admissão), priorizando o
   vínculo ativo ou o mais recente.
2. Consulta via SOAP (WS-Security) a base de funcionários já cadastrados no
   SOC, para cada empresa configurada.
3. Cruza as duas bases por CPF + data de admissão. Quando o funcionário do RM
   já existe no SOC, normaliza os campos (situação, sexo, cor/raça,
   escolaridade, telefones, endereço, CEP) e envia o cadastro/atualização via
   SOAP (`importacaoFuncionario`).
4. Registra cada envio (sucesso, erro ou ignorado) em log local (arquivo) e
   em uma tabela de histórico no SQL Server, e envia um e-mail ao final com o
   log de sucesso em anexo.

## Stack

- Python
- `requests` para consumo dos web services REST (RM) e SOAP (SOC)
- `pandas` / `xmltodict` para tratamento dos dados retornados
- `pyodbc` para log de processamento em SQL Server
- `smtplib` para notificação por e-mail ao final da execução
- Autenticação WS-Security (UsernameToken + PasswordDigest) implementada manualmente
- Adapter de TLS customizado para compatibilidade com servidor RM on-premise legado

## Estrutura

```
config.py              # variáveis de ambiente
mapeamentos.py          # de-para de domínios SOC <-> RM (situação, sexo, escolaridade, empresas...)
utils.py                # normalização de CPF, telefone, datas
rm_client.py            # consulta REST ao TOTVS RM
soc_client.py            # consulta SOAP + WS-Security ao SOC
db_logger.py            # logging em arquivo e histórico em SQL Server
email_utils.py           # envio do log por e-mail
sincronizar_soc_rm.py     # orquestração do fluxo completo
main.py                  # ponto de entrada
```

## Configuração

1. Copie `.env.example` para `.env` e preencha com as credenciais do seu ambiente:

```bash
cp .env.example .env
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute:

```bash
python main.py
```

> Este repositório é uma versão sanitizada de uma automação usada em produção:
> credenciais, hosts, e-mails e códigos internos de empresa foram removidos
> ou anonimizados e passam a ser lidos de variáveis de ambiente.
