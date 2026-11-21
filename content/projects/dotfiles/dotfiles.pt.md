---
title: dotfiles
summary: Meu ambiente de trabalho, Arch Linux no WSL, gerenciado por um comando.
---

Meu ambiente com Arch Linux no WSL, pronto para voltar ao Arch num desktop. Todo script pode rodar de novo sem quebrar.

## Como funciona

Uma máquina nova é uma linha: clonar o repositório e rodar o `bootstrap`, que instala o git e o GNU Stow e aplica o
arquivo da máquina. Cada pasta em `home/` é um pacote de configuração ligado no `$HOME` pelo Stow, e cada máquina tem
um arquivo com as ferramentas, os pacotes de configuração e as pastas dela.

O comando `dots` faz o resto: `apply` deixa a máquina igual ao arquivo, `status` mostra o que falta, `doctor` o que
está quebrado e `migrate` roda mudanças que só acontecem uma vez. Ele também salva a lista de pacotes, troca o tema e
abre as colas de comandos.

## O que mais tem

O lado do Windows fica no mesmo repositório: GlazeWM, YASB, Windows Terminal, PowerShell, as configurações do WSL e os
pacotes do winget. Tem também as configurações e prompts dos meus agentes de IA, e os arquivos compose dos serviços
que hospedo. Um script de teste confere todos os scripts, também no CI.
