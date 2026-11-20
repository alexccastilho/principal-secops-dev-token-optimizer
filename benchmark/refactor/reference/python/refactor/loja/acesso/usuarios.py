"""Usuários do sistema (quem opera o caixa e o back office).

Papéis:
  admin    - acesso completo
  vendedor - vende e consulta os próprios pedidos
"""
import hashlib
import logging
import re

from ..comum.validacao import normalizar_email
from ..infra import banco, config

log = logging.getLogger(__name__)

_RE_LOGIN = re.compile(r"^[a-z0-9_.]{3,30}$")


def _hash_senha(senha):
    return hashlib.md5(senha.encode("utf-8")).hexdigest()


def _validar_senha_nova(senha):
    if not senha or len(senha) < config.TAMANHO_MINIMO_SENHA:
        raise ValueError(
            "A senha precisa ter pelo menos %d caracteres" % config.TAMANHO_MINIMO_SENHA
        )


def _usuario(linha):
    if linha is None:
        return None
    return {
        "id": linha["id"],
        "login": linha["login"],
        "nome": linha["nome"],
        "email": linha["email"],
        "papel": linha["papel"],
        "ativo": bool(linha["ativo"]),
    }


def criar_usuario(conn, login, senha, papel=config.PAPEL_PADRAO, nome="", email=""):
    """Cria um usuário e devolve o id."""
    login = (login or "").strip().lower()
    if not _RE_LOGIN.match(login):
        raise ValueError("Login inválido: use de 3 a 30 letras minúsculas, números, '_' ou '.'")
    if papel not in config.PAPEIS:
        raise ValueError("Papel inválido: %s" % papel)
    _validar_senha_nova(senha)
    email = normalizar_email(email, obrigatorio=False)
    if conn.execute("SELECT 1 FROM usuarios WHERE login = ?", (login,)).fetchone():
        raise ValueError("Login já existe")
    cur = conn.execute(
        "INSERT INTO usuarios (login, nome, email, senha_hash, papel, ativo, criado_em)"
        " VALUES (?, ?, ?, ?, ?, 1, ?)",
        (login, (nome or "").strip(), email, _hash_senha(senha), papel, banco.agora()),
    )
    conn.commit()
    log.info("usuario %s criado com papel %s", login, papel)
    return cur.lastrowid


def buscar_usuario(conn, login):
    linha = conn.execute(
        "SELECT * FROM usuarios WHERE login = ?", ((login or "").strip().lower(),)
    ).fetchone()
    return _usuario(linha)


def buscar_usuario_por_id(conn, usuario_id):
    linha = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _usuario(linha)


def verificar_senha(conn, login, senha):
    """True se o login existe, está ativo e a senha confere."""
    linha = conn.execute(
        "SELECT senha_hash, ativo FROM usuarios WHERE login = ?",
        ((login or "").strip().lower(),),
    ).fetchone()
    if linha is None or not linha["ativo"]:
        return False
    return linha["senha_hash"] == _hash_senha(senha or "")


def alterar_senha(conn, login, senha_atual, nova_senha):
    """Troca a senha conferindo a atual. Devolve False se a atual não bate."""
    if not verificar_senha(conn, login, senha_atual):
        return False
    _validar_senha_nova(nova_senha)
    conn.execute(
        "UPDATE usuarios SET senha_hash = ? WHERE login = ?",
        (_hash_senha(nova_senha), login.strip().lower()),
    )
    # derruba as sessões abertas com a senha antiga
    conn.execute(
        "DELETE FROM sessoes WHERE usuario_id = (SELECT id FROM usuarios WHERE login = ?)",
        (login.strip().lower(),),
    )
    conn.commit()
    return True


def desativar_usuario(conn, login):
    login = (login or "").strip().lower()
    cur = conn.execute("UPDATE usuarios SET ativo = 0 WHERE login = ?", (login,))
    conn.execute(
        "DELETE FROM sessoes WHERE usuario_id = (SELECT id FROM usuarios WHERE login = ?)",
        (login,),
    )
    conn.commit()
    return cur.rowcount > 0


def listar_usuarios(conn):
    linhas = conn.execute("SELECT * FROM usuarios ORDER BY login").fetchall()
    return [_usuario(l) for l in linhas]
