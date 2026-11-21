---
title: 'Reading a SIP ladder: what a 488 really means'
summary: Codec negotiation failures, SDP, and where to look first.
created: 2026-08-12
updated: 2026-09-02
project: sipx
status: draft
type: note
tags:
- sip
- voip
---

A `488 Not Acceptable Here` looks simple and almost never is. The far end is saying: *I understood your INVITE, but nothing in your SDP works for me.* The question is always **which part**.

## Start with the offer

Before blaming the carrier, read your own SDP. Most 488s I've chased came down to one of three things:

- No codec overlap: you offered `G.729` only, they only accept `PCMA`.
- Wrong `ptime` or a missing `telephone-event` payload.
- SRTP required on one side, plain RTP offered on the other.

```sdp offer.sdp
m=audio 49170 RTP/AVP 18 101
a=rtpmap:18 G729/8000
a=rtpmap:101 telephone-event/8000
a=ptime:20
```

## Then look at the SBC

If your endpoint offered the right codecs, the SBC may be rewriting the SDP on the way out. Compare the INVITE on the **inside leg** with the one on the **outside leg**. The diff is usually the answer.

> The ladder tells you what happened. The SDP tells you why.

### Checklist

1. Capture both legs (`sngrep` or a PCAP).
2. Diff the SDP in and out of the SBC.
3. Read the `Warning` header.
4. Confirm the carrier's accepted codec list.
