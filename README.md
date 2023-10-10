
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

## Application file tree

USEA-Payload API comes with the following system resources:
```
+-- system
|   +-- emap.py
|   +-- ctd.py
|   +-- io_lib.py
|   +-- serial_lib.py
|   +-- share_lib.py
|   +-- timer_lib.py
|   +-- trace_lib.py
+-- user
|   +-- sensor.py
main.py
```

## Version history

### 1.0.0 (2023-09-25)
- Creating reference application

## License information

This application is restricted to PROVOR-CTS5 use.\
All rights reserved to nke Instrumentation.

<p align="center">
<img src="./doc/image/Float2.png" width="850"/>
</p>
