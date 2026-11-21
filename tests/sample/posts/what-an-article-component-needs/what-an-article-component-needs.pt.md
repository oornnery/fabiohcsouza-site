---
title: O que realmente precisa ter em um componente de artigo?
summary: Título, resumo e link. Um exercício de separar apresentação, dados e comportamento
  sem criar abstrações cedo demais.
---

## O mínimo

Uma lista de artigos existe para a pessoa decidir o que ler. Para isso bastam três coisas: um título que é link, um resumo curto e metadados que ajudam a escolher.

```html artigo.html
<article>
  <h3><a href="/posts/fastapi-route">Uma rota FastAPI</a></h3>
  <p>Do código à resposta HTTP.</p>
  <time datetime="2026-09-28">28 set 2026</time>
</article>
``` 

## O que fica de fora, por enquanto

- Imagem de capa, se nenhum post tem uma.
- Autor, enquanto só existe um.
- Variações do componente que nenhuma página usa ainda.

## Separar sem abstrair

Os dados vêm de um lugar, a apresentação é o HTML acima e o comportamento (como o realce ao passar o mouse) fica no CSS. Só vale extrair um componente genérico quando a segunda página precisar dele.
