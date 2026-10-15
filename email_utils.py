import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

from config import SMTP_SERVER, SMTP_PORT, EMAIL_REMETENTE, EMAIL_SENHA, EMAIL_DESTINATARIO


def enviar_email_com_anexo(caminho_arquivo):
    if not all([EMAIL_REMETENTE, EMAIL_SENHA, EMAIL_DESTINATARIO]):
        print("Aviso: credenciais de e-mail não configuradas no .env. O e-mail não será enviado.")
        return

    msg = EmailMessage()
    msg["Subject"] = f'Log de Processamento de Integração SOC - {datetime.now().strftime("%d/%m/%Y %H:%M")}'
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO

    corpo_email = f"""
    Olá,

    O processamento da integração foi finalizado.
    Segue em anexo o arquivo de log gerado: {os.path.basename(caminho_arquivo)}.

    Atenciosamente,
    Automação de Integração
    """
    msg.set_content(corpo_email)

    try:
        with open(caminho_arquivo, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(caminho_arquivo)
        msg.add_attachment(file_data, maintype="text", subtype="csv", filename=file_name)
    except Exception as e:
        print(f"Erro ao ler o arquivo de log para anexo: {e}")
        return

    try:
        print("Conectando ao servidor SMTP para envio de e-mail...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.send_message(msg)
        print("E-mail com log enviado com sucesso!")
    except Exception as e:
        print(f"Erro crítico ao enviar o e-mail: {e}")
