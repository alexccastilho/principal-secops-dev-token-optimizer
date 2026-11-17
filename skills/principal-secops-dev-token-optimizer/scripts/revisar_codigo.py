#!/usr/bin/env python3
"""Scanner de padroes inseguros para o portao de pre-entrega da skill.

Uso (Windows: troque python3 por py -3):
    python3 revisar_codigo.py <arquivo-ou-pasta> [mais arquivos...]
    python3 revisar_codigo.py . --json

O trecho da linha de achados que envolvem segredo e omitido da saida, para que
o valor do segredo nao va parar no historico de uma conversa ou de um log.

Codigo de saida:
    0 = nenhum achado HIGH
    1 = pelo menos um achado HIGH (nao entregar o codigo assim)
    2 = erro de uso (caminho inexistente, nenhum arquivo legivel)

O scanner e deliberadamente conservador: ele aponta padroes que quase sempre
sao problema. Um achado nao e prova de falha, e um ponto para revisar antes
de entregar. A ausencia de achados tambem nao prova que o codigo e seguro:
o checklist do SKILL.md continua obrigatorio.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Extensoes analisadas. Binarios e assets ficam de fora porque regex sobre
# eles gera ruido sem valor.
CODE_SUFFIXES = {
    ".php", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rb", ".cs", ".rs", ".sql", ".html", ".htm",
    ".sh", ".bash", ".env", ".yml", ".yaml", ".json", ".ini", ".conf",
    ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".inl",
    ".cmake", ".toml", ".qml", ".slint", ".xaml", ".axaml", ".ui", ".dart",
}

# Arquivos de build sem extensao util. Sao codigo: definem as flags com que
# o binario e compilado, e uma flag errada ali quebra o programa no usuario.
CODE_NAMES = {"CMakeLists.txt", "Makefile", "makefile", "GNUmakefile"}

# Pastas ignoradas: sao dependencias de terceiros ou artefatos de build.
# Achados nelas nao sao acionaveis por quem esta escrevendo o codigo.
SKIP_DIRS = {
    "node_modules", "vendor", ".git", "__pycache__", "dist", "build",
    "target", ".venv", "venv", ".next", "coverage", ".idea", ".vscode",
}

# O proprio scanner contem, em texto, os padroes que ele procura. Analisar
# a si mesmo gera achados que nao sao vulnerabilidade nenhuma.
SKIP_FILES = {"revisar_codigo.py"}

# Arquivos acima deste tamanho quase sempre sao minificados ou gerados.
# 1 MB cobre com folga qualquer fonte escrita a mao.
MAX_FILE_BYTES = 1_000_000

# Linhas acima deste comprimento sao minificadas. Regex nelas produz
# falso positivo em serie.
MAX_LINE_CHARS = 500


@dataclass
class Rule:
    id: str
    severity: str          # HIGH | MEDIUM | LOW
    pattern: re.Pattern
    message: str           # em pt-BR, para o usuario final
    fix: str               # em pt-BR, o que fazer


def _rx(p: str) -> re.Pattern:
    return re.compile(p, re.IGNORECASE)


RULES: list[Rule] = [
    # --- Segredos no codigo (OWASP A02/A04) ---
    Rule("secret-atribuido", "HIGH",
         _rx(r"""(senha|password|passwd|pwd|secret|token|api[_-]?key|apikey|access[_-]?key|client[_-]?secret)\s*[:=]\s*["'][^"'{}$\s]{6,}["']"""),
         "Segredo escrito direto no codigo.",
         "Mova para variavel de ambiente (.env) e leia de la. Se ja foi pro Git, troque o segredo."),
    Rule("chave-privada", "HIGH",
         _rx(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
         "Chave privada dentro do repositorio.",
         "Remova o arquivo, gere uma chave nova e guarde fora do codigo."),
    Rule("aws-key", "HIGH",
         _rx(r"\bAKIA[0-9A-Z]{16}\b"),
         "Credencial de nuvem exposta no codigo.",
         "Revogue a credencial agora e recrie via variavel de ambiente."),
    Rule("conexao-com-senha", "HIGH",
         _rx(r"(mysql|postgres|postgresql|mongodb|redis|amqp)://[^\s:'\"]+:[^\s@'\"]+@"),
         "String de conexao com usuario e senha embutidos.",
         "Monte a conexao a partir de variaveis de ambiente."),

    # --- SQL montado por concatenacao (OWASP A05) ---
    Rule("sql-concat-php", "HIGH",
         _rx(r"""(select|insert|update|delete|where|values)[^;\n]{0,120}?["']\s*\.\s*\$"""),
         "SQL montado juntando texto com variavel (PHP).",
         "Use prepared statement do PDO com placeholders (?) e bindValue."),
    Rule("sql-interp-php", "HIGH",
         _rx(r"""(select|insert|update|delete)\b[^;\n]{0,120}?(where|values|set)\b[^;\n]{0,120}?\$\{?\w+"""),
         "SQL com variavel interpolada dentro da string (PHP).",
         "Use prepared statement com placeholders."),
    Rule("sql-fstring-py", "HIGH",
         _rx(r"""(execute|executemany|raw|text)\s*\(\s*f["']"""),
         "SQL montado com f-string (Python).",
         "Use cursor.execute(sql, params) com %s ou :nome."),
    Rule("sql-template-js", "HIGH",
         _rx(r"""(query|execute)\s*\(\s*`[^`]*\$\{"""),
         "SQL montado com template string (JavaScript).",
         "Use query parametrizada: connection.execute(sql, [valores])."),
    Rule("sql-concat-java", "HIGH",
         _rx(r"""(executeQuery|executeUpdate|createQuery|createNativeQuery)\s*\(\s*["'][^"']*["']\s*\+"""),
         "SQL montado por concatenacao (Java).",
         "Use PreparedStatement com ? ou parametros nomeados no JPA."),

    # --- Execucao dinamica e shell (OWASP A05) ---
    Rule("eval-dinamico", "HIGH",
         _rx(r"\b(eval|assert)\s*\(\s*\$|\bexec\s*\(\s*\$|\bsystem\s*\(\s*\$|\bpassthru\s*\(\s*\$|\bshell_exec\s*\(\s*\$"),
         "Execucao de codigo ou comando montado com dado de entrada.",
         "Nao execute string vinda do usuario. Use lista de valores permitidos."),
    Rule("shell-true", "HIGH",
         _rx(r"shell\s*=\s*True"),
         "Comando de sistema executado atraves do shell (Python).",
         "Use subprocess.run([lista, de, argumentos]) com shell=False."),
    Rule("child-process-exec", "HIGH",
         _rx(r"""child_process\.exec\s*\(|\bexec\s*\(\s*`"""),
         "Comando de sistema com string montada (Node.js).",
         "Use execFile com array de argumentos."),
    Rule("eval-js-py", "MEDIUM",
         _rx(r"\beval\s*\(|\bnew\s+Function\s*\("),
         "Uso de eval.",
         "Substitua por logica explicita ou JSON.parse."),

    # --- Hash e criptografia fraca (OWASP A04) ---
    Rule("hash-fraco-senha", "HIGH",
         _rx(r"\b(md5|sha1)\s*\([^)\n]{0,60}(pass|senha|pwd|secret)"),
         "Senha protegida com hash fraco (MD5 ou SHA-1).",
         "Use password_hash com PASSWORD_ARGON2ID, bcrypt ou argon2-cffi."),
    Rule("hash-fraco", "MEDIUM",
         _rx(r"\b(md5|sha1)\s*\("),
         "Uso de MD5 ou SHA-1.",
         "Se for para senha ou assinatura, troque. Para checksum simples, tudo bem."),
    Rule("random-inseguro", "MEDIUM",
         _rx(r"\b(rand|mt_rand|Math\.random|random\.random|random\.randint)\s*\("),
         "Numero aleatorio previsivel usado onde pode virar token.",
         "Para token ou senha use random_bytes, secrets ou crypto.randomBytes."),
    Rule("tls-desligado", "HIGH",
         _rx(r"(verify\s*=\s*False|rejectUnauthorized\s*:\s*false|CURLOPT_SSL_VERIFYPEER\s*,\s*(false|0)|InsecureSkipVerify\s*:\s*true)"),
         "Verificacao do certificado HTTPS desligada.",
         "Nunca desligue em producao. Corrija o certificado."),

    # --- Saida sem escape (OWASP A05) ---
    Rule("echo-sem-escape", "MEDIUM",
         _rx(r"""echo\s+\$_(GET|POST|REQUEST|COOKIE)"""),
         "Dado do usuario impresso na tela sem tratamento (PHP).",
         "Use htmlspecialchars($v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')."),
    Rule("innerhtml", "MEDIUM",
         _rx(r"\.innerHTML\s*=|dangerouslySetInnerHTML|v-html\s*="),
         "HTML inserido direto na pagina.",
         "Use textContent, ou sanitize antes de inserir."),
    Rule("autoescape-off", "HIGH",
         _rx(r"(\|\s*raw\b|\|\s*safe\b|html_safe|autoescape\s*=\s*False|\{\!\!)"),
         "Escape automatico do template desligado.",
         "Deixe o template escapar. So desligue para HTML que voce mesmo gerou."),

    # --- Configuracao insegura (OWASP A02) ---
    Rule("debug-ligado", "MEDIUM",
         _rx(r"(DEBUG\s*=\s*True|display_errors\s*[,=]\s*['\"]?(1|On)|APP_DEBUG\s*=\s*true)"),
         "Modo de depuracao ligado.",
         "Desligue em producao. Erro detalhado vai pro log, nao pra tela."),
    Rule("cors-aberto", "HIGH",
         _rx(r"""Access-Control-Allow-Origin["'\s:,]+\*|origin\s*:\s*["']\*["']"""),
         "CORS liberado para qualquer site.",
         "Liste os dominios permitidos. Nunca * junto com credenciais."),
    Rule("permissao-777", "HIGH",
         _rx(r"chmod\s+(-R\s+)?0?777|chmod\s*\(\s*[^,]+,\s*0?777"),
         "Permissao 777 em arquivo ou pasta.",
         "Use 644 para arquivos e 755 para pastas."),
    Rule("jwt-alg-none", "HIGH",
         _rx(r"""(alg["'\s:]+none|algorithms\s*=\s*\[\s*["']none)"""),
         "JWT aceitando assinatura vazia.",
         "Fixe o algoritmo esperado e rejeite 'none'."),

    # --- Desserializacao (OWASP A08) ---
    Rule("desserializacao", "HIGH",
         _rx(r"\bunserialize\s*\(|\bpickle\.loads?\s*\(|\byaml\.load\s*\((?!.*SafeLoader)|Marshal\.load\s*\("),
         "Desserializacao de dado nao confiavel.",
         "Use JSON com validacao de schema, ou yaml.safe_load."),

    # --- Erro engolido (OWASP A10) ---
    Rule("except-vazio", "MEDIUM",
         _rx(r"except\b[^:\n]*:\s*pass\b|catch\s*\([^)]*\)\s*\{\s*\}|catch\s*\{\s*\}"),
         "Erro capturado e ignorado em silencio.",
         "Registre no log e decida: tentar de novo, ou recusar a operacao."),
    Rule("except-generico", "MEDIUM",
         _rx(r"^\s*except\s*:\s*$"),
         "except sem tipo captura tudo, ate Ctrl+C e erros de memoria (Python).",
         "Capture a excecao especifica esperada, por exemplo except ValueError."),
    Rule("supressao-arroba", "MEDIUM",
         _rx(r"(?<![\w'\"])@(mysqli_|file_get_contents|fopen|unlink|include|require)"),
         "Erro suprimido com @ (PHP).",
         "Trate o erro explicitamente. O @ esconde o problema."),

    # --- C / C++: memoria e entrada hostil (CERT C, C++ Core Guidelines) ---
    Rule("c-funcao-insegura", "HIGH",
         _rx(r"\b(strcpy|strcat|sprintf|vsprintf|gets|stpcpy)\s*\("),
         "Funcao de string que escreve sem saber o tamanho do destino (C/C++).",
         "Troque por snprintf ou pela versao com tamanho do destino, e confira o retorno."),
    Rule("c-scanf-sem-limite", "HIGH",
         _rx(r"\b[fs]?scanf\s*\([^;]{0,120}%s"),
         "scanf com %s sem largura maxima grava alem do buffer.",
         "Informe a largura (%%31s para um buffer de 32) ou use fgets."),
    Rule("c-comando-shell", "HIGH",
         _rx(r"\b(system|popen|_popen|_wsystem|execlp|execvp|ShellExecuteA|ShellExecuteW)\s*\("),
         "Comando de sistema disparado a partir do codigo nativo.",
         "Use execve ou CreateProcess com os argumentos separados. Nunca monte a linha de comando com dado que veio de fora."),
    Rule("c-alloc-multiplicacao", "MEDIUM",
         _rx(r"\b(malloc|realloc|alloca)\s*\([^;]{0,80}?[\w\)]\s*\*\s*[\w(]"),
         "Tamanho de alocacao calculado por multiplicacao: pode estourar e alocar de menos.",
         "Use ckd_mul (C23) ou __builtin_mul_overflow e recuse o arquivo se a conta estourar."),
    Rule("c-alloca", "MEDIUM",
         _rx(r"\balloca\s*\("),
         "alloca reserva na pilha e nao avisa quando ela acaba.",
         "Use malloc com verificacao de retorno, ou um buffer fixo com tamanho validado."),
    Rule("c-fread-struct", "MEDIUM",
         _rx(r"\b(fread|recv)\s*\(\s*&"),
         "Bytes lidos direto para dentro de uma struct ou de um numero.",
         "Leia para um buffer de bytes e monte cada campo com deslocamento explicito. Layout e ordem dos bytes mudam entre plataformas, e o arquivo fica ambiguo."),
    Rule("c-memcpy-tamanho-externo", "LOW",
         _rx(r"\bmemcpy\s*\([^;]{0,120}\b(len|length|size|count|tamanho)\w*\s*\)"),
         "memcpy com tamanho vindo de variavel.",
         "Valide o tamanho contra a capacidade do destino na mesma expressao, antes de copiar."),
    Rule("march-native", "HIGH",
         _rx(r"-march\s*=\s*native|-mtune\s*=\s*native|-xHost"),
         "Compilacao mirando a CPU da maquina que compilou.",
         "O binario morre com instrucao invalida em processador mais antigo. Use uma base portavel (-march=x86-64-v2) e escolha o caminho otimizado em tempo de execucao. So aceite em build local de teste, nunca no que voce distribui."),
    Rule("rust-unsafe", "MEDIUM",
         _rx(r"\bunsafe\s*(\{|fn\b|impl\b)"),
         "Bloco unsafe em Rust.",
         "Confirme que tem um comentario // SAFETY: logo acima dizendo qual garantia torna o bloco correto, e rode cargo miri test."),
    Rule("cpp-u8path", "LOW",
         _rx(r"\b(std::filesystem::|fs::)u8path\s*\("),
         "u8path foi marcado obsoleto no C++20.",
         "Monte o path a partir de char8_t ou de std::u8string."),

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
         "Nunca em producao. Corrija o certificado ou instale a cadeia correta."),
    Rule("ui-widget-nao-virtualizado", "MEDIUM",
         _rx(r"\b(QTableWidget|QListWidget|QTreeWidget)\b"),
         "Widget que cria um objeto por linha: trava quando a lista cresce.",
         "Use QAbstractItemModel com QTableView ou QTreeView. Acima de mil linhas isso deixa de ser detalhe."),
    Rule("ui-loop-reentrante", "MEDIUM",
         _rx(r"processEvents\s*\(|\bDoEvents\s*\(|\bdo_events\s*\("),
         "Loop de eventos rodado a mao para a janela nao congelar.",
         "Isso reentra nos seus proprios tratadores e gera bug intermitente. Mova o trabalho pesado para uma thread."),
]

