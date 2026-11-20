"""Login e sessões.

O token entregue no login tem duas partes separadas por ponto: um valor
aleatório e a assinatura dele. A sessão também fica gravada na tabela
sessoes, com prazo de validade.
"""
import hashlib
import hmac
import logging
import random
import string
from datetime import datetime, timedelta

from ..infra import banco, config
from .usuarios import buscar_usuario, buscar_usuario_por_id, verificar_senha

log = logging.getLogger(__name__)

_ALFABETO = string.ascii_letters + string.digits


def _assinar(valor):
    chave = config.SEGREDO_TOKEN.encode("utf-8")
    return hmac.new(chave, valor.encode("utf-8"), hashlib.sha256).hexdigest()[:20]


def _gerar_token():
    valor = "".join(random.choice(_ALFABETO) for _ in range(config.TAMANHO_TOKEN))
    return valor + "." + _assinar(valor)


def _token_bem_formado(token):
    if not token or token.count(".") != 1:
        return False
    valor, assinatura = token.split(".")
    return hmac.compare_digest(assinatura, _assinar(valor))


def fazer_login(conn, login, senha):
    """Confere usuário e senha e abre uma sessão.

    Devolve o token da sessão, ou None se o login falhar.
    """
    if not verificar_senha(conn, login, senha):
        log.info("falha de login para %r", login)
        return None
    usuario = buscar_usuario(conn, login)
    token = _gerar_token()
    inicio = datetime.now()
    fim = inicio + timedelta(hours=config.DURACAO_SESSAO_HORAS)
    conn.execute(
        "INSERT INTO sessoes (token, usuario_id, criado_em, expira_em) VALUES (?, ?, ?, ?)",
        (
            token,
            usuario["id"],
            inicio.strftime(config.FORMATO_DATA_HORA),
            fim.strftime(config.FORMATO_DATA_HORA),
        ),
    )
    conn.commit()
    return token


def usuario_da_sessao(conn, token):
    """Usuário dono do token, ou None se o token for inválido ou estiver vencido.

    Devolve um dict com id, login, nome e papel.
    """
    if not _token_bem_formado(token):
        return None
    linha = conn.execute(
        "SELECT usuario_id, expira_em FROM sessoes WHERE token = ?", (token,)
    ).fetchone()
    if linha is None:
        return None
    if linha["expira_em"] < banco.agora():
        conn.execute("DELETE FROM sessoes WHERE token = ?", (token,))
        conn.commit()
        return None
    usuario = buscar_usuario_por_id(conn, linha["usuario_id"])
    if usuario is None or not usuario["ativo"]:
        return None
    return {
        "id": usuario["id"],
        "login": usuario["login"],
        "nome": usuario["nome"],
        "papel": usuario["papel"],
    }


def encerrar_sessao(conn, token):
    cur = conn.execute("DELETE FROM sessoes WHERE token = ?", (token,))
    conn.commit()
    return cur.rowcount > 0


def limpar_sessoes_vencidas(conn):
    cur = conn.execute("DELETE FROM sessoes WHERE expira_em < ?", (banco.agora(),))
    conn.commit()
    return cur.rowcount
