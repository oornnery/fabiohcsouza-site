---
title: sipx
kind: open_source
year: 2025
summary: An async SIP library for Python, in the style of httpx.
tags: [python, sip, voip, rtp, asyncio]
repo: https://github.com/oornnery/sipx
updated: 2026-06-14
---

`sipx` sends SIP from Python the way httpx sends HTTP: one async client, one settings object and optional Digest
authentication. It has no runtime dependencies and needs Python 3.14.

```python
async with AsyncClient(settings=settings, auth=auth) as client:
    response = await client.register("sip:pbx.example.com:5060")
    print(response.status_code, response.reason)
```

## What it does

As a client it sends REGISTER, OPTIONS, MESSAGE, INVITE, SUBSCRIBE, ACK, BYE, CANCEL and any other method, and it
can also answer requests as a server. It follows the RFC rules that matter on a real network: UDP retransmission,
the automatic ACK on a failed INVITE, rport, reliable provisional responses (PRACK), and Digest with MD5 or SHA-256.

For media it negotiates SDP (PCMU, PCMA and DTMF events) and has RTP with G.711, RFC 4733 DTMF and a jitter buffer,
so an example can place a call and play audio.

## How it is organized

The SIP, SDP and RTP code is sans-I/O: parsers and serializers that don't touch the network, tested on their own.
Above them sit the transactions, dialogs and authentication, then the UDP, TCP and TLS transports, and the client on
top. Event hooks see every request and response, which helps when debugging a call.
