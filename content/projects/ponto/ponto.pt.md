---
title: ponto
summary: CLI para o Secullum Ponto Web.
---

Usa a Central do Funcionário da Secullum pelo terminal: espelho de ponto, ajustes e justificativas, sem abrir o
navegador.

## Comandos

- `ponto status` mostra o espelho de ponto de um período. Os horários ainda aguardando aprovação vêm marcados, para
  não passarem por batidas registradas.
- `ponto adjust` preenche os dias que precisam de ajuste. Com `--dry-run` mostra o plano antes; fins de semana,
  feriados, folgas e dias com solicitação pendente ficam de fora.
- `ponto justify` lista os motivos e lança a justificativa de um dia.
- `ponto requests` mostra as solicitações já enviadas.
- `--json` escreve só JSON, para scripts.

## Como é feito

Python com Typer nos comandos, Rich nas tabelas e httpx na API da Central. A configuração vem de flags, variáveis de
ambiente, um `.env` ou um arquivo TOML que o `ponto setup` cria. Os testes rodam contra uma versão falsa da API.
