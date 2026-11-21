---
title: Python encontra a web
summary: Um laboratório de páginas renderizadas no servidor com FastAPI e Jinja. As
  interações do navegador entram conforme a página precisa delas.
goal: Entender até onde HTML do servidor vai antes de precisar de um framework de
  front-end.
---

## O projeto

Páginas simples renderizadas no servidor, começando sem nenhum JavaScript. Cada interação nova entra só quando a página realmente precisa dela.

## Como funciona

- Rotas FastAPI devolvem templates Jinja.
- Formulários funcionam com POST normal antes de virarem interativos.
- Cada etapa vira um post desta série.
