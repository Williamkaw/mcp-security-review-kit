import json, subprocess, sys
cmd, out = sys.argv[1], sys.argv[2]
p = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
def send(m): p.stdin.write(json.dumps(m)+"\n"); p.stdin.flush()
def recv(i):
    while True:
        l=p.stdout.readline()
        if not l: return None
        try: r=json.loads(l)
        except Exception: continue
        if r.get("id")==i: return r
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}); init=recv(1)
send({"jsonrpc":"2.0","method":"notifications/initialized"})
send({"jsonrpc":"2.0","id":2,"method":"tools/list"}); tl=recv(2)
json.dump({"serverInfo":init["result"].get("serverInfo"),"tools":tl["result"]["tools"]},open(out,"w"),indent=2)
print(init["result"].get("serverInfo"), len(tl["result"]["tools"]))
for i,u in enumerate(["http://127.0.0.1:8080/","http://169.254.169.254/latest/meta-data/","http://2130706433/","http://[::ffff:127.0.0.1]/","file:///etc/passwd"],3):
    send({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":"fetch","arguments":{"url":u}}})
    r=recv(i); print(u,"->",json.dumps(r.get("result",r.get("error")))[:210])
p.terminate()
