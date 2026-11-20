#!/usr/bin/env python3
"""Scanner de padroes inseguros para o portao de pre-entrega da skill.

Uso (Windows: troque python3 por py -3):
    python3 revisar_codigo.py <arquivo-ou-pasta> [mais arquivos...]
    python3 revisar_codigo.py . --json

Requer Python 3.8 ou mais novo. So usa a biblioteca padrao.

Segredos nunca aparecem na saida: se uma linha contem um possivel segredo, o
trecho dela e omitido em TODOS os achados daquela linha, nao so no achado de
segredo. Arquivos onde segredo e esperado (.env, wp-config.php) nunca tem
trecho impresso.

Codigo de saida:
    0 = nenhum achado HIGH
    1 = pelo menos um achado HIGH (nao entregar o codigo assim)
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

# Extensoes analisadas ao varrer uma pasta. Um arquivo passado pelo nome e
# analisado seja qual for a extensao.
CODE_SUFFIXES = C_FAMILY | PHP | PY | JS | TEMPLATES | CONFIG | frozenset({
    ".java", ".kt", ".kts", ".scala", ".groovy", ".gradle", ".go", ".cs",
    ".rs", ".swift", ".dart", ".sql", ".sh", ".bash", ".ps1", ".psm1",
    ".bat", ".cmd", ".json", ".xml", ".tf", ".cmake", ".qml", ".slint",
    ".xaml", ".axaml", ".ui", ".pem", ".key", ".htaccess",
})

# Arquivos sem extensao util, pelo nome. O valor e o tipo usado nas regras.
CODE_NAMES = {
    "CMakeLists.txt": ".cmake", "Makefile": ".mk", "makefile": ".mk",
    "GNUmakefile": ".mk", "Dockerfile": ".dockerfile", ".htaccess": ".htaccess",
    "id_rsa": ".key", "id_dsa": ".key", "id_ecdsa": ".key", "id_ed25519": ".key",
}

# Linguagens em que "#" abre comentario. Em C e diretiva (#define com segredo
# existe) e em JavaScript e campo privado de classe.
HASH_COMMENT = PY | PHP | CONFIG | frozenset({
    ".sh", ".bash", ".rb", ".ps1", ".psm1", ".cmake", ".mk", ".dockerfile",
    ".tf", ".htaccess",
})
# "--" so e comentario em SQL. Fora dele, "-----BEGIN PRIVATE KEY-----"
# comeca com "--" e nao pode ser pulado.
DASH_COMMENT = frozenset({".sql"})
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

RULES: List[Rule] = [
    # --- Segredos no codigo (OWASP A02/A04) ---
    Rule("secret-atribuido", "HIGH",
         _rx(_KEYWORDS + r"""["']?\s*\]?\s*(?:=>|[:=])\s*["'](?P<v>[^"'{}$\s<|]{6,})["']"""
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
             r"APP_USR-[0-9a-f-]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-proj-[A-Za-z0-9_-]{20,})", case=True),
         "Chave de servico externo (GitHub, Stripe, Google, Mercado Pago, Slack ou IA) exposta.",
         "Revogue a chave no painel do servico agora, gere outra e leia de variavel de ambiente.",
         secret=True, precise=True),
    Rule("conexao-com-senha", "HIGH",
         _rx(r"""\b(?:mysql|mariadb|postgres(?:ql)?|mongodb(?:\+srv)?|rediss?|amqps?|sqlserver|mssql)://[^\s:'"/@]+:(?![${<%\[])[^\s@'"{}]+@"""),
         "String de conexao com usuario e senha embutidos.",
         "Monte a conexao a partir de variaveis de ambiente.",
         secret=True, precise=True),
    Rule("segredo-em-config", "MEDIUM",
         _rx(r"""^\s*(?:(?:export|ENV|ARG)\s+)?["']?[\w.\-]*(?:password|passwd|pwd|senha|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)[\w.\-]*["']?\s*[:=]\s*(?P<v>[^\s"'#${<%*!\[][^\s"'#]{5,})\s*(?:#.*)?$"""),
         "Possivel segredo em arquivo de configuracao.",
         "Se o arquivo vai para o Git, deixe o valor vazio aqui e ponha o valor real no .env, que fica fora do Git.",
         only=CONFIG | frozenset({".sh", ".bash", ".dockerfile"}), secret=True),

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
         "Substitua por logica explicita ou JSON.parse."),

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
         _rx(r"""\bverify\s*=\s*False\b|rejectUnauthorized\s*:\s*false|CURLOPT_SSL_VERIFY(?:PEER|HOST)\s*,\s*(?:false|0)\b|InsecureSkipVerify\s*:\s*true|NODE_TLS_REJECT_UNAUTHORIZED["'\]\s]*=\s*["']?0"""),
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
    return kind in DASH_COMMENT and stripped.startswith("--")


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
    args = parser.parse_args()

    notes = {"grandes": 0, "binarios": 0, "linhas_longas": 0, "ausentes": 0}
    files = iter_files(args.paths, notes)
    if not files:
        print("Nenhum arquivo analisavel encontrado nos caminhos informados.", file=sys.stderr)
        return 2

    findings: List[Finding] = []
    for f in files:
        findings.extend(scan_file(f, notes))

    if args.json:
        print(json.dumps({
            "files_scanned": len(files),
            "not_scanned": notes,
            "findings": [asdict(f) for f in findings],
        }, ensure_ascii=False, indent=2))
    else:
        report_text(findings, len(files), notes)

    if any(f.severity == "HIGH" for f in findings):
        return 1
    # Um caminho digitado errado nao pode passar como "OK".
    return 2 if notes["ausentes"] else 0


if __name__ == "__main__":
    sys.exit(main())
