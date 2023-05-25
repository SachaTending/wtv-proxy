print("WTVProxy by TendingStream73 is starting up...")
from configparser import ConfigParser
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
import json
try: import requests
except ImportError:
    print("requests not found, installing...")
    from pip._internal import main as pmain
    pmain(['install', 'requests'])
    import requests

print("Parsing config...")
cparse = ConfigParser()
cparse.read("config.ini")
print(f"Config sections: {cparse.sections()}")

if cparse.get("General", "Restore",fallback="yes") == "yes":
    print("(RE)Creating config")
    cparse['Server'] = {'Custom': 'no', 'Name': 'hacktv'}
    cparse['General'] = {'Restore': 'no'}
    print("Saving config...")
    cparse.write(open("config.ini", "w"))
print(f"Server: {cparse['Server']['Name']}")

if cparse['Server']['Custom'] == 'no':
    print("Fetching server list from https://rcrms.ru/srvlist.json")
    srvlist = requests.get("https://rcrms.ru/srvlist.json").json()['servers']
    try:
        srv_specs = srvlist['servers'][cparse['Server']['Name']]
    except Exception as e:
        print("Invalid server specified, check if name is valid")
        print("If server is local, check if valude Custom set to yes")
        print(f"Python error: {e}")
        exit(-1)
else:
    print("Getting server info from config")
    srv_conf = cparse[cparse['Server']['Name']]
    srv_specs = {'host': srv_conf['Host'], 'port': int(srv_conf['Port'])}

def handler(sock: socket):
    srv = socket(AF_INET, SOCK_STREAM)
    if srv_specs.get("avaible", "yes") == "no":
        sock.send(f"400 {srv_specs.get('not_avaible_text', 'Server is not public, contact server author for connection info')}\r\nContent-Type: text/html\r\nContent-Length: 0\r\n".encode())
    try: srv.connect((srv_specs['host'], int(srv_specs['port'])))
    except: sock.send(b"400 WTVProxy error: Cannot connect to server\r\nContent-Type: text/html\r\nContent-Length: 0\r\n");sock.close();return
    sock.settimeout(1)
    srv.settimeout(1)
    tsrv = 0
    try:
        while True:
            try: srv.send(sock.recv(16384))
            except TimeoutError: pass
            try: sock.send(srv.recv(16384))
            except TimeoutError: 
                tsrv+=1
                if tsrv > 3:
                    raise Exception("a")
    except Exception as e:
        print(f"handler: Client/Server disconnected(err: {e}), cleaning up")
        sock.close()
        srv.close()

serv = socket(AF_INET, SOCK_STREAM)
serv.bind(('', 1615))
serv.listen(1024 * 1024 * 1024)

while True:
    print("Waiting for connection...")
    try: conn, addr = serv.accept()
    except KeyboardInterrupt:
        print("Clearing up")
        serv.close()
        break
    print(f"Got connection: {addr}")
    Thread(target=handler, name=f"Handler({conn}, {addr})", args=(conn,)).start()