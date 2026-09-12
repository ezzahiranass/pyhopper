"""
rhino_bridge.py - keep a Rhino COM automation object alive and relay commands to it.

Rhino's COM server (Rhino.Application.N) is out-of-process: the Rhino instance exits when
the client that created it releases the object. So this long-running process owns the object
and accepts command strings over a local TCP socket (one line = one Rhino command line).

  .venv\Scripts\python rhino_bridge.py [8|7] [port]     (server, keep running)
  .venv\Scripts\python rh.py "_-Circle 0,0,0 5"         (client)

Protocol: client sends one UTF-8 line; server replies one line: "OK <ret>" | "ERR <msg>".
Special lines: "__ping__", "__quit__" (releases Rhino -> Rhino exits).
"""
import sys, socket, traceback, time
import pythoncom
import win32com.client

version = sys.argv[1] if len(sys.argv) > 1 else "8"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 5008 if version == "8" else 5007

pythoncom.CoInitialize()
t0 = time.time()
rh = win32com.client.Dispatch(f"Rhino.Application.{version}")
while not (rh.IsInitialized() if callable(rh.IsInitialized) else rh.IsInitialized):
    time.sleep(0.5)
rh.Visible = 1
print(f"[bridge] Rhino {version} up via COM in {time.time()-t0:.1f}s", flush=True)

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", port))
srv.listen(1)
print(f"[bridge] listening on 127.0.0.1:{port}", flush=True)

running = True
while running:
    conn, _ = srv.accept()
    with conn:
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(65536)
            if not chunk:
                break
            data += chunk
        line = data.decode("utf-8", "replace").rstrip("\r\n")
        try:
            if line == "__ping__":
                reply = "OK pong"
            elif line == "__quit__":
                reply = "OK bye"
                running = False
            elif line == "__visible__":
                rh.Visible = 1
                reply = f"OK visible={rh.Visible}"
            elif line == "__status__":
                init = rh.IsInitialized() if callable(rh.IsInitialized) else rh.IsInitialized
                reply = f"OK initialized={init} visible={rh.Visible}"
            else:
                # echo=1 shows the command in Rhino's command history (nice for the user to follow)
                ret = rh.RunScript(line, 1)
                reply = f"OK {ret}"
        except Exception as e:
            reply = "ERR " + " ".join(traceback.format_exception_only(type(e), e)).strip()
        print(f"[bridge] {line!r} -> {reply}", flush=True)
        conn.sendall((reply + "\n").encode("utf-8"))

rh = None
pythoncom.CoUninitialize()
print("[bridge] released Rhino, exiting", flush=True)
