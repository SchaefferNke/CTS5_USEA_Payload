rem rename system files
copy .\system\config.py system#config.py
copy .\system\const.py system#const.py
copy .\system\ctd.py system#ctd.py
copy .\system\emap.py system#emap.py
copy .\system\io_lib.py system#io_lib.py
copy .\system\rtc.py system#rtc.py
copy .\system\serial_lib.py system#serial_lib.py
copy .\system\share_lib.py system#share_lib.py
copy .\system\system_lib.py system#system_lib.py
copy .\system\technical.py system#technical.py
copy .\system\timer_lib.py system#timer_lib.py
copy .\system\trace_lib.py system#trace_lib.py
copy .\system\web_server.py system#web_server.py
rem create update archive
tar.exe -a -c -f payload_update.zip main.py system#config.py system#const.py system#ctd.py system#emap.py system#io_lib.py system#rtc.py system#serial_lib.py system#share_lib.py system#system_lib.py system#technical.py system#timer_lib.py system#trace_lib.py system#web_server.py
rem delete temporary files
del system#config.py
del system#const.py
del system#ctd.py
del system#emap.py
del system#io_lib.py
del system#rtc.py
del system#serial_lib.py
del system#share_lib.py
del system#system_lib.py
del system#technical.py
del system#timer_lib.py
del system#trace_lib.py
del system#web_server.py
pause
