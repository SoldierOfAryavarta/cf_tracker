import os, json, requests, datetime, time
from zoneinfo import ZoneInfo

HANDLES = ["simplesumit12","theUB_02","WarriorFTW","The_Parzival","devanshudubey7349"]
ONLINE_THRESHOLD = 300
STATE_FILE = "state.json"
LOG_FILE = "sessions.log"
DAILY_FILE = "daily_summary.txt"
LOCAL_TZ = "Asia/Kolkata"
API_URL = "https://codeforces.com/api/user.info?handles=" + ";".join(HANDLES)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE,"r") as f:
                return json.load(f)
        except: pass
    return {h:{"online":False,"start_ts":None,"last_seen_ts":None} for h in HANDLES}

def save_state(state):
    with open(STATE_FILE,"w") as f:
        json.dump(state,f,indent=2)

def fmt_ts(epoch_s):
    tz = ZoneInfo(LOCAL_TZ)
    dt = datetime.datetime.fromtimestamp(epoch_s,tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def append_log(line):
    with open(LOG_FILE,"a") as f:
        f.write(line)

def update_daily_summary():
    today = datetime.datetime.now(ZoneInfo(LOCAL_TZ)).strftime("%Y-%m-%d")
    lines = [line for line in open(LOG_FILE,"r") if line.startswith(today)]
    if not lines: return
    with open(DAILY_FILE,"a") as f:
        f.write(f"Summary for {today}\n-------------------\n")
        f.writelines(lines)
        f.write("\n")

def main():
    now_ts = int(time.time())
    state = load_state()
    try:
        r = requests.get(API_URL,timeout=10).json()
        if r.get("status")!="OK": return
        results = r.get("result",[])
    except: return
    by_handle = {u["handle"]: u for u in results}

    for handle in HANDLES:
        user = by_handle.get(handle)
        last_seen = user.get("lastOnlineTimeSeconds") if user else None
        online = last_seen and (now_ts - int(last_seen) <= ONLINE_THRESHOLD)
        prev_online = state[handle]["online"]

        if not prev_online and online:
            state[handle]["online"] = True
            state[handle]["start_ts"] = int(last_seen)
            state[handle]["last_seen_ts"] = int(last_seen)
        elif prev_online and online:
            state[handle]["last_seen_ts"] = int(last_seen)

        elif prev_online and not online:
            start = state[handle]["start_ts"]
            end = state[handle]["last_seen_ts"]
            duration = end - start
            hours, minutes = divmod(duration // 60, 60)
            line = f"{fmt_ts(start)} - {fmt_ts(end)} | {handle} online {hours}h {minutes}m\n"
            append_log(line)
            state[handle] = {"online":False,"start_ts":None,"last_seen_ts":None}

    save_state(state)
    now = datetime.datetime.now(ZoneInfo(LOCAL_TZ))
    if now.hour==0 and now.minute<5:
        update_daily_summary()

if __name__=="__main__":
    main()
