import logging
import os
from datetime import datetime

import pyodbc

from config import DB_CONNECTION_STRING, PASTA_LOGS

TIMESTAMP_EXECUCAO = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_SUCESSO = os.path.join(PASTA_LOGS, f"log_sucesso_{TIMESTAMP_EXECUCAO}.txt")
LOG_ERRO = os.path.join(PASTA_LOGS, f"log_erro_{TIMESTAMP_EXECUCAO}.txt")

logger = logging.getLogger("SOC_Integration")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt="%d/%m/%Y %H:%M:%S")

file_sucesso = logging.FileHandler(LOG_SUCESSO, encoding="utf-8")
file_sucesso.setLevel(logging.INFO)
file_sucesso.addFilter(lambda record: record.levelno == logging.INFO)
file_sucesso.setFormatter(formatter)

file_erro = logging.FileHandler(LOG_ERRO, encoding="utf-8")
file_erro.setLevel(logging.WARNING)
file_erro.setFormatter(formatter)

logger.addHandler(file_sucesso)
logger.addHandler(file_erro)

_db_conn = None


def get_db_conn():
    global _db_conn
    try:
        if _db_conn is None:
            raise Exception("sem conexão")
        _db_conn.cursor().execute("SELECT 1")
    except Exception:
        _db_conn = pyodbc.connect(DB_CONNECTION_STRING)
    return _db_conn


def init_db():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LogIntegracaoSOC' AND xtype='U')
        CREATE TABLE LogIntegracaoSOC (
            Id          INT IDENTITY(1,1) PRIMARY KEY,
            DataHora    DATETIME      NOT NULL,
            Status      NVARCHAR(50),
            Empresa     NVARCHAR(10),
            Chapa       NVARCHAR(50),
            Nome        NVARCHAR(255),
            CPF         NVARCHAR(20),
            CodigoHTTP  NVARCHAR(10),
            MensagemSOC NVARCHAR(MAX),
            RespostaSOC NVARCHAR(MAX)
        )
    """)
    for col, tipo in [("Empresa", "NVARCHAR(10)"), ("Chapa", "NVARCHAR(50)")]:
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM sys.columns
                WHERE object_id = OBJECT_ID('LogIntegracaoSOC') AND name = '{col}'
            )
            ALTER TABLE LogIntegracaoSOC ADD {col} {tipo}
        """)
    conn.commit()


def salvar_log_db(dados):
    global _db_conn
    for tentativa in range(2):
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO LogIntegracaoSOC "
                "(DataHora, Status, Empresa, Chapa, Nome, CPF, CodigoHTTP, MensagemSOC, RespostaSOC) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                dados["Data/Hora"],
                dados["Status"],
                dados.get("Empresa", ""),
                dados.get("Chapa", ""),
                dados.get("Nome", ""),
                dados.get("CPF", ""),
                str(dados.get("Codigo_HTTP", "")),
                dados.get("Mensagem_SOC", ""),
                dados.get("Resposta_SOC", ""),
            )
            conn.commit()
            return
        except pyodbc.OperationalError:
            _db_conn = None
            if tentativa == 1:
                raise
