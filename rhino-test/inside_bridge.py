#! python 3
# -*- coding: utf-8 -*-
"""
inside_bridge.py - runs INSIDE Rhino 7 (IronPython 2.7) via:
    Rhino.exe /nosplash /runscript="_-RunPythonScript \"D:\Apps\pyhopper\rhino-test\inside_bridge.py\""

Starts a tiny TCP server (127.0.0.1:5017) on a background thread. Each request is a Python
source string (terminated by a line containing only "<<END>>"). The code is executed on
Rhino's UI thread with a persistent namespace (like a REPL), stdout is captured and sent
back together with any traceback.  Client: px.py
"""
import sys, threading, socket, traceback
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import System
import Rhino

PORT = 5017
NS = {"__name__": "__rhino_bridge__"}      # persistent namespace across requests


def _run_on_ui(code):
    """Execute `code` on the Rhino UI thread; return captured output text."""
    result = {"out": ""}
    done = threading.Event()

    def job():
        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            exec(code, NS)
        except Exception:
            buf.write(traceback.format_exc())
        finally:
            sys.stdout = old
            result["out"] = buf.getvalue()
            done.set()

    Rhino.RhinoApp.InvokeOnUiThread(System.Action(job))
    done.wait(600)
    return result["out"]


def _serve():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", PORT))
    srv.listen(1)
    while True:
        conn, _ = srv.accept()
        try:
            data = ""
            while "<<END>>" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
            code = data.split("<<END>>")[0]
            if code.strip() == "__quit__":
                out = "bye"
            else:
                out = _run_on_ui(code)
            conn.sendall((out + "\n<<END>>\n").encode("utf-8"))
        except Exception:
            try:
                conn.sendall((traceback.format_exc() + "\n<<END>>\n").encode("utf-8"))
            except Exception:
                pass
        finally:
            conn.close()


t = threading.Thread(target=_serve)
t.daemon = True
t.start()
print("[inside_bridge] listening on 127.0.0.1:%d (Rhino %s)" % (PORT, Rhino.RhinoApp.Version))
