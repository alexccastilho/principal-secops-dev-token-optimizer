"""Cópia de segurança do banco.

Roda no fechamento do caixa. Guarda as últimas N cópias numa pasta e
apaga as mais antigas.
"""
import logging
import os
import sqlite3
from datetime import datetime

log = logging.getLogger(__name__)

PREFIXO = "loja-"
EXTENSAO = ".db"
MANTER_PADRAO = 7


def fazer_backup(conn, pasta, manter=MANTER_PADRAO):
    """Copia o banco aberto para a pasta e devolve o caminho da cópia.

    Usa a API de backup do SQLite, que funciona com o banco em uso.
    """
    os.makedirs(pasta, exist_ok=True)
    nome = PREFIXO + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + EXTENSAO
    destino = os.path.join(pasta, nome)
    copia = sqlite3.connect(destino)
    try:
        conn.backup(copia)
    finally:
        copia.close()
    log.info("backup gravado em %s", destino)
    _apagar_antigos(pasta, manter)
    return destino


def listar_backups(pasta):
    """Caminhos das cópias na pasta, da mais nova para a mais antiga."""
    if not os.path.isdir(pasta):
        return []
    nomes = [n for n in os.listdir(pasta) if n.startswith(PREFIXO) and n.endswith(EXTENSAO)]
    nomes.sort(reverse=True)
    return [os.path.join(pasta, n) for n in nomes]


def _apagar_antigos(pasta, manter):
    for caminho in listar_backups(pasta)[manter:]:
        try:
            os.remove(caminho)
        except OSError as erro:
            log.warning("não consegui apagar %s: %s", caminho, erro)


def verificar_backup(caminho):
    """True se o arquivo abre como banco SQLite íntegro e tem as tabelas da loja."""
    try:
        conn = sqlite3.connect(caminho)
        try:
            ok = conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            tabelas = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
        finally:
            conn.close()
    except sqlite3.Error:
        return False
    return ok and {"clientes", "produtos", "pedidos"} <= tabelas
