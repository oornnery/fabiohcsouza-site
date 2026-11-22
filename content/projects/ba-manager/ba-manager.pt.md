---
title: Gestor de BAs
summary: Centraliza os BAs de interconexão da ABR Telecom, ligados ao Jira, com alertas de SLA e automações. FastAPI e Preact.
---

BA (Boletim de Anormalidade) é como as operadoras registram uma falha na interconexão entre as redes delas, pelo
[sistema da ABR Telecom](https://www.abrtelecom.com.br/servicos/outras-solucoes/ba%27s-de-interconexao). Criei este sistema para tratar esses boletins.

Ele fica sincronizado com a ABR pelo web service SOAP. Os BAs são abertos, alterados e encerrados pela plataforma,
com predefinições e modelos de mensagem que preenchem o texto. Cada BA recebido abre um chamado no Jira; os dois ficam
ligados e compartilham os comentários.

As automações são montadas num editor de arrastar e soltar: um gatilho, condições e ações ligados como um grafo. Uma
regra roda por evento ou por agendamento, pode ser testada antes de salvar e guarda o histórico de cada execução. Uma
execução com falha gera um alerta. O escalonamento segue o SLA de cada BA, e os avisos saem por e-mail e Slack.

O painel tem gráficos dos BAs, do SLA e dos tempos de resposta, e as listas exportam relatórios. Os administradores
cuidam dos usuários e das áreas, que definem os serviços que cada usuário vê, e têm log de auditoria, os logs da
aplicação e backups.

O backend é em FastAPI, com SQLModel e Alembic. A interface é em Preact e TypeScript, com gráficos em ECharts e o
editor de automações em React Flow.
