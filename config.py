import os

from dotenv import load_dotenv

load_dotenv()

# === SOC ===
URL_SOC_SOAP_CONSULTA = os.getenv("URL_SOC_SOAP_CONSULTA")
URL_SOC_SOAP_INSERT = os.getenv("URL_SOC_SOAP_INSERT")
USER_SOC = os.getenv("USER_SOC")
PASS_SOC = os.getenv("PASS_SOC")
SOC_CODIGO = os.getenv("SOC_CODIGO")
SOC_CHAVE = os.getenv("SOC_CHAVE")
SOC_CODIGO_EMPRESA_PRINCIPAL = os.getenv("SOC_CODIGO_EMPRESA_PRINCIPAL")
SOC_CODIGO_RESPONSAVEL = os.getenv("SOC_CODIGO_RESPONSAVEL")

# === TOTVS RM ===
URL_RM_REST = os.getenv("URL_RM_REST")
REST_USER = os.getenv("REST_USER")
REST_PASS = os.getenv("REST_PASS")

# === SQL Server (log) ===
DB_CONNECTION_STRING = (
    "Driver={ODBC Driver 17 for SQL Server};"
    f"Server={os.getenv('DB_SERVER')},{os.getenv('DB_PORT', '1433')};"
    f"Database={os.getenv('DB_DATABASE')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')}"
)

# === E-mail de notificação ===
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")

# === Pastas de log local ===
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_LOGS = os.path.join(PASTA_SCRIPT, "logs_integracao_soc")
os.makedirs(PASTA_LOGS, exist_ok=True)