# Comentarios inteiros viram ruido: 'senha = ...' num exemplo comentado nao
# e vulnerabilidade. Estas marcas cobrem os estilos mais comuns.
#
# O "*" sozinho nao entra: em C e C++ uma linha como "*out = malloc(n * size);"
# e codigo, nao comentario. Linhas internas de bloco de comentario comecam com
# "* " (asterisco e espaco) ou sao so "*" ou "*/".
COMMENT_PREFIXES = ("//", "#", "/*", "* ", "*/", "--", "<!--")

# Regras cujo trecho de linha nunca deve ser impresso, porque contem o segredo.
SECRET_RULE_IDS = {"secret-atribuido", "chave-privada", "aws-key", "conexao-com-senha"}
OMITTED_EXCERPT = "[trecho omitido: a linha contem um possivel segredo]"


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    message: str
    fix: str
    excerpt: str


def iter_files(paths: list[str]) -> list[Path]:
    """Coleta arquivos analisaveis. Caminho invalido vira aviso, nao excecao."""
    found: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            print(f"aviso: caminho nao encontrado, ignorado: {raw}", file=sys.stderr)
            continue
        candidates = [p] if p.is_file() else sorted(p.rglob("*"))
        for c in candidates:
            if not c.is_file():
                continue
            if any(part in SKIP_DIRS for part in c.parts):
                continue
            if c.name in SKIP_FILES:
                continue
            if (c.suffix.lower() not in CODE_SUFFIXES
                    and c.name not in CODE_NAMES and c.name != ".env"):
                continue
            try:
                if c.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            found.append(c)
    return found


