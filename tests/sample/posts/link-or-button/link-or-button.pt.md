---
title: Link ou botão? Comece pelo que a pessoa vai fazer
summary: Uma revisão prática de semântica, foco e navegação por teclado em componentes
  de página.
---

## A regra

Se a ação leva a outro lugar, é um link. Se muda algo na página ou envia dados, é um botão. A aparência vem depois, no CSS.

```html exemplo.html
<a href="/posts">Ver todos os posts</a>
<button type="button" aria-expanded="false">Abrir menu</button>
``` 

## Teste com o teclado

- `Tab` precisa chegar em todos os dois.
- `Enter` ativa o link; `Enter` e `Espaço` ativam o botão.
- O foco precisa ficar visível nos dois casos.

Um `div` com `onclick` falha em todos esses testes. Começar pelo elemento certo resolve de graça.
