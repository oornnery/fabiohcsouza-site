---
title: 'Lendo um ladder SIP: o que um 488 quer dizer'
summary: Falhas de negociação de codec, SDP e onde olhar primeiro.
---

Um `488 Not Acceptable Here` parece simples e quase nunca é. O outro lado está dizendo: *entendi seu INVITE, mas nada no seu SDP serve para mim.* A pergunta é sempre **qual parte**.

## Comece pela oferta

Antes de culpar a operadora, leia o seu SDP. A maioria dos 488 que persegui veio de uma destas três coisas:

- Nenhum codec em comum: você ofereceu só `G.729`, eles só aceitam `PCMA`.
- `ptime` errado ou falta do payload `telephone-event`.
- SRTP obrigatório de um lado e RTP simples oferecido do outro.

## Depois olhe o SBC

Se o seu endpoint ofereceu os codecs certos, o SBC pode estar reescrevendo o SDP na saída. Compare o INVITE da **perna interna** com o da **perna externa**. A diferença costuma ser a resposta.
