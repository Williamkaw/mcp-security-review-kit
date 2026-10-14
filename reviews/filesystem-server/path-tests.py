import json, subprocess, sys
server, data = sys.argv[1], sys.argv[2]
p = subprocess.Popen(["node", server, data], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
def send(m): p.stdin.write(json.dumps(m)+"\n"); p.stdin.flush()
def recv(i):
    while True:
        l=p.stdout.readline()
        if not l: return None
        try: r=json.loads(l)
        except Exception: continue
        if r.get("id")==i: return r
send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}); recv(1)
send({"jsonrpc":"2.0","method":"notifications/initialized"})
for i,(a) in enumerate([("read_text_file",{"path":data+"/sample.txt"}),("read_text_file",{"path":data+"/link.txt"}),("read_text_file",{"path":data+"/../fs-server/package.json"}),("read_text_file",{"path":"/etc/passwd"})],2):
    send({"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":a[0],"arguments":a[1]}})
    r=recv(i); print(a[1]["path"].replace(data,"<data>"),"->",json.dumps(r.get("result",r.get("error")))[:170])
p.terminate()
