"""Client for rhino_bridge.py:  python rh.py [--port N] "<rhino command line>" [more commands...]"""
import sys, socket
args = sys.argv[1:]
port = 5008
if args and args[0] == "--port":
    port = int(args[1]); args = args[2:]
if args and args[0] in ("7", "8") and len(args) > 1:   # shorthand: rh.py 7 "cmd"
    port = 5007 if args[0] == "7" else 5008; args = args[1:]
for cmd in args:
    s = socket.create_connection(("127.0.0.1", port), timeout=600)
    s.sendall((cmd + "\n").encode("utf-8"))
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = s.recv(65536)
        if not chunk: break
        buf += chunk
    s.close()
    print(f"{cmd!r:60} -> {buf.decode().strip()}")
