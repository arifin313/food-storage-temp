import json, os, time, threading, math, random, csv
from collections import deque
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib import request as urlreq

E = lambda k, d: float(os.getenv(k, d))
S = dict(mode=os.getenv("MODE", "sim"), temp=E("START_TEMP", 28), hum=60.0,
         ambient=E("AMBIENT", 32), setpoint=E("SETPOINT", 20), band=E("BAND", 1.0),
         alarm_high=E("ALARM_HIGH", 25), alarm_low=E("ALARM_LOW", 5),
         cooler=False, heater=False, alarm="", last_sensor=0.0)
SPEED, MIN_SWITCH, ACT_URL = E("SIM_SPEED", 10), E("MIN_SWITCH_SEC", 5), os.getenv("ACTUATOR_URL", "")
HIST = deque(maxlen=720); LOCK = threading.Lock(); last_sw = 0.0
os.makedirs("/data", exist_ok=True); LOG = "/data/log.csv"

def actuate():
    if not ACT_URL: return
    try:
        req = urlreq.Request(ACT_URL, json.dumps({"cooler": S["cooler"], "heater": S["heater"]}).encode(),
                             {"Content-Type": "application/json"})
        urlreq.urlopen(req, timeout=3)
    except Exception as e: print("actuator error:", e, flush=True)

def control():
    global last_sw
    t, sp, b, now = S["temp"], S["setpoint"], S["band"], time.time()
    c, h = S["cooler"], S["heater"]
    if c and t <= sp: c = False
    if h and t >= sp: h = False
    if not c and not h and now - last_sw >= MIN_SWITCH:
        if t > sp + b: c = True
        elif t < sp - b: h = True
    if (c, h) != (S["cooler"], S["heater"]):
        S["cooler"], S["heater"], last_sw = c, h, now
        threading.Thread(target=actuate, daemon=True).start()

def loop():
    n = 0
    while True:
        time.sleep(1); n += 1
        with LOCK:
            if S["mode"] == "sim":
                dt = SPEED
                dT = (S["ambient"] - S["temp"]) * 0.0005 * dt
                dT += (0.010 if S["heater"] else 0) * dt - (0.012 if S["cooler"] else 0) * dt
                S["temp"] += dT + random.uniform(-0.02, 0.02)
                S["hum"] = max(30, min(90, S["hum"] + random.uniform(-0.3, 0.3)))
                S["last_sensor"] = time.time()
            S["alarm"] = ""
            if time.time() - S["last_sensor"] > 30: S["alarm"] = "Sensor data pachchhi na"
            elif S["temp"] > S["alarm_high"]: S["alarm"] = "Temperature beshi (khabar nosto hote pare)"
            elif S["temp"] < S["alarm_low"]: S["alarm"] = "Temperature onek kom"
            if S["alarm"] == "Sensor data pachchhi na": S["cooler"] = S["heater"] = False
            else: control()
            if n % 5 == 0:
                row = [int(time.time()), round(S["temp"], 2), round(S["hum"], 1), int(S["cooler"]), int(S["heater"]), S["setpoint"]]
                HIST.append(row)
                if n % 10 == 0:
                    new = not os.path.exists(LOG)
                    with open(LOG, "a", newline="") as f:
                        w = csv.writer(f)
                        if new: w.writerow(["ts", "temp", "hum", "cooler", "heater", "setpoint"])
                        w.writerow(row)

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, obj, code=200, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == "/api/status":
            with LOCK: return self.send({**S, "temp": round(S["temp"], 2), "hum": round(S["hum"], 1), "hist": list(HIST)})
        if self.path == "/api/log":
            return self.send(open(LOG, "rb").read() if os.path.exists(LOG) else b"", ctype="text/csv")
        self.send(open("/app/static/index.html", "rb").read(), ctype="text/html; charset=utf-8")
    def do_POST(self):
        try: d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except Exception: return self.send({"error": "bad json"}, 400)
        with LOCK:
            if self.path == "/api/sensor":  # real sensor theke data (ESP32/Arduino etc.)
                S["temp"] = float(d["temp"]); S["hum"] = float(d.get("hum", S["hum"])); S["last_sensor"] = time.time()
            elif self.path == "/api/config":
                for k in ("setpoint", "band", "alarm_high", "alarm_low", "ambient"):
                    if k in d: S[k] = float(d[k])
                if d.get("mode") in ("sim", "real"): S["mode"] = d["mode"]
            else: return self.send({"error": "not found"}, 404)
        self.send({"ok": True})

if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    print("Running on http://localhost:8080", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
