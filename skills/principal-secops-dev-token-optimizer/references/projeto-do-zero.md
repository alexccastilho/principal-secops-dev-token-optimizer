# Projeto do zero — autonomous scaffolding for a non-programmer

## Contents
- Intake: the three questions
- Choosing the stack for the user, not for yourself
- Delivery order
- Standard project skeleton
- Copy-paste ready instructions
- Handoff document

Goal: the user describes a business problem and ends up with something running, without ever needing to understand the language.

## Intake: the three questions

Ask these in one message, numbered, in pt-BR. Not more.

```
1. Onde isso vai rodar? (hospedagem que você já paga, computador local, ainda não sei)
2. Já existe algum código ou é tudo do zero?
3. Quantas pessoas vão usar e o sistema guarda dado pessoal (nome, CPF, e-mail, pagamento)?
```

Answer 3 decides the security level: personal data or payment means ASVS Level 2 and the LGPD section of `security-baseline.md`.

"Ainda não sei" on question 1 is a valid answer. Pick the simplest option and say why in one line.

## Choosing the stack for the user, not for yourself

Decide by what the user can actually operate, not by what is technically elegant.

| Situation | Choose | Why (say this in pt-BR, one line) |
|---|---|---|
| Shared hosting with cPanel, already paid | PHP + MySQL | roda no que você já tem, sem instalar nada |
| Wants a simple site, no dynamic data | HTML + CSS + a little JS | um arquivo, hospedagem grátis serve |
| Already has a WordPress | plugin or child theme, not a new system | evita manter dois sistemas |
| Needs an API or realtime | Node.js | mesma linguagem no navegador e no servidor |
| Data analysis, automation, spreadsheets | Python | menos código para o mesmo resultado |
| Company already runs Java | Java | fica junto do que a empresa mantém |
| Desktop program for Windows and Linux | C++ with Qt | um programa só para os dois sistemas, abre rápido |
| Desktop and the core is already Rust | Rust with Slint | não precisa de duas linguagens no projeto |
| Desktop and the team is a web team | Tauri | reaproveita o que a equipe já sabe fazer |

Never introduce Docker, Kubernetes, microservices, a build pipeline or a JS framework unless the user already has it or explicitly asks. Every extra tool is something they will have to operate alone at 2am.

State the choice in one line and move on. Do not present a menu of options.

## Delivery order

Ship in this sequence so the user always has something working:

```
- [ ] 1. Skeleton that runs and shows something on screen
- [ ] 2. Database connection and one real read
- [ ] 3. The main feature (the thing they asked for)
- [ ] 4. Authentication, if needed
- [ ] 5. Hardening pass against security-baseline.md
- [ ] 6. Handoff document
```

After each step, one test instruction and a stop. Do not dump the whole system in one message: the user cannot debug six files at once.

## Standard project skeleton

Same shape regardless of language, so the user learns the layout once:

```
projeto/
├── public/           única pasta exposta na internet (index, css, js, imagens)
├── src/              código da aplicação
├── config/           configuração, lê do .env
├── storage/
│   ├── logs/         app.log
│   └── uploads/      fora da pasta pública
├── .env              segredos, NUNCA enviar pro Git
├── .env.example      mesmas chaves, valores vazios
├── .gitignore        contém .env, storage/, dependências
└── LEIA-ME.md        o documento de entrega
```

Web server document root points at `public/`. Everything else is unreachable from the browser. This single decision removes a whole class of vulnerabilities.

Shared hosting where the public folder is fixed (`public_html` on cPanel): the contents of `public/` go inside `public_html`, and `src/`, `config/`, `storage/` and `.env` go one level above it, next to `public_html`, not inside. Say exactly that to the user, with the folder names they see in the file manager.

## Copy-paste ready instructions

Every command block is literal. No placeholders the user has to interpret.

Bad: "instale as dependências e configure o banco".

Good:
```
1. Abra o phpMyAdmin no painel da sua hospedagem.
2. Clique em "Importar", escolha o arquivo banco.sql que te mandei, clique em "Executar".
3. Abra o arquivo .env e preencha as 4 linhas com os dados que a hospedagem te deu.
4. Acesse seusite.com.br/login.php. Deve aparecer a tela de entrada.
   Se aparecer erro 500, me mande o conteúdo de storage/logs/app.log.
```

Rules:
* One action per line, in the order they happen.
* Name the button, the menu or the exact path, not the concept.
* Always end with what success looks like and what to send back if it fails.
* When a value is specific to the user (host, password, path), mark it clearly: `SEU_USUARIO_AQUI`.

## Handoff document

Generate `LEIA-ME.md` at the end of any project from scratch. Keep it under one page, in pt-BR:

```markdown
# O que é este sistema
[uma frase]

# Como rodar
[comandos literais]

# Onde ficam as coisas
[3 a 5 linhas: onde mudar o texto da página, onde ficam os logs, onde fica a config]

# O que NÃO mexer
[arquivos que quebram tudo se editados]

# Backup
[como fazer, com que frequência]

# Se der problema
[onde olhar o log, que informação mandar pro suporte]
```

This document is what lets the user come back in six months, or hand the project to someone else, without the system becoming a black box.
