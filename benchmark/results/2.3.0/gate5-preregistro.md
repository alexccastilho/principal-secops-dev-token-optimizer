# Portão 5 (ativação): critério registrado antes de ver qualquer número da v2.3

Registrado em 2026-11-25, depois da medição baseline/v2.2.1 e antes de rodar o braço v23.

Números da v2.2.1 (Sonnet, mesma bancada):
- Prompts de ativação (python + node, 2 repetições = 4 por prompt):
  a01 4/4, a02 4/4, a03 4/4, a04 2/4, a05 0/4, a06 4/4, a07 0/4, a08 0/4, a09 4/4, a10 0/4; n01..n04 0/16.
- Suíte de refatoração: review 6/6, bugfix 0/6.

O critério original ("ativação em fix e review maior que a v2.2.1") não serve como está: a v2.2.1 já tem 4/4 em a01..a03 e 6/6 em review, então não dá para superar. Fica substituído por:

- 5a. Bugfix da suíte de refatoração: v23 > 0/6.
- 5b. Prompts em que a v2.2.1 falhou alguma vez (a04, a05, a07, a08, a10): v23 > 2/20.
- 5c. Sem regressão onde a v2.2.1 acertou tudo (a01, a02, a03, a06, a09 e review): v23 >= 23/26.
- 5d. Falso positivo nos prompts que não são de código (n01..n04): 0/16.

O portão 5 passa só se 5a, 5b, 5c e 5d passarem. A comparação é feita prompt a prompt e publicada assim.
