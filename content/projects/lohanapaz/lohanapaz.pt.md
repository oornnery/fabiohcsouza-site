---
title: Site da Lohana Paz
summary: Site de uma publicitária, com serviços, trabalhos e contato. Feito em Astro.
---

O site da Lohana Paz, publicitária: uma página em português com quem ela é, os serviços, os trabalhos, como um
projeto acontece e um jeito de falar com ela pelo WhatsApp.

![A página inicial](assets/home.png)

## Como é feito

O Astro gera a página inteira em HTML no build. Cada seção é um componente com o próprio CSS e um script pequeno em
TypeScript para o que se mexe: o menu, o carrossel de trabalhos, o modal de projeto e as animações. Os textos e os
projetos são arquivos JSON em content collections, validados com zod, e as imagens são redimensionadas no build.

A Cloudflare serve os arquivos pelos static assets de um Worker. O único código que roda no servidor é uma rota que
registra cliques no Analytics Engine, com checagem de origem e limite de requisições. As visitas vêm do Cloudflare Web
Analytics, e o Google Ads só carrega depois que a pessoa aceita os cookies.

Cada push roda checagem de tipos, testes e o build no GitHub Actions, e a Cloudflare publica o Worker.

![A página no celular](assets/mobile.png)
