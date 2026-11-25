#!/usr/bin/env python3
"""Scanner de padroes inseguros para o portao de pre-entrega da skill.

Uso (Windows: troque python3 por py -3):
    python3 revisar_codigo.py <arquivo-ou-pasta> [mais arquivos...]
    python3 revisar_codigo.py . --json
    python3 revisar_codigo.py <pasta-do-projeto> --entrega   (tambem confere se roda como entregue)

Requer Python 3.8 ou mais novo. So usa a biblioteca padrao.

Segredos nunca aparecem na saida: se uma linha contem um possivel segredo, o
trecho dela e omitido em TODOS os achados daquela linha, nao so no achado de
segredo. Arquivos onde segredo e esperado (.env, wp-config.php) nunca tem
trecho impresso.

Codigo de saida:
    0 = nenhum achado HIGH (e, com --entrega, nenhum problema de entrega)
    1 = pelo menos um achado HIGH, ou com --entrega um problema que impede rodar
    2 = erro de uso (caminho inexistente, nenhum arquivo legivel)

O scanner e deliberadamente conservador: ele aponta padroes que quase sempre
sao problema. Um achado nao e prova de falha, e um ponto para revisar antes
de entregar. A ausencia de achados tambem nao prova que o codigo e seguro:
o checklist do SKILL.md continua obrigatorio.

As mensagens ficam em ASCII de proposito: a saida e lida por terminais e
ferramentas do Windows que nem sempre decodificam UTF-8.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

# --- Grupos de tipo de arquivo. Uma regra so roda onde o padrao significa
# o que ela diz: sprintf e perigoso em C e inofensivo em PHP.
C_FAMILY = frozenset({".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".inl", ".m", ".mm"})
PHP = frozenset({".php", ".phtml", ".inc"})
PY = frozenset({".py"})
JS = frozenset({".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
                ".astro", ".html", ".htm", ".ejs"})
TEMPLATES = frozenset({".twig", ".html", ".htm", ".jinja", ".j2", ".njk", ".erb",
                       ".rb", ".py", ".php", ".phtml", ".liquid"})
CONFIG = frozenset({".properties", ".ini", ".conf", ".yml", ".yaml", ".toml", ".env"})
QT = C_FAMILY | PY | frozenset({".qml", ".ui"})
# Linguagens cobertas a partir da 2.2.0. Cada grupo so recebe as regras que
# significam a mesma coisa nele.
PASCAL = frozenset({".pas", ".dpr", ".dpk", ".pp", ".lpr", ".dfm", ".lfm"})
XBASE = frozenset({".prg", ".ch"})
VB = frozenset({".bas", ".cls", ".frm", ".vb", ".vbs"})
COBOL_RPG = frozenset({".cob", ".cbl", ".cpy", ".rpgle", ".sqlrpgle", ".srw", ".sru", ".srd"})
ABAP = frozenset({".abap"})
OPENEDGE = frozenset({".p", ".w"})
LUA = frozenset({".lua"})
PERL = frozenset({".pl", ".pm", ".t", ".cgi"})
TCL = frozenset({".tcl"})
AHK = frozenset({".ahk"})
GAS = frozenset({".gs"})
BATCH = frozenset({".bat", ".cmd"})
PS = frozenset({".ps1", ".psm1", ".psd1"})
SH = frozenset({".sh", ".bash"})
R_LANG = frozenset({".r", ".rmd", ".qmd"})
JULIA = frozenset({".jl"})
FORTRAN = frozenset({".f90", ".f95", ".f03", ".f08", ".f18", ".f", ".for", ".f77"})
SAS = frozenset({".sas"})
GO = frozenset({".go"})
CS = frozenset({".cs", ".cshtml", ".razor"})
RUBY = frozenset({".rb", ".rake", ".erb", ".gemspec"})
KOTLIN = frozenset({".kt", ".kts"})
SWIFT = frozenset({".swift"})
DART = frozenset({".dart"})
SCALA = frozenset({".scala", ".sc", ".sbt"})
BEAM = frozenset({".ex", ".exs", ".erl", ".hrl"})
CLOJURE = frozenset({".clj", ".cljs", ".cljc"})
HASKELL = frozenset({".hs", ".lhs"})
OCAML = frozenset({".ml", ".mli"})
GROOVY = frozenset({".groovy", ".gvy", ".jenkinsfile"})
CRYSTAL = frozenset({".cr"})
RUST = frozenset({".rs"})
ZIG = frozenset({".zig"})
ADA = frozenset({".adb", ".ads", ".gpr"})
DLANG = frozenset({".d"})
NIM = frozenset({".nim"})
FSHARP = frozenset({".fs", ".fsi", ".fsx"})
JAVA = frozenset({".java", ".jsp"})
NEW_LANGS = (PASCAL | XBASE | VB | COBOL_RPG | ABAP | OPENEDGE | LUA | PERL | TCL | AHK | GAS
             | R_LANG | JULIA | FORTRAN | SAS | BEAM | CLOJURE | HASKELL | OCAML | CRYSTAL
             | ZIG | ADA | DLANG | NIM | FSHARP | RUBY | KOTLIN | SWIFT | DART | SCALA
             | GO | CS | RUST | JAVA | PS | SH | BATCH
             | frozenset({".mts", ".cts", ".ipynb", ".rules", ".dockerfile"}))

# Extensoes analisadas ao varrer uma pasta. Um arquivo passado pelo nome e
# analisado seja qual for a extensao.
CODE_SUFFIXES = C_FAMILY | PHP | PY | JS | TEMPLATES | CONFIG | frozenset({
    ".java", ".kt", ".kts", ".scala", ".groovy", ".gradle", ".go", ".cs",
    ".rs", ".swift", ".dart", ".sql", ".sh", ".bash", ".ps1", ".psm1",
    ".bat", ".cmd", ".json", ".xml", ".tf", ".cmake", ".qml", ".slint",
    ".xaml", ".axaml", ".ui", ".pem", ".key", ".htaccess",
}) | NEW_LANGS

# Arquivos sem extensao util, pelo nome. O valor e o tipo usado nas regras.
CODE_NAMES = {
    "CMakeLists.txt": ".cmake", "Makefile": ".mk", "makefile": ".mk",
    "GNUmakefile": ".mk", "Dockerfile": ".dockerfile", ".htaccess": ".htaccess",
    "id_rsa": ".key", "id_dsa": ".key", "id_ecdsa": ".key", "id_ed25519": ".key",
    "Jenkinsfile": ".jenkinsfile", "Gemfile": ".rb", "Rakefile": ".rb",
}

# Linguagens em que "#" abre comentario. Em C e diretiva (#define com segredo
# existe) e em JavaScript e campo privado de classe.
HASH_COMMENT = PY | PHP | CONFIG | frozenset({
    ".sh", ".bash", ".rb", ".ps1", ".psm1", ".cmake", ".mk", ".dockerfile",
    ".tf", ".htaccess", ".psd1", ".jenkinsfile",
}) | PERL | TCL | R_LANG | JULIA | NIM | BEAM - frozenset({".erl", ".hrl"}) | CRYSTAL | RUBY
# "--" so e comentario em SQL. Fora dele, "-----BEGIN PRIVATE KEY-----"
# comeca com "--" e nao pode ser pulado.
DASH_COMMENT = frozenset({".sql"}) | LUA | HASKELL | ADA
# Outros marcadores de comentario de linha, por tipo de arquivo.
EXTRA_COMMENT = {k: ("'", "rem ") for k in VB}
EXTRA_COMMENT.update({k: ("rem ", "::", "@rem ") for k in BATCH})
EXTRA_COMMENT.update({k: (";",) for k in AHK})
EXTRA_COMMENT.update({k: ("!",) for k in FORTRAN})
EXTRA_COMMENT.update({k: ("%",) for k in (".erl", ".hrl")})
EXTRA_COMMENT.update({k: (";",) for k in CLOJURE})
EXTRA_COMMENT.update({k: ("&&", "*") for k in XBASE})
# "*" sozinho nao entra: em C, "*out = malloc(n * size);" e codigo.
COMMENT_PREFIXES = ("//", "/*", "* ", "*/", "<!--")

# Pastas ignoradas ao varrer: dependencias de terceiros ou artefatos de build.
SKIP_DIRS = {
    "node_modules", "vendor", ".git", "__pycache__", "dist", "build",
    "target", ".venv", "venv", ".next", "coverage", ".idea", ".vscode",
}

# O proprio scanner contem, em texto, os padroes que ele procura.
SKIP_FILES = {"revisar_codigo.py"}

MAX_FILE_BYTES = 1_000_000   # acima disso quase sempre e minificado ou gerado
MAX_LINE_CHARS = 500         # idem para uma linha; so as regras de segredo exatas rodam nela
LONG_LINE_SCAN = 20_000      # teto do que se le de uma linha longa


@dataclass
class Rule:
    id: str
    severity: str                          # HIGH | MEDIUM | LOW
    pattern: "re.Pattern[str]"
    message: str                           # em pt-BR, para o usuario final
    fix: str                               # em pt-BR, o que fazer
    only: Optional[FrozenSet[str]] = None  # tipos de arquivo; None = todos
    secret: bool = False                   # a linha casada contem um segredo
    precise: bool = False                  # formato inconfundivel: roda tambem em comentario e linha longa
    skip: Optional[FrozenSet[str]] = None  # tipos onde o padrao significa outra coisa


def _rx(p: str, case: bool = False) -> "re.Pattern[str]":
    return re.compile(p, 0 if case else re.IGNORECASE)


# Inicio de comando SQL de verdade. "\bupdate\b" sozinho casa com
# "Profile updated"; exigir a forma do comando tira esse falso positivo.
def _sql_head(stop: str) -> str:
    return (r"\b(?:select\s[^" + stop + r"]{0,160}?\sfrom\s|insert\s+into\s|"
            r"update\s+[\w.`\[\]{}$>-]+\s+set\s|delete\s+from\s)")


_CMP = r"(?:=|<>|!=|<|>|\blike\b)"
_PHP_VAR = r"(?:\$\{?|\{\$)(?!wpdb->)[a-zA-Z_]"
_PHP_CONCAT_VAR = r"\$(?!wpdb->|table\b|tabela\b|prefix|this->table\b)"
_KEYWORDS = (r"(?:senha|password|passwd|pwd|(?<![a-z])pass|dbpass|secret|token|"
             r"api[_-]?key|apikey|access[_-]?key|client[_-]?secret|private[_-]?key|"
             r"secret[_-]?key|app[_-]?key|encryption[_-]?key)")

# Fim de uma chamada de comando: texto juntado com variavel, ou interpolado.
_SHELL_TAIL = r"""[^\n;]{0,200}?(?:["']\s*(?:\+|&|\.\.|\+\+|\^|~|//)\s*[\w$(]|["']\s*\.\s*\$|"[^"\n]*\$[A-Za-z_{]|#\{|\bpaste0?\s*\()"""
_SQL_CLAUSE = r"\b(?:where|values|set|and|or|like|in|limit|offset|having|by)\b"

RULES: List[Rule] = [
    # --- Segredos no codigo (OWASP A02/A04) ---
    Rule("secret-atribuido", "HIGH",
         _rx(_KEYWORDS + r"""["']?\s*\]?\s*(?:=>|:=|[:=])\s*["'](?P<v>[^"'{}$\s<|]{6,})["']"""
             r"""|\bdefine\s*\(\s*["']\w*(?:PASS|SENHA|SECRET|TOKEN|KEY|SALT)\w*["']\s*,\s*["'](?P<w>[^"'\s]{6,})["']"""
             r"""|#\s*define\s+\w*(?:PASS|SENHA|SECRET|TOKEN|KEY)\w*\s+"(?P<u>[^"\s]{6,})\""""),
         "Segredo escrito direto no codigo.",
         "Mova para variavel de ambiente (.env) e leia de la. Se ja foi pro Git, troque o segredo.",
         secret=True),
    Rule("conexao-php-literal", "HIGH",
         _rx(r"""\b(?:mysqli_connect|new\s+mysqli|mysql_connect|new\s+PDO)\s*\(\s*["'][^"']*["']\s*,\s*["'][^"']*["']\s*,\s*["'][^"'$]+["']"""),
         "Senha do banco escrita direto na chamada de conexao (PHP).",
         "Leia usuario e senha de variavel de ambiente (getenv ou $_ENV). Troque a senha se o arquivo ja foi publicado.",
         only=PHP, secret=True),
    Rule("chave-privada", "HIGH",
         _rx(r"-----BEGIN [A-Z0-9 ]{0,24}PRIVATE KEY", case=True),
         "Chave privada dentro do projeto.",
         "Remova o arquivo, gere uma chave nova e guarde fora do codigo.",
         secret=True, precise=True),
    Rule("aws-key", "HIGH",
         _rx(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b", case=True),
         "Credencial de nuvem exposta no codigo.",
         "Revogue a credencial agora e recrie via variavel de ambiente.",
         secret=True, precise=True),
    Rule("token-de-servico", "HIGH",
         _rx(r"\b(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|glpat-[A-Za-z0-9_-]{20,}|"
             r"[sr]k_live_[A-Za-z0-9]{16,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}|"
             r"APP_USR-[0-9a-f-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sb_secret_[A-Za-z0-9_-]{16,})", case=True),
         "Chave de servico externo (GitHub, Stripe, Google, Mercado Pago, Slack, Supabase ou IA) exposta.",
         "Revogue a chave no painel do servico agora, gere outra e leia de variavel de ambiente.",
         secret=True, precise=True),
    Rule("conexao-com-senha", "HIGH",
         _rx(r"""\b(?:mysql|mariadb|postgres(?:ql)?|mongodb(?:\+srv)?|rediss?|amqps?|sqlserver|mssql)://[^\s:'"/@]+:(?![${<%\[])[^\s@'"{}]+@"""),
         "String de conexao com usuario e senha embutidos.",
         "Monte a conexao a partir de variaveis de ambiente.",
         secret=True, precise=True),
    Rule("segredo-em-config", "MEDIUM",
         _rx(r"""^\s*(?:(?:export|ENV|ARG|@?set)\s+"?)?["']?[\w.\-]*(?:password|passwd|pwd|senha|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)[\w.\-]*["']?\s*[:=]\s*(?P<v>[^\s"'#${<%*!\[][^\s"'#]{5,})\s*(?:#.*)?$"""),
         "Possivel segredo em arquivo de configuracao.",
         "Se o arquivo vai para o Git, deixe o valor vazio aqui e ponha o valor real no .env, que fica fora do Git.",
         only=CONFIG | BATCH | frozenset({".sh", ".bash", ".dockerfile"}), secret=True),

    # --- SQL montado por concatenacao (OWASP A05) ---
    Rule("sql-concat-php", "HIGH",
         _rx(_sql_head(r";\n") + r"""[^;\n]{0,200}?["']\s*\.\s*""" + _PHP_CONCAT_VAR
             + r"""|\b(?:where|and|or)\s+[\w.`]+\s*""" + _CMP + r"""\s*'?%?\s*["']\s*\.\s*\$"""
             + r"""|\bvalues\s*\(\s*'?["']\s*\.\s*\$"""),
         "SQL montado juntando texto com variavel (PHP).",
         "Use prepared statement do PDO com placeholders (?) e bindValue.",
         only=PHP),
    Rule("sql-interp-php", "HIGH",
         _rx(r'"[\s(]*' + _sql_head(r'"\n')
             + r"""[^"\n]{0,200}?(?:=|<|>|\(|,|\blike\s|\bin\s)\s*\(?\s*'?%?\s*""" + _PHP_VAR
             + r"""|^\s*(?:where|and|or|set|on)\s+[\w.`]+\s*""" + _CMP + r"""\s*'?%?\s*""" + _PHP_VAR
             + r"""|^\s*values\s*\(\s*'?""" + _PHP_VAR),
         "SQL com variavel interpolada dentro da string (PHP).",
         "Use prepared statement com placeholders.",
         only=PHP),
    Rule("sql-concat", "HIGH",
         _rx(_sql_head(r";\n") + r"""[^;\n]{0,200}?["']\s*\+\s*[A-Za-z_(]"""
             + r"""|\b(?:where|and|or)\s+[\w.`"\[\]]+\s*""" + _CMP + r"""\s*'?%?\s*["']\s*\+\s*[A-Za-z_(]"""),
         "SQL montado juntando texto com variavel.",
         "Use consulta parametrizada: o valor vai separado, nunca dentro do texto do SQL."),
    Rule("sql-fstring-py", "HIGH",
         _rx(r"""\b(?:execute|executemany|raw|text)\s*\(\s*f["']"""
             r"""|\b(?:execute|executemany)\s*\(\s*["'][^"'\n]*["']\s*(?:%\s*[\w(]|\.format\s*\()"""),
         "SQL montado com f-string, % ou format (Python).",
         "Use cursor.execute(sql, params) com %s ou :nome.",
         only=PY),
    Rule("sql-template-js", "HIGH",
         # Template com tag (sql`...`, Prisma.sql`...`) e parametrizado pela
         # biblioteca; so o template sem tag e concatenacao.
         _rx(r"(?<![\w$)\]])`\s*(?:select\s|insert\s+into\s|update\s+\S+\s+set\s|delete\s+from\s)[^`]*\$\{"),
         "SQL montado com template string (JavaScript).",
         "Use query parametrizada: connection.execute(sql, [valores]).",
         only=JS),
    Rule("sql-concat-java", "HIGH",
         _rx(r"""\b(?:executeQuery|executeUpdate|createQuery|createNativeQuery|prepareStatement)\s*\(\s*["'][^"']*["']\s*\+"""),
         "SQL montado por concatenacao (Java).",
         "Use PreparedStatement com ? ou parametros nomeados no JPA."),

    # --- Execucao dinamica, inclusao e shell (OWASP A05) ---
    Rule("eval-dinamico", "HIGH",
         _rx(r"\b(?:eval|assert|exec|system|passthru|shell_exec|popen|proc_open)\s*\(\s*\$"),
         "Execucao de codigo ou comando montado com dado de entrada (PHP).",
         "Nao execute string vinda do usuario. Use lista de valores permitidos.",
         only=PHP),
    Rule("include-dinamico", "HIGH",
         _rx(r"\b(?:include|require)(?:_once)?\s*\(?\s*\$_(?:GET|POST|REQUEST|COOKIE)"),
         "Arquivo incluido a partir de dado do usuario (PHP).",
         "Escolha o arquivo por uma lista fixa de nomes permitidos, nunca pelo texto que chegou."),
    Rule("shell-true", "HIGH",
         _rx(r"\bshell\s*=\s*True\b"),
         "Comando de sistema executado atraves do shell (Python).",
         "Use subprocess.run([lista, de, argumentos]) com shell=False.",
         only=PY),
    Rule("os-system", "MEDIUM",
         _rx(r"\bos\.(?:system|popen)\s*\("),
         "Comando de sistema passado como texto para o shell (Python).",
         "Use subprocess.run com lista de argumentos. Nunca monte o comando com dado que veio de fora.",
         only=PY),
    Rule("child-process-exec", "HIGH",
         _rx(r"""child_process\.exec(?:Sync)?\s*\(|\bexec(?:Sync)?\s*\(\s*(?:`[^`]*\$\{|["'][^"']*["']\s*\+)"""),
         "Comando de sistema com string montada (Node.js).",
         "Use execFile com array de argumentos.",
         only=JS),
    Rule("eval-js-py", "MEDIUM",
         _rx(r"\beval\s*\(|\bnew\s+Function\s*\("),
         "Uso de eval.",
         "Substitua por logica explicita ou JSON.parse.",
         skip=XBASE),

    # --- Hash e criptografia fraca (OWASP A04) ---
    Rule("hash-fraco-senha", "HIGH",
         _rx(r"\b(?:md5|sha1)\s*\([^)\n]{0,60}(?:pass|senha|pwd|secret)"),
         "Senha protegida com hash fraco (MD5 ou SHA-1).",
         "Use password_hash com PASSWORD_ARGON2ID, bcrypt ou argon2-cffi."),
    Rule("hash-fraco", "MEDIUM",
         _rx(r"""\b(?:md5|sha1)\s*\(|getInstance\s*\(\s*"(?:MD5|SHA-?1)"|createHash\s*\(\s*["'](?:md5|sha1)["']"""),
         "Uso de MD5 ou SHA-1.",
         "Se for para senha ou assinatura, troque. Para checksum simples, tudo bem."),
    Rule("random-inseguro", "MEDIUM",
         _rx(r"\b(?:rand|mt_rand|uniqid|Math\.random|random\.random|random\.randint)\s*\("),
         "Numero aleatorio previsivel usado onde pode virar token.",
         "Para token ou senha use random_bytes, secrets ou crypto.randomBytes."),
    Rule("tls-desligado", "HIGH",
         _rx(r"""\bverify\s*=\s*False\b|rejectUnauthorized\s*:\s*false|CURLOPT_SSL_VERIFY(?:PEER|HOST)\s*,\s*(?:false|0)\b|InsecureSkipVerify\s*:\s*true|NODE_TLS_REJECT_UNAUTHORIZED["'\]\s]*=\s*["']?0"""
             r"""|danger_accept_invalid_(?:certs|hostnames)\s*\(\s*true|ServerCertificateCustomValidationCallback\s*=[^;\n]*=>\s*true\b"""
             r"""|badCertificateCallback\s*=[^;\n]*=>\s*true\b|hostnameVerifier\s*\{\s*\w+\s*,\s*\w+\s*->\s*true"""
             r"""|setHostnameVerifier\s*\(\s*\(?\s*\w+\s*,\s*\w+\s*\)?\s*->\s*true|NoopHostnameVerifier|ALLOW_ALL_HOSTNAME_VERIFIER"""
             r"""|TrustServerCertificate\s*=\s*(?:true|yes)\b|VerifyMode\s*:=\s*\[\s*\]|\{\s*verify\s*,\s*verify_none\s*\}"""
             r"""|SSL_VERIFY_NONE\b|usesCleartextTraffic\s*=\s*.true|cleartextTrafficPermitted\s*=\s*.true"""
             r"""|\bcurl\b[^\n|]*\s(?:-[a-zA-Z]*k[a-zA-Z]*|--insecure)\b|\bwget\b[^\n|]*--no-check-certificate"""),
         "Verificacao do certificado HTTPS desligada.",
         "Nunca desligue em producao. Corrija o certificado."),

    # --- Saida sem escape (OWASP A05) ---
    Rule("echo-sem-escape", "HIGH",
         _rx(r"""(?:\becho|\bprint|<\?=)\s*\(?\s*\$_(?:GET|POST|REQUEST|COOKIE)"""),
         "Dado do usuario impresso na tela sem tratamento (PHP).",
         "Use htmlspecialchars($v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8').",
         only=PHP),
    Rule("innerhtml", "MEDIUM",
         _rx(r"\.(?:inner|outer)HTML\s*\+?=|dangerouslySetInnerHTML|v-html\s*=|\bdocument\.write\s*\("),
         "HTML inserido direto na pagina.",
         "Use textContent, ou sanitize antes de inserir.",
         only=JS),
    Rule("autoescape-off", "HIGH",
         _rx(r"(?:\|\s*raw\b|\|\s*safe\b|\bhtml_safe\b|autoescape\s*=\s*False|\{!!)"),
         "Escape automatico do template desligado.",
         "Deixe o template escapar. So desligue para HTML que voce mesmo gerou.",
         only=TEMPLATES),

    # --- Configuracao insegura (OWASP A02) ---
    Rule("debug-ligado", "MEDIUM",
         _rx(r"""\bDEBUG\s*=\s*True\b|display_errors["']?\s*[,=]\s*["']?(?:1|On|true)\b|APP_DEBUG\s*=\s*true\b"""),
         "Modo de depuracao ligado.",
         "Desligue em producao. Erro detalhado vai pro log, nao pra tela."),
    Rule("cors-aberto", "HIGH",
         _rx(r"""Access-Control-Allow-Origin["'\s:,]+\*|\borigin\s*:\s*["']\*["']"""),
         "CORS liberado para qualquer site.",
         "Liste os dominios permitidos. Nunca * junto com credenciais."),
    Rule("permissao-777", "HIGH",
         _rx(r"chmod\s+(?:-R\s+)?0?777\b|chmod\s*\(\s*[^,]+,\s*0o?777\b"),
         "Permissao 777 em arquivo ou pasta.",
         "Use 644 para arquivos e 755 para pastas."),
    Rule("jwt-alg-none", "HIGH",
         _rx(r"""\balg["'\s:=]+["']?none\b|algorithms\s*[:=]\s*\[\s*["']none"""),
         "JWT aceitando assinatura vazia.",
         "Fixe o algoritmo esperado e rejeite 'none'."),

    # --- Desserializacao (OWASP A08) ---
    Rule("desserializacao", "HIGH",
         _rx(r"\bunserialize\s*\(|\bpickle\.loads?\s*\(|\bMarshal\.load\s*\(|\bnew\s+ObjectInputStream\s*\("),
         "Desserializacao de dado nao confiavel.",
         "Use JSON com validacao de schema."),
    Rule("yaml-load", "HIGH",
         _rx(r"\byaml\.load\s*\((?!.*SafeLoader)"),
         "yaml.load sem SafeLoader executa codigo que vier no arquivo (Python).",
         "Use yaml.safe_load.",
         only=PY),

    # --- Erro engolido (OWASP A10) ---
    Rule("except-vazio", "MEDIUM",
         _rx(r"except\b[^:\n]*:\s*pass\b|catch\s*\([^)]*\)\s*\{\s*\}|catch\s*\{\s*\}"),
         "Erro capturado e ignorado em silencio.",
         "Registre no log e decida: tentar de novo, ou recusar a operacao."),
    Rule("except-generico", "MEDIUM",
         _rx(r"^\s*except\s*:\s*$"),
         "except sem tipo captura tudo, ate Ctrl+C e erros de memoria (Python).",
         "Capture a excecao especifica esperada, por exemplo except ValueError.",
         only=PY),
    Rule("supressao-arroba", "MEDIUM",
         _rx(r"(?<![\w'\"])@(?:mysqli_|file_get_contents|fopen|unlink|include|require)"),
         "Erro suprimido com @ (PHP).",
         "Trate o erro explicitamente. O @ esconde o problema.",
         only=PHP),

    # --- C / C++: memoria e entrada hostil (CERT C, C++ Core Guidelines) ---
    Rule("c-funcao-insegura", "HIGH",
         _rx(r"\b(?:strcpy|strcat|sprintf|vsprintf|gets|stpcpy)\s*\("),
         "Funcao de string que escreve sem saber o tamanho do destino (C/C++).",
         "Troque por snprintf ou pela versao com tamanho do destino, e confira o retorno.",
         only=C_FAMILY),
    Rule("c-scanf-sem-limite", "HIGH",
         _rx(r"\b[fs]?scanf\s*\([^;]{0,120}%s"),
         "scanf com %s sem largura maxima grava alem do buffer.",
         "Informe a largura (%31s para um buffer de 32) ou use fgets.",
         only=C_FAMILY),
    Rule("c-comando-shell", "HIGH",
         _rx(r"\b(?:system|popen|_popen|_wsystem|execlp|execvp|ShellExecuteA|ShellExecuteW)\s*\("),
         "Comando de sistema disparado a partir do codigo nativo.",
         "Use execve ou CreateProcess com os argumentos separados. Nunca monte a linha de comando com dado que veio de fora.",
         only=C_FAMILY),
    Rule("c-alloc-multiplicacao", "MEDIUM",
         _rx(r"\b(?:malloc|realloc|alloca)\s*\([^;]{0,80}?[\w\)]\s*\*\s*[\w(]"),
         "Tamanho de alocacao calculado por multiplicacao: pode estourar e alocar de menos.",
         "Use ckd_mul (C23) ou __builtin_mul_overflow e recuse o arquivo se a conta estourar.",
         only=C_FAMILY),
    Rule("c-alloca", "MEDIUM",
         _rx(r"\balloca\s*\("),
         "alloca reserva na pilha e nao avisa quando ela acaba.",
         "Use malloc com verificacao de retorno, ou um buffer fixo com tamanho validado.",
         only=C_FAMILY),
    Rule("c-fread-struct", "MEDIUM",
         _rx(r"\b(?:fread|recv)\s*\(\s*&"),
         "Bytes lidos direto para dentro de uma struct ou de um numero.",
         "Leia para um buffer de bytes e monte cada campo com deslocamento explicito. Layout e ordem dos bytes mudam entre plataformas, e o arquivo fica ambiguo.",
         only=C_FAMILY),
    Rule("c-memcpy-tamanho-externo", "LOW",
         _rx(r"\bmemcpy\s*\([^;]{0,120}\b(?:len|length|size|count|tamanho)\w*\s*\)"),
         "memcpy com tamanho vindo de variavel.",
         "Valide o tamanho contra a capacidade do destino na mesma expressao, antes de copiar.",
         only=C_FAMILY),
    Rule("march-native", "HIGH",
         _rx(r"-march\s*=\s*native|-mtune\s*=\s*native|-xHost|target-cpu\s*=\s*native"),
         "Compilacao mirando a CPU da maquina que compilou.",
         "O binario morre com instrucao invalida em processador mais antigo. Use uma base portavel (-march=x86-64-v2) e escolha o caminho otimizado em tempo de execucao. So aceite em build local de teste, nunca no que voce distribui."),
    Rule("rust-unsafe", "MEDIUM",
         _rx(r"\bunsafe\s*(?:\{|fn\b|impl\b)"),
         "Bloco unsafe em Rust.",
         "Confirme que tem um comentario // SAFETY: logo acima dizendo qual garantia torna o bloco correto, e rode cargo miri test.",
         only=frozenset({".rs"})),
    Rule("cpp-u8path", "LOW",
         _rx(r"\b(?:std::filesystem::|fs::)u8path\s*\("),
         "u8path foi marcado obsoleto no C++20.",
         "Monte o path a partir de char8_t ou de std::u8string.",
         only=C_FAMILY),

    # --- Interface grafica: seguranca de webview e virtualizacao ---
    Rule("webview-context-isolation", "HIGH",
         _rx(r"contextIsolation\s*:\s*false"),
         "Isolamento de contexto desligado no webview (Electron).",
         "Deixe contextIsolation: true e exponha so o necessario via contextBridge no preload."),
    Rule("webview-node-integration", "HIGH",
         _rx(r"nodeIntegration\s*:\s*true"),
         "Pagina do webview com acesso direto ao Node (Electron).",
         "Deixe nodeIntegration: false e sandbox: true. Qualquer conteudo remoto carregado vira execucao de codigo na maquina."),
    Rule("webview-security-off", "HIGH",
         _rx(r"webSecurity\s*:\s*false|allowRunningInsecureContent\s*:\s*true"),
         "Protecoes de origem do webview desligadas.",
         "Nunca desligue. Se e por causa de arquivo local, use um protocolo customizado registrado."),
    Rule("tauri-ipc-remoto", "HIGH",
         _rx(r"dangerousRemoteDomainIpcAccess|dangerousDisableAssetCspModification"),
         "Acesso remoto ao canal de comandos do Tauri liberado.",
         "Remova. Isso deixa uma pagina remota chamar as funcoes nativas do seu programa."),
    Rule("qt-ssl-ignorado", "HIGH",
         _rx(r"ignoreSslErrors\s*\("),
         "Verificacao de certificado TLS ignorada (Qt).",
         "Nunca em producao. Corrija o certificado ou instale a cadeia correta.",
         only=QT),
    Rule("ui-widget-nao-virtualizado", "MEDIUM",
         _rx(r"\b(?:QTableWidget|QListWidget|QTreeWidget)\b", case=True),
         "Widget que cria um objeto por linha: trava quando a lista cresce.",
         "Use QAbstractItemModel com QTableView ou QTreeView. Acima de mil linhas isso deixa de ser detalhe.",
         only=QT),
    Rule("ui-loop-reentrante", "MEDIUM",
         _rx(r"processEvents\s*\(|\bDoEvents\s*\(|\bdo_events\s*\("),
         "Loop de eventos rodado a mao para a janela nao congelar.",
         "Isso reentra nos seus proprios tratadores e gera bug intermitente. Mova o trabalho pesado para uma thread."),
    # --- Linguagens cobertas na 2.2.0: SQL montado (OWASP A05) ---
    Rule("sql-concat-outros", "HIGH",
         # & (VB, VBA, Nim), .. (Lua), || e // (SAS, Fortran), ++ ^ ~ <> (Haskell, OCaml, D, Elixir).
         # Exige uma clausula SQL antes da juncao: "selecione um item da lista: " & x nao e SQL.
         _rx(_sql_head(r";\n") + r"[^\n]{0,200}?" + _SQL_CLAUSE
             + r"""[^\n]{0,120}?["']\s*(?:&|\.\.|\|\||//|\+\+|\^|~|<>)\s*[A-Za-z_(]"""),
         "SQL montado juntando texto com variavel.",
         "Use consulta parametrizada: o valor vai separado, nunca dentro do texto do SQL.",
         only=VB | NIM | LUA | SAS | FORTRAN | HASKELL | OCAML | DLANG | BEAM),
    Rule("sql-interpolado", "HIGH",
         # "$x", "${x}", "#{x}" e "\(x)" num SQL com aspas duplas, depois de uma clausula
         # (where, values, set...). fr"..." (doobie) e sql"..." sao parametrizados pela biblioteca.
         _rx(r'(?<!fr)(?<!sql)(?<!")"[^"\n]*?' + _sql_head(r'"\n') + r'[^"\n]*?' + _SQL_CLAUSE
             + r'[^"\n]*?(?:\$\{?[A-Za-z_]|#\{|\\\()'),
         "SQL montado com interpolacao de variavel dentro do texto.",
         "Use consulta parametrizada (? ou :nome) e passe o valor separado.",
         only=PERL | TCL | RUBY | CRYSTAL | BEAM | KOTLIN | DART | SCALA | JULIA | PS | SH | SWIFT),
    Rule("sql-format", "HIGH",
         _rx(r"""\b(?:Sprintf|format!|String\.format|Printf\.sprintf|paste0?|sprintf|glue)\s*\(\s*&?["']""" + _sql_head(r"\"'\n")
             + r"[^\n]*?" + _SQL_CLAUSE + r"""[^\n]*?(?:%[sdvq]|\{[\w:]*\}|["']\s*,)"""),
         "SQL montado com funcao de formatacao de texto.",
         "Use consulta parametrizada: o valor vai separado, nunca dentro do texto do SQL.",
         only=GO | RUST | OCAML | JAVA | KOTLIN | SCALA | HASKELL | R_LANG),
    Rule("sql-raw-dotnet", "HIGH",
         # FromSql($"...{x}") e FromSqlInterpolated sao parametrizados; os "Raw" nao.
         _rx(r"""\b(?:FromSqlRaw|ExecuteSqlRaw(?:Async)?|SqlQueryRaw)\s*\(\s*(?:\$@?"|@\$"|"[^"\n]*"\s*\+)"""),
         "SQL cru do Entity Framework montado com interpolacao ou concatenacao.",
         "Troque por FromSql($\"... {valor}\") ou ExecuteSql, que viram parametros.",
         only=CS),
    Rule("sql-rails-interp", "HIGH",
         _rx(r"""\b(?:where|find_by_sql|order|having|joins|group|exec_query|select_all|pluck)\s*\(\s*"[^"\n]*#\{"""),
         "Consulta do Rails montada com interpolacao.",
         "Use where(\"nome = ?\", valor) ou where(nome: valor).",
         only=RUBY),
    Rule("sql-fragment-const", "HIGH",
         _rx(r"""\bFragment\.const0?\s*\(\s*s\""""),
         "Fragmento SQL do doobie montado com interpolacao de texto.",
         "Use fr\"... $valor\", que vira parametro.",
         only=SCALA),
    Rule("sql-dinamico-legado", "MEDIUM",
         _rx(r"""\bEXEC\s+SQL\s+(?:PREPARE\b[^\n]*\bFROM\s+:|EXECUTE\s+IMMEDIATE\s+:)|\b(?:WHERE|FROM)\s+\(\s*\w+\s*\)"""),
         "SQL dinamico em COBOL, RPG ou ABAP.",
         "Prefira SQL estatico com variaveis de host. Se for dinamico, valide contra lista permitida (ABAP: cl_abap_dyn_prg).",
         only=COBOL_RPG | ABAP),
    Rule("mongo-filtro-cru", "HIGH",
         _rx(r"""\.(?:find|findOne|findOneAndUpdate|updateOne|updateMany|deleteOne|deleteMany|countDocuments)\(\s*req\.(?:body|query|params)\s*[,)]"""),
         "Objeto da requisicao usado direto como filtro do MongoDB (injecao de operador).",
         "Monte o filtro campo a campo, convertendo cada valor: { email: String(req.body.email) }.",
         only=JS),

    # --- Linguagens cobertas na 2.2.0: comando de sistema montado (OWASP A05) ---
    Rule("shell-montado", "HIGH",
         # Nome exato (maiusculas contam) em forma de chamada: "System.out.println" e "Shell: " em texto nao sao comando.
         _rx(r"""(?:(?<!["'\w.])(?:os\.execute|io\.popen|system2?|exec|qx|spawn|IO\.popen|Shell|ShellExecute(?:Ex)?[AW]?|WinExec"""
             r"""|CreateProcess[AW]?|shell|execute_command_line|callCommand|spawnCommand|Sys\.command|Unix\.system"""
             r"""|Unix\.open_process(?:_in)?|executeShell|spawnShell|execCmd|execShellCmd|execCmdEx)\s*[(\s]"""
             r"""|:os\.cmd\s*\(|Runtime\.getRuntime\(\)\.exec\s*\(|\bcall\s+system\s*\(|\.Run\s*\(?\s*")""" + _SHELL_TAIL, case=True),
         "Comando de sistema montado com dado variavel.",
         "Chame o programa com os argumentos separados, sem shell, e valide o valor contra uma lista permitida.",
         only=LUA | PERL | VB | PASCAL | R_LANG | FORTRAN | HASKELL | OCAML | DLANG | NIM | BEAM
         | JAVA | KOTLIN | SCALA | GROOVY | RUBY | CRYSTAL),
    Rule("shell-montado", "HIGH",
         # Clipper/Harbour: RUN e um comando no inicio da linha.
         _rx(r"""(?:^\s*RUN\b|\b__Run\s*\(|\bhb_processRun\s*\()""" + _SHELL_TAIL),
         "Comando de sistema montado com dado variavel.",
         "Chame o programa com os argumentos separados (hb_processRun com lista) e valide o valor contra uma lista permitida.",
         only=XBASE),
    Rule("shell-crase", "HIGH",
         _rx(r"""`[^`\n]*(?:#\{|\$[A-Za-z_{])"""),
         "Comando de sistema entre crases com variavel dentro.",
         "Use system(\"programa\", arg1, arg2), que nao passa pelo shell.",
         only=RUBY | CRYSTAL | PERL),
    Rule("shell-c-montado", "HIGH",
         _rx(r"""\bexec\.Command(?:Context)?\s*\([^\n]*"(?:sh|bash|cmd(?:\.exe)?|powershell)"\s*,\s*"(?:-c|/c|-Command)"[^\n]*(?:"\s*\+|\+\s*"|Sprintf)"""
             r"""|\brun\s*\(\s*`(?:sh|bash)\s+-c\b|\bProcess\.run\s*\(\s*['"](?:sh|bash)['"]\s*,\s*\[\s*['"]-c['"]"""
             r"""|\bSeq\s*\(\s*"(?:sh|bash)"\s*,\s*"-c"|\bRun(?:Wait)?\s*,?\s*\(?\s*A_ComSpec\b[^\n]*['"]\s+[A-Za-z_%]"""),
         "Comando montado e passado para o shell (sh -c, cmd /c).",
         "Chame o programa direto, com os argumentos em lista, sem shell.",
         only=GO | JULIA | DART | SCALA | AHK),
    Rule("jenkins-sh-interpolado", "HIGH",
         _rx(r"""\bsh\s*\(?\s*(?:script\s*:\s*)?"[^"\n]*\$\{?\s*(?:params|env)\."""),
         "Parametro do Jenkins interpolado pelo Groovy dentro de um comando sh.",
         "Use aspas simples e deixe o shell ler a variavel: sh 'deploy \"$BRANCH\"'.",
         only=GROOVY),
    Rule("powershell-iex", "HIGH",
         _rx(r"""\b(?:Invoke-Expression|iex)\b\s*(?:\(|"[^"\n]*\$|\$)|\|\s*(?:iex|Invoke-Expression)\b"""),
         "Invoke-Expression executa texto montado ou baixado como codigo.",
         "Chame o comando direto (& comando -Parametro $valor). Para script baixado, salve, leia e so depois rode.",
         only=PS),
    Rule("shell-baixa-e-executa", "HIGH",
         _rx(r"""\b(?:curl|wget|irm|iwr|Invoke-RestMethod|Invoke-WebRequest)\b[^|\n]*\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b"""),
         "Script baixado da internet e executado direto, sem leitura.",
         "Baixe para um arquivo, confira o conteudo (e o hash, se publicado) e so depois execute.",
         only=SH | PS | frozenset({".dockerfile", ".yml", ".yaml"})),
    Rule("shell-eval", "HIGH",
         # eval "$(ssh-agent -s)" e uso comum de ferramenta conhecida; o risco e eval de variavel.
         _rx(r"""^\s*eval\s+"?\$(?!\()"""),
         "eval em shell executa o conteudo de uma variavel como comando.",
         "Use um array: cmd=(prog --opcao \"$valor\"); \"${cmd[@]}\".",
         only=SH),
    Rule("securestring-literal", "HIGH",
         _rx(r"""ConvertTo-SecureString\s+(?:-String\s+)?["'][^"'$]{4,}["'][^\n]*-AsPlainText"""),
         "Senha escrita no script e convertida com -AsPlainText.",
         "Peca a senha com Read-Host -AsSecureString ou use o Gerenciador de Credenciais do Windows.",
         only=PS, secret=True),

    # --- Linguagens cobertas na 2.2.0: codigo carregado em tempo de execucao ---
    Rule("codigo-dinamico", "HIGH",
         _rx(r"""\bloadstring\s*\(|\bload\s*\(\s*[^,()"']+\)"""),
         "Texto carregado e executado como codigo (Lua).",
         "Use load(texto, nome, \"t\", ambiente_restrito) e nunca entregue os, io ou require ao script.",
         only=LUA),
    Rule("codigo-dinamico", "HIGH",
         _rx(r"""&\(\s*\w"""),
         "Macro do Clipper/Harbour executa texto como codigo.",
         "Troque a macro por um bloco de codigo fixo ou por uma lista de opcoes permitidas.",
         only=XBASE),
    Rule("codigo-dinamico", "HIGH",
         _rx(r"""(?<![\w/."-])(?:read-string|load-string)\b|\(eval\s|\bEval\.(?:me|x|xy|xyz)\s*\(|GroovyShell\s*\([^)]*\)\s*\.evaluate|\beval\s*\(\s*parse\s*\("""),
         "Texto carregado e executado como codigo.",
         "Nao execute texto vindo de fora. Use um parser de dados (JSON, EDN, numero) ou uma lista de opcoes.",
         only=CLOJURE | GROOVY | R_LANG),
    Rule("beam-atomo-e-termo", "HIGH",
         _rx(r"""\b(?:String\.to_atom|List\.to_atom|binary_to_atom|list_to_atom)\s*\(|(?<![\w.])(?::erlang\.)?binary_to_term\s*\((?![^)\n]*:?safe)"""),
         "Atomo criado a partir de entrada (esgota a memoria da VM) ou termo desserializado sem :safe.",
         "Mapeie a entrada para atomos fixos e use binary_to_term(bin, [:safe]) ou Plug.Crypto.non_executable_binary_to_term.",
         only=BEAM),
    Rule("desserializacao-dotnet", "HIGH",
         _rx(r"""\bnew\s+(?:BinaryFormatter|SoapFormatter|NetDataContractSerializer|LosFormatter|ObjectStateFormatter)\b"""
             r"""|TypeNameHandling\s*=\s*TypeNameHandling\.(?:All|Objects|Auto|Arrays)"""),
         "Desserializador .NET que executa tipos escolhidos pelo dado.",
         "Use System.Text.Json com tipos fixos. BinaryFormatter lanca excecao a partir do .NET 9.",
         only=CS | FSHARP | VB),
    Rule("perl-open-2-args", "MEDIUM",
         _rx(r"""\bopen\s*\(?\s*(?:my\s+)?[$\w]+\s*,\s*\$\w+\s*\)"""),
         "open com dois argumentos: o nome do arquivo pode virar comando (\"| rm -rf\").",
         "Use a forma de tres argumentos: open(my $fh, '<', $caminho).",
         only=PERL),
    Rule("tcl-expr-sem-chaves", "MEDIUM",
         _rx(r"""\bexpr\s+(?!\{)[^\]\n]*\$"""),
         "expr sem chaves avalia o valor da variavel de novo (injecao de codigo).",
         "Sempre use chaves: expr {$a + $b}.",
         only=TCL),
    Rule("apps-script-sem-escape", "MEDIUM",
         _rx(r"""<\?!=\s*(?!include\b)"""),
         "<?!= imprime sem escape no HtmlService (Apps Script).",
         "Use <?= valor ?>, que escapa. Deixe <?!= so para include de arquivo seu.",
         only=GAS | frozenset({".html"})),
    Rule("pg-hba-trust", "HIGH",
         _rx(r"""^\s*host(?:ssl|nossl)?\s+\S+\s+\S+\s+(?!127\.0\.0\.1/32\b|::1/128\b|samehost\b)\S+\s+trust\b"""),
         "PostgreSQL aceita conexao de rede sem senha (trust).",
         "Troque trust por scram-sha-256 nas linhas host.",
         only=CONFIG),
    Rule("firebase-regra-aberta", "HIGH",
         _rx(r"""allow\s+(?:read\s*,\s*)?write(?:\s*,\s*read)?\s*:\s*if\s+true\s*;"""),
         "Regra do Firebase deixa qualquer pessoa gravar.",
         "Exija login e dono: allow write: if request.auth != null && request.auth.uid == userId;",
         only=frozenset({".rules"})),
    Rule("seguranca-desligada-nativo", "MEDIUM",
         _rx(r"""@setRuntimeSafety\s*\(\s*false|\bpragma\s+Suppress\s*\(\s*All_Checks|-gnatp\b"""),
         "Verificacoes de seguranca do compilador desligadas (Zig ou Ada).",
         "Desligue so no trecho medido como gargalo, com comentario explicando, nunca no projeto inteiro.",
         only=ZIG | ADA | frozenset({".gpr"})),
]

# Quando a regra da esquerda casa numa linha, a da direita e redundante.
SUPERSEDES = {
    "hash-fraco-senha": "hash-fraco",
    "eval-dinamico": "eval-js-py",
    "secret-atribuido": "segredo-em-config",
    "conexao-com-senha": "segredo-em-config",
    "token-de-servico": "segredo-em-config",
    "sql-concat-java": "sql-concat",
    "c-alloca": "c-alloc-multiplicacao",
    "sql-raw-dotnet": "sql-concat",
    "codigo-dinamico": "eval-js-py",
    "shell-montado": "c-comando-shell",
}

SECRET_RULES = [r for r in RULES if r.secret]
OMITTED_EXCERPT = "[trecho omitido: a linha contem um possivel segredo]"

# Valor que e rotulo, exemplo ou nome de campo, nao segredo.
_PLACEHOLDER = re.compile(
    r"^(?:your|seu|sua|example|exemplo|placeholder|change|troque|coloque|insira|"
    r"xxx|required|string|bearer|hidden|undefined|null|none|true|false)"
    r"|^(.)\1+$",
    re.IGNORECASE)
# Rotulo de tela: so letras, podendo terminar em pontuacao ("Esqueceu?").
_LABEL = re.compile(r"^[^\W\d_]+[?!:.]?$")
# Para ESCONDER o trecho o criterio e mais largo que para acusar: basta um
# nome com cara de segredo recebendo qualquer valor. Esconder demais custa
# so o trecho; esconder de menos vaza a senha.
_HIDE = re.compile(
    r"""(?:senha|pass|pwd|secret|segredo|token|key|chave|credential|auth)\w*["'\])]*\s*(?:=>|[:=,])\s*\S""",
    re.IGNORECASE)
_KEYWORD_ONLY = re.compile(r"^" + _KEYWORDS + r"$", re.IGNORECASE)

# Nomes que indicam arquivo de exemplo, que vai para o Git.
_EXAMPLE_MARKS = ("example", "sample", "template", "dist", "default")


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    message: str
    fix: str
    excerpt: str


def _is_placeholder(value: Optional[str], config: bool = False) -> bool:
    if not value:
        return False
    if _PLACEHOLDER.search(value) or _KEYWORD_ONLY.match(value):
        return True
    # Em arquivo de configuracao, numero puro e prazo ou tamanho (token_ttl: 3600).
    if config and value.isdigit():
        return True
    # Uma palavra curta so de letras e rotulo de tela ("Esqueceu?"), nao senha.
    return len(value) < 12 and bool(_LABEL.match(value))


def kind_of(path: Path) -> str:
    """Tipo do arquivo para efeito de regras: a extensao, ou o equivalente pelo nome."""
    name = path.name
    if name.lower().startswith(".env"):
        return ".env"
    if name in CODE_NAMES:
        return CODE_NAMES[name]
    return path.suffix.lower()


def is_secret_home(path: Path) -> bool:
    """Arquivo onde segredo e esperado e que nao vai para o Git."""
    name = path.name.lower()
    if name == "wp-config.php":
        return True
    return name.startswith(".env") and not any(m in name for m in _EXAMPLE_MARKS)


def iter_files(paths: List[str], notes: Dict[str, int]) -> List[Path]:
    """Coleta arquivos analisaveis. Caminho invalido vira aviso, nao excecao."""
    found: List[Path] = []
    seen = set()

    def add(c: Path, explicit: bool) -> None:
        key = os.path.abspath(str(c))
        if key in seen:
            return
        seen.add(key)
        if c.name in SKIP_FILES:
            return
        if not explicit and c.suffix.lower() not in CODE_SUFFIXES \
                and c.name not in CODE_NAMES and not c.name.lower().startswith(".env"):
            return
        try:
            if c.stat().st_size > MAX_FILE_BYTES:
                notes["grandes"] += 1
                print("aviso: arquivo acima de 1 MB, nao analisado: %s" % c, file=sys.stderr)
                return
        except OSError:
            return
        found.append(c)

    for raw in paths:
        p = Path(raw)
        if not p.exists():
            notes["ausentes"] += 1
            print("aviso: caminho nao encontrado, ignorado: %s" % raw, file=sys.stderr)
            continue
        if p.is_file():
            add(p, True)
            continue
        # os.walk com poda: nao desce em node_modules nem em vendor. A poda
        # vale so abaixo da pasta pedida, entao um projeto que mora dentro
        # de uma pasta chamada "build" e analisado normalmente.
        for root, dirs, names in os.walk(str(p)):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(names):
                add(Path(root) / name, False)
    return found


def read_text(path: Path) -> Optional[str]:
    """Le o arquivo como texto. Devolve None para binario ou ilegivel."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        print("aviso: nao consegui ler %s: %s" % (path, exc), file=sys.stderr)
        return None
    # Arquivo salvo pelo Bloco de Notas ou pelo PowerShell antigo vem em
    # UTF-16; lido como UTF-8 ele vira lixo e o scanner diria "OK" sem ter lido nada.
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    if b"\x00" in data[:4096]:
        return None
    if data[:3] == b"\xef\xbb\xbf":
        data = data[3:]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        # PHP legado brasileiro costuma estar em Latin-1.
        return data.decode("cp1252", errors="replace")


def _is_comment(stripped: str, kind: str) -> bool:
    if stripped == "*" or stripped.startswith(COMMENT_PREFIXES):
        return True
    if kind in HASH_COMMENT and stripped.startswith("#"):
        return True
    if kind in DASH_COMMENT and stripped.startswith("--"):
        return True
    extra = EXTRA_COMMENT.get(kind)
    return bool(extra) and stripped.lower().startswith(extra)


def scan_file(path: Path, notes: Dict[str, int]) -> List[Finding]:
    text = read_text(path)
    if text is None:
        notes["binarios"] += 1
        return []

    kind = kind_of(path)
    secret_home = is_secret_home(path)
    findings: List[Finding] = []

    for n, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line
        precise_only = False
        if len(line) > MAX_LINE_CHARS:
            notes["linhas_longas"] += 1
            line = line[:LONG_LINE_SCAN]
            precise_only = True
        stripped = line.strip()
        if not stripped:
            continue
        if _is_comment(stripped, kind):
            precise_only = True

        # A omissao do trecho e decidida pela linha, nao pela regra: qualquer
        # padrao de segredo, de qualquer linguagem, esconde a linha inteira.
        hide = (secret_home or bool(_HIDE.search(line))
                or any(r.pattern.search(line) for r in SECRET_RULES))

        hits: List[Rule] = []
        for rule in RULES:
            if precise_only and not rule.precise:
                continue
            if rule.only is not None and kind not in rule.only:
                continue
            if rule.skip is not None and kind in rule.skip:
                continue
            if rule.secret and secret_home:
                continue
            m = rule.pattern.search(line)
            if not m:
                continue
            if rule.id in ("secret-atribuido", "segredo-em-config"):
                groups = m.groupdict()
                if _is_placeholder(groups.get("v") or groups.get("w") or groups.get("u"),
                                   config=rule.id == "segredo-em-config"):
                    continue
            hits.append(rule)

        hit_ids = {r.id for r in hits}
        for rule in hits:
            if any(SUPERSEDES.get(other) == rule.id for other in hit_ids):
                continue
            findings.append(Finding(
                file=str(path),
                line=n,
                rule=rule.id,
                severity=rule.severity,
                message=rule.message,
                fix=rule.fix,
                excerpt=OMITTED_EXCERPT if hide else stripped[:160],
            ))
    return findings


SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _notes_line(notes: Dict[str, int]) -> str:
    parts: List[str] = []
    if notes["grandes"]:
        parts.append("%d arquivo(s) acima de 1 MB" % notes["grandes"])
    if notes["binarios"]:
        parts.append("%d arquivo(s) binario(s)" % notes["binarios"])
    if notes["linhas_longas"]:
        parts.append("%d linha(s) acima de %d caracteres (so regras de segredo)"
                     % (notes["linhas_longas"], MAX_LINE_CHARS))
    if notes["ausentes"]:
        parts.append("%d caminho(s) nao encontrado(s)" % notes["ausentes"])
    return "Nao analisado: " + "; ".join(parts) + "." if parts else ""


def report_text(findings: List[Finding], files_scanned: int, notes: Dict[str, int]) -> None:
    skipped = _notes_line(notes)
    if not findings:
        print("OK. %d arquivo(s) analisado(s), nenhum padrao inseguro encontrado." % files_scanned)
        if skipped:
            print(skipped)
        print("Isso nao substitui o checklist do SKILL.md.")
        return

    highs = sum(1 for f in findings if f.severity == "HIGH")
    print("%d achado(s) em %d arquivo(s). HIGH: %d." % (len(findings), files_scanned, highs))
    if skipped:
        print(skipped)

    # Agrupado por regra: a explicacao e a correcao saem uma vez, os locais
    # embaixo. Num projeto legado isso corta a saida para uma fracao.
    groups: Dict[Tuple[int, str], List[Finding]] = {}
    for f in findings:
        groups.setdefault((SEVERITY_ORDER[f.severity], f.rule), []).append(f)

    current = None
    for (_, rule_id), items in sorted(groups.items()):
        first = items[0]
        if first.severity != current:
            current = first.severity
            print("\n--- %s ---" % current)
        print("[%s] %s" % (rule_id, first.message))
        print("  Correcao: %s" % first.fix)
        for f in sorted(items, key=lambda x: (x.file, x.line)):
            print("  %s:%d  %s" % (f.file, f.line, f.excerpt))

    if highs:
        print("\nHIGH em codigo que voce escreveu ou alterou: corrija e rode de novo antes de entregar.")


# --------------------------------------------------------------------------- entrega
# --entrega: confere, sem rede e sem executar nada, se o que foi entregue tem as pecas
# para rodar. Cada checagem veio de uma falha medida no benchmark: um atalho que chama
# um script nunca escrito, Go sem go.mod, pacote usado e nao declarado.

_REF_EXTS = "php|py|js|mjs|cjs|ts|ps1|bat|cmd|sh|csproj|sln|java|go|rb"
_REF_RX = re.compile(r"(?<![\w/\\.:@-])((?:\.{1,2}[\\/])?[\w.\-]+(?:[\\/][\w.\-]+)*\.(?:%s))(?![\w.])" % _REF_EXTS)
_GENERATED_DIRS = {"node_modules", "vendor", "obj", "dist", "build", "target", ".venv", "venv",
                   "__pycache__", ".git"}
_NODE_BUILTINS = {
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console", "constants", "crypto",
    "dgram", "diagnostics_channel", "dns", "domain", "events", "fs", "http", "http2", "https",
    "inspector", "module", "net", "os", "path", "perf_hooks", "process", "punycode", "querystring",
    "readline", "repl", "stream", "string_decoder", "sys", "test", "timers", "tls", "trace_events",
    "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib", "sqlite",
}


def _project_files(root: Path) -> List[Path]:
    out = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _GENERATED_DIRS and not d.startswith(".")]
        out.extend(Path(dirpath) / f for f in files)
    return out


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# Nomes de produto que terminam como arquivo e nunca sao um arquivo do projeto.
_PRODUCT_NAMES = {"node.js", "next.js", "nuxt.js", "vue.js", "react.js", "express.js", "nest.js",
                  "three.js", "chart.js", "d3.js", "alpine.js", "ember.js", "backbone.js", "angular.js",
                  "deno.js", "socket.io.js", "moment.js", "day.js", "p5.js", "htmx.js"}


def _missing_refs(root: Path, src: Path, text: str, names: List[str]) -> List[str]:
    """Arquivos citados que nao existem. `names` sao os nomes de todos os arquivos do projeto:
    uma citacao vale se bater com o caminho ou, sem caminho, com o nome de qualquer arquivo
    (o README costuma citar `db.py` que mora numa subpasta, ou "Abrir Contatos.bat")."""
    missing = []
    lower_names = [n.lower() for n in names]
    for ref in sorted(set(_REF_RX.findall(text))):
        if any(c in ref for c in "<>*$%{}") or ref.lower().startswith(("http", "www.")):
            continue
        if ref.lower() in _PRODUCT_NAMES:
            continue
        norm = ref.replace("\\", "/")
        if norm.startswith("/") or re.match(r"^[A-Za-z]:", norm):
            continue
        parts = [p for p in norm.split("/") if p not in (".", "")]
        if not parts or any(p in _GENERATED_DIRS for p in parts):
            continue
        rel = "/".join(parts)
        if (src.parent / rel).exists() or (root / rel).exists():
            continue
        base = parts[-1].lower()
        if len(parts) == 1 and any(n == base or n.endswith(" " + base) for n in lower_names):
            continue
        missing.append(ref)
    return missing


def check_delivery(root: Path) -> List[str]:
    """Problemas que impedem o projeto de rodar como entregue (lista vazia = ok)."""
    problems: List[str] = []
    files = _project_files(root)
    rel = lambda p: str(p.relative_to(root))  # noqa: E731
    by_ext: Dict[str, List[Path]] = {}
    for f in files:
        by_ext.setdefault(f.suffix.lower(), []).append(f)
    names = [f.name for f in files]

    # 1. Arquivo citado em atalho, instrucao ou script do package.json existe.
    for f in files:
        name, ext = f.name.lower(), f.suffix.lower()
        text = ""
        if ext in (".bat", ".cmd", ".ps1", ".sh"):
            text = "\n".join(l for l in _read(f).splitlines()
                             if not re.match(r"\s*(rem\b|::|#|echo\b)", l, re.I))
        elif ext == ".md" and f.parent == root:
            md = _read(f)
            text = "\n".join(re.findall(r"```.*?```", md, re.S) + re.findall(r"`([^`\n]+)`", md))
        elif name == "package.json" and f.parent == root:
            try:
                text = "\n".join(str(v) for v in (json.loads(_read(f)).get("scripts") or {}).values())
            except ValueError:
                problems.append("%s: JSON invalido" % rel(f))
        for ref in _missing_refs(root, f, text, names):
            problems.append("%s cita '%s', que nao existe no projeto" % (rel(f), ref))

    # 2. Manifesto que a linguagem precisa para compilar ou instalar.
    if by_ext.get(".go") and not any(f.name == "go.mod" for f in files):
        problems.append("Codigo Go sem go.mod: 'go build' falha. Rode 'go mod init <nome>' e 'go mod tidy'.")
    if by_ext.get(".cs") and not (by_ext.get(".csproj") or by_ext.get(".sln")):
        problems.append("Codigo C# sem arquivo .csproj: 'dotnet build' e 'dotnet run' falham.")
    php_autoload = any("vendor/autoload.php" in _read(f) for f in by_ext.get(".php", []))
    if php_autoload and not any(f.name == "composer.json" for f in files):
        problems.append("PHP usa vendor/autoload.php mas nao ha composer.json: 'composer install' nao tem o que instalar.")

    js = by_ext.get(".js", []) + by_ext.get(".mjs", []) + by_ext.get(".cjs", []) + by_ext.get(".ts", [])
    declared_cache: Dict[Path, Optional[set]] = {}

    def nearest_manifest(f: Path) -> Optional[Path]:
        for parent in f.parents:
            if (parent / "package.json").is_file():
                return parent / "package.json"
            if parent == root:
                return None
        return None

    def declared_in(manifest: Path) -> set:
        if manifest not in declared_cache:
            found = set()
            try:
                data = json.loads(_read(manifest))
                for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                    found.update((data.get(key) or {}).keys())
                for key in ("imports",):  # subpath imports (#alias)
                    found.update((data.get(key) or {}).keys())
            except (ValueError, AttributeError):
                pass
            declared_cache[manifest] = found
        return declared_cache[manifest]

    undeclared: Dict[str, set] = {}
    no_manifest = set()
    for f in js:
        manifest = nearest_manifest(f)
        for m in re.finditer(r"""(?:require\(\s*|from\s+|import\s+)['"]([^'"./][^'"]*)['"]""", _read(f)):
            spec = m.group(1)
            # node:, https:, npm:, jsr:, virtual: e aliases de caminho (@/, ~/, #) nao sao pacotes do registro.
            if ":" in spec or spec.startswith(("@/", "~", "#")):
                continue
            pkg = "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
            if pkg in _NODE_BUILTINS:
                continue
            if manifest is None:
                no_manifest.add(pkg)
            elif pkg not in declared_in(manifest):
                undeclared.setdefault(rel(manifest), set()).add(pkg)
    for manifest, pkgs in sorted(undeclared.items()):
        for pkg in sorted(pkgs):
            problems.append("Pacote '%s' e usado no codigo mas nao esta no %s." % (pkg, manifest))
    if no_manifest:
        problems.append("Codigo Node usa pacotes (%s) mas nao ha package.json." % ", ".join(sorted(no_manifest)[:5]))

    stdlib = getattr(sys, "stdlib_module_names", None)  # Python 3.10+
    if stdlib and by_ext.get(".py"):
        local = {f.stem for f in by_ext[".py"]} | {f.parent.name for f in by_ext[".py"]}
        third = set()
        for f in by_ext[".py"]:
            for m in re.finditer(r"^\s*(?:from\s+([A-Za-z_]\w*)[\w.]*\s+import|import\s+([A-Za-z_]\w*))", _read(f), re.M):
                mod = m.group(1) or m.group(2)
                if mod not in stdlib and mod not in local and mod != "__future__":
                    third.add(mod)
        manifests = {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile"}
        if third and not any(f.name in manifests or f.name.startswith("requirements") for f in files):
            problems.append("Codigo Python importa pacotes de fora (%s) sem requirements.txt ou pyproject.toml."
                            % ", ".join(sorted(third)[:5]))
    return problems


def report_delivery(root: Path, problems: List[str]) -> None:
    if not problems:
        print("ENTREGA OK em %s: arquivos citados existem e os manifestos necessarios estao presentes." % root)
        print("Isso nao substitui compilar e rodar o caminho feliz (SKILL.md, secao 7).")
        return
    print("\n--- ENTREGA: %d problema(s) que impedem rodar como entregue ---" % len(problems))
    for p in problems:
        print("  " + p)


def _utf8_streams() -> None:
    # Console do Windows em cp1252 quebra com UnicodeEncodeError ao imprimir
    # um trecho de codigo com caractere fora da pagina de codigo.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError, OSError):
            # Saida redirecionada ou stream sem reconfigure: segue com a codificacao atual.
            pass


def main() -> int:
    _utf8_streams()
    parser = argparse.ArgumentParser(
        description="Procura padroes inseguros conhecidos antes de entregar o codigo."
    )
    parser.add_argument("paths", nargs="+", help="arquivos ou pastas para analisar")
    parser.add_argument("--json", action="store_true", help="saida em JSON")
    parser.add_argument("--entrega", action="store_true",
                        help="tambem confere se o projeto tem as pecas para rodar como entregue")
    args = parser.parse_args()

    notes = {"grandes": 0, "binarios": 0, "linhas_longas": 0, "ausentes": 0}
    files = iter_files(args.paths, notes)
    if not files:
        print("Nenhum arquivo analisavel encontrado nos caminhos informados.", file=sys.stderr)
        return 2

    findings: List[Finding] = []
    for f in files:
        findings.extend(scan_file(f, notes))

    delivery: Dict[str, List[str]] = {}
    if args.entrega:
        for p in args.paths:
            root = Path(p)
            if root.is_dir():
                delivery[str(root)] = check_delivery(root.resolve())

    if args.json:
        payload = {
            "files_scanned": len(files),
            "not_scanned": notes,
            "findings": [asdict(f) for f in findings],
        }
        if args.entrega:
            payload["delivery"] = delivery
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        report_text(findings, len(files), notes)
        for root, problems in delivery.items():
            report_delivery(Path(root), problems)

    if any(f.severity == "HIGH" for f in findings) or any(delivery.values()):
        return 1
    # Um caminho digitado errado nao pode passar como "OK".
    return 2 if notes["ausentes"] else 0


if __name__ == "__main__":
    sys.exit(main())
