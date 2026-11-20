*Leia em outros idiomas: [English](../CONTRIBUTING.md) · [Español](CONTRIBUTING.es.md)*

# Como contribuir

Obrigado por considerar uma contribuição. Este documento explica o que está no escopo, como testar uma mudança e as convenções em que a skill se apoia. A documentação para quem usa é o [README](README.pt-BR.md).

## O que é este projeto

Uma skill, não um aplicativo: `skills/principal-secops-dev-token-optimizer/SKILL.md` e os arquivos que ele chama são instruções que o Claude lê. A maior parte das contribuições muda texto, e mudar o texto muda o comportamento. Trate uma frase do `SKILL.md` como trataria uma linha de código.

O público é fixo: uma pessoa que **não programa**, atendida em português do Brasil simples. Contribuições que deixam as respostas mais longas, mais técnicas ou menos seguras para essa pessoa estão fora do escopo, mesmo quando estão corretas.

## Prioridades

Toda mudança é avaliada na mesma ordem que a skill usa em caso de conflito:

1. **Segurança.** Nunca enfraquecer a linha de base, o modelo de ameaça ou a verificação antes da entrega.
2. **Integridade do sistema.** A skill nunca pode quebrar código que funciona: escopo mínimo, contratos preservados, permissão explícita para ações destrutivas.
3. **Clareza para quem usa.** pt-BR simples, uma instrução de aplicar e testar, nenhum jargão sem tradução.
4. **Estrutura.** Código que continua fácil de mudar (seção 9 do `SKILL.md`).
5. **Economia de tokens.** O `SKILL.md` é carregado toda vez que a skill entra em ação. Detalhe fica numa referência, carregada sob demanda.
6. **Estilo.**

## Preparando o ambiente

Você precisa de Git e de Python 3.8 ou mais novo. Mais nada: o scanner, os testes e as ferramentas só usam a biblioteca padrão, de propósito. A skill roda nas sandboxes do claude.ai e em computadores de quem não programa, onde instalar um pacote é um passo que falha.

```bash
git clone https://github.com/alexccastilho/principal-secops-dev-token-optimizer.git
cd principal-secops-dev-token-optimizer
python -B -m unittest discover -s tests -v
```

A única exceção é `tools/make_icon.py`: ele precisa do Pillow, e só para redesenhar o ícone.

## Testando uma mudança

- **A suíte de testes** precisa passar antes e depois da sua mudança. O GitHub Actions roda a suíte no Linux e no Windows, com Python 3.8 e a versão atual.
- **Mudanças no scanner** precisam de um teste em `tests/test_scanner.py`, com um trecho que deve ser marcado e outro que não deve. Um falso positivo é tão grave quanto um falso negativo: com a regra "só entregue com zero HIGH", um falso positivo faz o Claude reescrever código que funciona.
- **Mudanças no `SKILL.md` ou numa referência** precisam de uma conferência manual: rode pelo menos um cenário afetado do `evals/evals.json` no Claude Code (`claude --plugin-dir .`) ou enviando o ZIP para o claude.ai, e compare a resposta com as asserções. Se o comportamento for novo, acrescente um cenário.
- **Nunca cole um segredo real** num teste, num eval ou numa issue. Use valores claramente falsos.

## Convenções

### Ligações da skill

- Todo arquivo em `references/` precisa ser chamado pela tabela da seção 6 do `SKILL.md`. Uma referência que ninguém chama é texto morto, e uma chamada para um arquivo que não existe é uma promessa quebrada. A suíte de testes confere as duas coisas.
- A descrição do `SKILL.md` fica em até 1024 caracteres, o limite do formato de skill.
- Os números de seção do `SKILL.md` são citados em outros arquivos ("seção 4, regra 9"). Acrescente seções novas no fim em vez de renumerar.
- As referências são escritas em inglês, como o `SKILL.md`. O texto que a skill mostra para quem usa (exemplos de resposta, perguntas, nomes de arquivo como `LEIA-ME.md`) fica em pt-BR.

### Versões e lançamentos

- A versão fica em dois lugares, `.claude-plugin/plugin.json` e `metadata.version` no `SKILL.md`, e precisa ser igual à primeira entrada dos três changelogs. A suíte de testes confere.
- Para lançar uma versão: atualize os dois, acrescente a entrada em `CHANGELOG.md`, `docs/CHANGELOG.pt-BR.md` e `docs/CHANGELOG.es.md`, rode `python tools/build_zip.py` e anexe o ZIP de `dist/` à release no GitHub.

### Documentação em três idiomas

README, CHANGELOG e CONTRIBUTING existem em inglês (na raiz), português e espanhol (em `docs/`). Uma mudança num deles é feita nos três no mesmo pull request, e os READMEs mantêm as mesmas seções.

A documentação parece escrita por uma pessoa: nada de travessão ou meia-risca como aparte, aspas retas, três pontos em vez do caractere de reticências, nada de vocabulário inflado. A suíte de testes falha no primeiro caractere proibido.

### Trabalho de terceiros

Partes da skill adaptam [caldoai/skills](https://github.com/caldoai/skills) (MIT). Se você adaptar outro trabalho de terceiros, a licença dele precisa permitir, e o crédito e o texto da licença vão para `skills/principal-secops-dev-token-optimizer/THIRD_PARTY_NOTICES.md`, que vai junto no ZIP.

### Commits

Uma mudança completa por commit, com uma mensagem que diz o que mudou e por quê. Não misture renomeação em massa ou reformatação com mudança de comportamento.

## Relatando problemas

Bugs e ideias: abra uma issue usando os modelos. Vulnerabilidades de segurança: nunca numa issue pública; veja o [SECURITY.md](../SECURITY.md).

## Licença

Ao contribuir, você concorda que a sua contribuição fica sob a Licença MIT, a mesma do resto do projeto (veja o [LICENSE](../LICENSE)).
