---
title: Store POS
summary: Ponto de venda para loja pequena, em app desktop.
---

Um ponto de venda desktop para loja pequena, do caixa ao fechamento do dia.

## O que faz

No caixa você busca produtos, monta o carrinho, deixa uma venda em espera para retomar depois e recebe em dinheiro,
crédito (com parcelas), débito ou PIX, ligando a venda a um cliente se quiser. O caixa tem abertura, fechamento,
sangria e o histórico de cada sessão.

O painel mostra vendas, estoque baixo e as últimas transações, com o gráfico de vendas dos últimos 7 dias e as vendas
por forma de pagamento em qualquer período. O estoque tem produtos, categorias, importação por CSV e nível mínimo por
produto. Tem usuários Admin e Caixa, os dados da empresa no recibo, tema claro e escuro, inglês e português.

## Como é feito

Python com Flet, que desenha a interface com Flutter. Cada tela é uma view; as regras de venda, caixa, estoque e login
ficam em serviços; os dados ficam em SQLite pelo SQLModel. As senhas usam bcrypt.
