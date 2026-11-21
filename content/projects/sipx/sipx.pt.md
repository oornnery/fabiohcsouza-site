---
title: sipx
summary: Biblioteca SIP assíncrona em Python, no estilo do httpx.
---

O `sipx` manda SIP pelo Python do jeito que o httpx manda HTTP: um cliente assíncrono, um objeto de configuração e
autenticação Digest opcional. Não tem dependências e usa Python 3.14.

```python
async with AsyncClient(settings=settings, auth=auth) as client:
    response = await client.register("sip:pbx.example.com:5060")
    print(response.status_code, response.reason)
```

## O que faz

Como cliente, manda REGISTER, OPTIONS, MESSAGE, INVITE, SUBSCRIBE, ACK, BYE, CANCEL e qualquer outro método, e também
responde requisições como servidor. Segue as regras das RFCs que contam numa rede de verdade: retransmissão em UDP, o
ACK automático num INVITE recusado, rport, respostas provisórias confiáveis (PRACK) e Digest com MD5 ou SHA-256.

Na mídia, negocia SDP (PCMU, PCMA e eventos DTMF) e tem RTP com G.711, DTMF pela RFC 4733 e jitter buffer, então um
exemplo consegue fazer uma ligação e tocar áudio.

## Como é organizado

O código de SIP, SDP e RTP não faz I/O: são parsers e serializadores que não tocam a rede e são testados sozinhos.
Acima deles ficam as transações, os diálogos e a autenticação, depois os transportes UDP, TCP e TLS, e o cliente por
cima. Os event hooks veem cada requisição e resposta, o que ajuda a depurar uma ligação.
