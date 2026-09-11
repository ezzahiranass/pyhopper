"""Client for inside_bridge.py (Python running inside Rhino 7).
   python px.py -c "print(Rhino.RhinoApp.Version)"      # inline code
   python px.py script.py                                 # send a file
"""
import sys, socket
PORT = 5017
if sys.argv[1] == "-c":
    code = sys.argv[2]
else:
    code = open(sys.argv[1], encoding="utf-8").read()
s = socket.create_connection(("127.0.0.1", PORT), timeout=600)
s.sendall((code + "\n<<END>>\n").encode("utf-8"))
buf = b""
while b"<<END>>" not in buf:
    chunk = s.recv(65536)
    if not chunk: break
    buf += chunk
s.close()
print(buf.decode("utf-8", "replace").split("<<END>>")[0].rstrip())