def scan_file(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"aviso: nao consegui ler {path}: {exc}", file=sys.stderr)
        return []

    findings: list[Finding] = []
    for n, line in enumerate(text.splitlines(), start=1):
        if len(line) > MAX_LINE_CHARS:
            continue
        stripped = line.strip()
        if stripped == "*" or stripped.startswith(COMMENT_PREFIXES):
            continue
        for rule in RULES:
            if rule.pattern.search(line):
                findings.append(Finding(
                    file=str(path),
                    line=n,
                    rule=rule.id,
                    severity=rule.severity,
                    message=rule.message,
                    fix=rule.fix,
                    excerpt=OMITTED_EXCERPT if rule.id in SECRET_RULE_IDS else stripped[:160],
                ))
    return findings


SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def report_text(findings: list[Finding], files_scanned: int) -> None:
    if not findings:
        print(f"OK. {files_scanned} arquivo(s) analisado(s), nenhum padrao inseguro encontrado.")
        print("Isso nao substitui o checklist do SKILL.md.")
        return

    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.file, f.line))
    highs = sum(1 for f in findings if f.severity == "HIGH")

    print(f"{len(findings)} achado(s) em {files_scanned} arquivo(s). HIGH: {highs}.\n")
    current = None
    for f in findings:
        if f.severity != current:
            current = f.severity
            print(f"--- {current} ---")
        print(f"{f.file}:{f.line}  [{f.rule}]")
        print(f"  {f.message}")
        print(f"  Correcao: {f.fix}")
        print(f"  Linha: {f.excerpt}")
        print()

    if highs:
        print("Nao entregue o codigo com achados HIGH em aberto. Corrija e rode de novo.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Procura padroes inseguros conhecidos antes de entregar o codigo."
    )
    parser.add_argument("paths", nargs="+", help="arquivos ou pastas para analisar")
    parser.add_argument("--json", action="store_true", help="saida em JSON")
    args = parser.parse_args()

    files = iter_files(args.paths)
    if not files:
        print("Nenhum arquivo analisavel encontrado nos caminhos informados.", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for f in files:
        findings.extend(scan_file(f))

    if args.json:
        print(json.dumps({
            "files_scanned": len(files),
            "findings": [asdict(f) for f in findings],
        }, ensure_ascii=False, indent=2))
    else:
        report_text(findings, len(files))

    return 1 if any(f.severity == "HIGH" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
