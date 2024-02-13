
<p align="center">
<img src="./doc/image/logo_nke.png" width="250"/>
</p>

# USEA-Payload

nke Instrumentation provides this application programming interface (API) for PROVOR-CTS5 float.\
It enables third-party Python programming in USEA-Payload acquisition board.

<p align="center">
<img src="./doc/image/USEA-Board.png" height="250"/>
</p>

### Objective
- Develop new capabilities for profiling floats:
  - Integrate challenging sensors
  - Assessment of specific data processing
- Validate performance prior to industrial integration by nke

## Resources

### Developer support

[API documentation](https://support.nke-instrumentation.com/USEA-Payload-Documentation/index.html)

### Application file tree

```
+-- system
|   +-- config.py
|   +-- const.py
|   +-- ctd.py
|   +-- emap.py
|   +-- io_lib.py
|   +-- rtc.py
|   +-- serial_lib.py
|   +-- share_lib.py
|   +-- system_lib.py
|   +-- technical.py
|   +-- timer_lib.py
|   +-- trace_lib.py
|   +-- web_server.py
+-- user
|   +-- user.ini
|   +-- user_driver.py
main.py
```

## Version history

### 1.0.0 (2024-01-31)
- Creating reference application

## License information

This application is restricted to PROVOR-CTS5 use.\
All rights reserved to [nke Instrumentation](https://www.nke-instrumentation.com).

<p align="center">
<img src="./doc/image/Float2.png" width="850"/>
</p>
