---
title: icmpx
kind: open_source
year: 2025
summary: A Python library for ICMP diagnostics over raw sockets.
tags: [python, networking, icmp, textual]
repo: https://github.com/oornnery/icmpx
updated: 2025-10-15
---

A Python library for ping and traceroute over raw sockets, built from parts instead of wrapping the system tools.

![The ping view of the terminal UI](assets/ping-tui.png)

## The library

A `Client` opens and closes the raw socket. `probe()` sends one packet with a given TTL, `ping()` repeats it and
`traceroute()` walks the hops; each returns dataclasses with the times and the replies, ready to print or store.
Reverse DNS is optional per request. When Python lacks `CAP_NET_RAW`, the error says so, and
`uvx icmpx --bootstrap-cap` grants it.

## The terminal UI

`uvx icmpx` opens a Textual app with four views: ping with a live loss and RTT summary, ping to several hosts at once,
traceroute, and an MTR view that keeps refreshing the stats of each hop. The examples folder has the same flows as
short scripts, including an MTR table made with Rich.

![Ping to several hosts](assets/multiping-tui.png)

![Traceroute](assets/traceroute-tui.png)

![The MTR view](assets/mtr-tui.png)
