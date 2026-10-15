from db_logger import LOG_SUCESSO
from email_utils import enviar_email_com_anexo
from sincronizar_soc_rm import executar_sincronizacao

if __name__ == "__main__":
    executar_sincronizacao()
    enviar_email_com_anexo(LOG_SUCESSO)
