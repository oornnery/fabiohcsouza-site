---
title: Blog e portfólio
summary: Este site. Posts, projetos e currículo em português e inglês, servidos por
  um único processo Python atrás de um Cloudflare Tunnel.
goal: Um lugar para escrever, mostrar projetos e receber contato, simples de manter
  e de rodar em uma VPS.
---

## O projeto

Blog, projetos e página Sobre em um único app FastAPI, com templates Jinja2 e um admin em Preact para editar tudo em português e inglês.

## Como funciona

- Toda página é HTML do servidor e funciona sem JavaScript. Carrossel, filtros, reações e formulário de contato são ilhas carregadas quando entram na tela.
- O conteúdo nasce em Markdown com frontmatter, é importado para o SQLite e pode voltar para Markdown com um comando.
- Cada página tem uma cópia em Markdown e o site tem um `llms.txt` para agentes lerem.
- O formulário de contato salva no banco e envia uma notificação pelo Resend.

## Em produção

Docker na VPS, com o app sem expor portas e o `cloudflared` ao lado. O container roda sem privilégios, com sistema de arquivos somente leitura e limites de memória e CPU.

## Objetivo

Um lugar para escrever, mostrar projetos e receber contato, simples de manter e de rodar em uma VPS.

## Decisões

- HTML renderizado no servidor; JavaScript só em ilhas Preact onde a página precisa de interação.
- SQLite em um volume Docker, com backups consistentes feitos pelo próprio app.
- Nenhuma porta publicada: o tráfego chega pelo Cloudflare Tunnel.
- CSP estrita, limite de requisições por IP e sessão de admin com senha em hash.
