"""Importação de clientes a partir de planilha CSV.

O arquivo precisa ter cabeçalho com as colunas nome, cpf e email;
telefone e cep são opcionais. Aceita ponto e vírgula ou vírgula.
"""
import csv
import logging

from ..comum.formatacao import formatar_cep, formatar_telefone
from ..comum.validacao import somente_digitos, validar_cpf, validar_email
from ..infra import banco
from .clientes import cpf_ja_cadastrado

log = logging.getLogger(__name__)

COLUNAS_OBRIGATORIAS = ("nome", "cpf", "email")


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


def _cep_ou_vazio(cep):
    try:
        return formatar_cep(cep) if cep else ""
    except ValueError:
        return ""


def _problema(nome, cpf, email):
    if not nome:
        return "nome vazio"
    if not validar_cpf(cpf):
        return "CPF inválido (%s)" % cpf
    if not validar_email(email):
        return "e-mail inválido (%s)" % email
    return None


def importar_clientes_csv(conn, caminho):
    """Importa clientes do CSV. CPF já cadastrado é ignorado.

    Devolve {"importados": n, "ignorados": n, "erros": ["linha 3: ...", ...]}.
    """
    resultado = {"importados": 0, "ignorados": 0, "erros": []}
    agora = banco.agora()
    for numero, reg in _ler_registros(caminho):
        nome = " ".join(reg.get("nome", "").split())
        email = reg.get("email", "").lower()
        problema = _problema(nome, reg.get("cpf", ""), email)
        if problema:
            resultado["erros"].append("linha %d: %s" % (numero, problema))
            continue
        cpf = somente_digitos(reg["cpf"])
        if cpf_ja_cadastrado(conn, cpf):
            resultado["ignorados"] += 1
            continue
        telefone = formatar_telefone(reg["telefone"]) if reg.get("telefone") else ""
        conn.execute(
            "INSERT INTO clientes (nome, cpf, email, telefone, cep, criado_em)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (nome, cpf, email, telefone, _cep_ou_vazio(reg.get("cep", "")), agora),
        )
        resultado["importados"] += 1
    conn.commit()
    log.info("importacao de %s: %d importados, %d erros",
             caminho, resultado["importados"], len(resultado["erros"]))
    return resultado
