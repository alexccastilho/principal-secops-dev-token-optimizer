"""Importação de clientes a partir de planilha CSV.

Usada quando a loja trouxe a base do sistema antigo. O arquivo precisa
ter cabeçalho com as colunas nome, cpf e email; telefone e cep são
opcionais. Aceita ponto e vírgula ou vírgula como separador.
"""
import csv
import logging

from . import db
from .clientes import formatar_telefone

log = logging.getLogger(__name__)

COLUNAS_OBRIGATORIAS = ("nome", "cpf", "email")


def _valida_cpf(cpf):
    cpf = cpf.replace(".", "").replace("-", "").strip()
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    if cpf in [str(n) * 11 for n in range(10)]:
        return False
    digitos = [int(c) for c in cpf]
    for tam in (9, 10):
        peso = tam + 1
        total = 0
        for d in digitos[:tam]:
            total += d * peso
            peso -= 1
        resto = total % 11
        esperado = 0 if resto < 2 else 11 - resto
        if digitos[tam] != esperado:
            return False
    return True


def _valida_email(email):
    if " " in email or email.count("@") != 1:
        return False
    usuario, dominio = email.split("@")
    return bool(usuario) and "." in dominio and not dominio.endswith(".")


def _detectar_separador(primeira_linha):
    return ";" if primeira_linha.count(";") >= primeira_linha.count(",") else ","


def _ler_registros(caminho):
    with open(caminho, newline="", encoding="utf-8-sig") as arq:
        primeira = arq.readline()
        arq.seek(0)
        leitor = csv.DictReader(arq, delimiter=_detectar_separador(primeira))
        cabecalho = [c.strip().lower() for c in (leitor.fieldnames or [])]
        faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in cabecalho]
        if faltando:
            raise ValueError("Colunas obrigatórias ausentes: %s" % ", ".join(faltando))
        leitor.fieldnames = cabecalho
        for numero, registro in enumerate(leitor, start=2):
            yield numero, {k: (v or "").strip() for k, v in registro.items() if k}


def importar_clientes_csv(conn, caminho):
    """Importa clientes do CSV. CPF já cadastrado é ignorado.

    Devolve {"importados": n, "ignorados": n, "erros": ["linha 3: ...", ...]}.
    """
    importados = 0
    ignorados = 0
    erros = []
    agora = db.agora()
    for numero, reg in _ler_registros(caminho):
        nome = " ".join(reg.get("nome", "").split())
        cpf = reg.get("cpf", "")
        email = reg.get("email", "").lower()
        if not nome:
            erros.append("linha %d: nome vazio" % numero)
            continue
        if not _valida_cpf(cpf):
            erros.append("linha %d: CPF inválido (%s)" % (numero, cpf))
            continue
        if not _valida_email(email):
            erros.append("linha %d: e-mail inválido (%s)" % (numero, email))
            continue
        cpf = cpf.replace(".", "").replace("-", "").strip()
        if conn.execute("SELECT 1 FROM clientes WHERE cpf = ?", (cpf,)).fetchone():
            ignorados += 1
            continue
        telefone = formatar_telefone(reg.get("telefone", "")) if reg.get("telefone") else ""
        cep = reg.get("cep", "")
        if cep:
            digitos = "".join(c for c in cep if c.isdigit())
            cep = digitos[:5] + "-" + digitos[5:] if len(digitos) == 8 else ""
        conn.execute(
            "INSERT INTO clientes (nome, cpf, email, telefone, cep, criado_em)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (nome, cpf, email, telefone, cep, agora),
        )
        importados += 1
    conn.commit()
    log.info("importacao de %s: %d importados, %d erros", caminho, importados, len(erros))
    return {"importados": importados, "ignorados": ignorados, "erros": erros}
