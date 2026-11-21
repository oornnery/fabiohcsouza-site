---
title: Yealink Manager
kind: open_source
year: 2024
summary: Controls Yealink phones over the network from Python.
tags: [python, voip, yealink]
repo: https://github.com/oornnery/yealink-manager
updated: 2024-04-17
---

Controls a Yealink desk phone over the network, through its Action URI.

```python
yl = YealinkController("admin", "admin", "192.168.1.10")
yl.set_line(1)
yl.dial("1234")
yl.screenshot()
yl.hangup()
```

A script picks the line, reads the status, dials, hangs up and saves a screenshot of the display. The phone has to
allow Action URI requests from the computer and accept remote control once:

![Action URI allowed in the phone's web interface](assets/action-uri-allowed.png)

![The phone asking to allow remote control](assets/allow-remote-control.png)
