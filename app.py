import json
import getpass
import os
import threading
import tkinter
import tkinter as tk
import tkinter.ttk as ttk
from pystray import MenuItem as item
import pystray
from PIL import Image
import requests
import time

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import sv_ttk

dir_path = os.path.dirname(os.path.realpath(__file__)) + str('/')
USER_NAME = getpass.getuser()

import sys
base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
icon_path = os.path.join(base_path, 'assets', 'distatus.ico')

patchURL = 'https://discord.com/api/v10/users/@me/settings'

def add_to_startup(file_path=""):
  if file_path == "":
    file_path = os.getcwd() + '\\distatus.exe'

  startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
  shortcut_path = os.path.join(startup_path, 'distatus.lnk')

  try:
    import pythoncom
    from win32com.shell import shell, shellcon

    shell_link = pythoncom.CoCreateInstance(
      shell.CLSID_ShellLink, None,
      pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
    )
    shell_link.SetPath(file_path)
    shell_link.SetDescription('Start Distatus')
    shell_link.SetWorkingDirectory(os.path.dirname(file_path))
    persist_file = shell_link.QueryInterface(pythoncom.IID_IPersistFile)
    persist_file.Save(shortcut_path, 0)
    print(f"Shortcut created at {shortcut_path}")
  except ImportError:
    print("pywin32 is required to create shortcut. You can install it with 'pip install pywin32'")

def remove_from_startup():
  startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
  print(f"Startup path: {startup_path}")
  shortcut_path = os.path.join(startup_path, 'distatus.lnk')

  try:
    if os.path.exists(shortcut_path):
      os.remove(shortcut_path)
      print(f"Shortcut removed from {shortcut_path}")
    else:
      print("No startup shortcut found.")
  except Exception as e:
    print(f"Error removing shortcut: {e}")

def check_startup():
  startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
  shortcut_path = os.path.join(startup_path, 'distatus.lnk')

  return os.path.exists(shortcut_path)

def create_appdata_folder():
  appdata_folder = os.path.join(os.getenv("APPDATA"), "Distatus")
  if not os.path.exists(appdata_folder):
    os.makedirs(appdata_folder)
    print(f"AppData folder created at {appdata_folder}")
  else:
    print(f"AppData folder already exists at {appdata_folder}")

def find_appdata_folder():
  appdata_folder = os.path.join(os.getenv("APPDATA"), "Distatus")
  if os.path.exists(appdata_folder):
    return appdata_folder
  else:
    print("AppData folder not found.")
    return None

create_appdata_folder()
class App:
 def __init__(self):
  try:
   self.appdataFolder = find_appdata_folder()
   self.icon = None

   self.statusFile = f'{self.appdataFolder}\\status.json'
   self.configFile = f'{self.appdataFolder}\\config.json'

   self.statusLines = json.load(open(self.statusFile, 'r'))
  except FileNotFoundError:
   with open(self.statusFile, 'w') as statusFile:
    json.dump([], statusFile, indent=1)
   self.statusLines = []

  try:
    with open(self.configFile, 'r') as configFile:
      self.data = json.load(configFile)
  except FileNotFoundError:
    with open(self.configFile, 'w') as configFile:
      default_config = {
      "TOKEN": None,
      "TIME": 10,
      "START_MINIMISED": False,
      "START_ON_STARTUP": False
      }
      json.dump(default_config, configFile, indent=1)
      self.data = default_config

  self.headers = { "authorization": self.data['TOKEN'] }

  if self.data['TIME'] < 10:
    self.data['TIME'] = 10

  self.token = self.data['TOKEN'] if 'TOKEN' in self.data else ""
  self.time = self.data['TIME'] if 'TIME' in self.data else 10
  self.startMinimised = self.data['START_MINIMISED'] if 'START_MINIMISED' in self.data else False
  self.startOnStartup = self.data['START_ON_STARTUP'] if 'START_ON_STARTUP' in self.data else False

  if self.startOnStartup:
   if not check_startup():
    add_to_startup()

  self.check_token_stop_event = threading.Event()
  self.update_status_stop_event = threading.Event()

  self.check_token_proc = threading.Thread(target=self.check_token, name="check_token", daemon=True)
  self.check_token_proc.start()

  self.root = tk.Tk()
  self.root.protocol("WM_DELETE_WINDOW", self.minimise)
  if self.startMinimised == True:
   self.minimise()  # Start minimised
  self.root.title("discord-status by @nero")
  self.root.geometry("400x300")
  self.root.iconbitmap(icon_path)
  self.root.resizable(False, False)

  ## Load tabs
  self.tabControl = ttk.Notebook(self.root)
  self.addTab = ttk.Frame(self.tabControl)
  self.removeTab = ttk.Frame(self.tabControl)
  self.configTab = ttk.Frame(self.tabControl)
  self.tabControl.add(self.addTab, text="Add Status")
  self.tabControl.add(self.removeTab, text="Remove Status")
  self.tabControl.add(self.configTab, text="Config")

  ## Tabs 
  self.tabControl.pack(expand=1, fill="both")

  self.button = tk.Button(self.root, text="X", command=self.minimise, border=0, font=("Verdana", 10, "bold"), width=2, height=1)
  self.button.place(relx=1, rely=0, anchor='ne')

  ## Load add status tab elements
  tk.Label(self.addTab, text="Status Message", font=("Verdana", 9)).place(relx=0.01, rely=0.1, anchor='w')
  self.statusMsg = tk.StringVar(self.addTab, value="You're as beautiful as the day I lost you.", name="statusMsg")
  self.statusEntry = ctk.CTkEntry(self.addTab, textvariable=self.statusMsg, width=310, font=("Verdana", 9))
  self.statusEntry.place(relx=0.4, rely=0.2, anchor='center')

  tk.Label(self.addTab, text="Emoji Name", font=("Verdana", 9)).place(relx=0.01, rely=0.3, anchor='w')
  self.statusMsgEmojiName = tk.StringVar(self.addTab, value="Heart500", name="emojiName")
  self.emojiNameEntry = ctk.CTkEntry(self.addTab, textvariable=self.statusMsgEmojiName, width=310, font=("Verdana", 9))
  self.emojiNameEntry.place(relx=0.4, rely=0.4, anchor='center')

  tk.Label(self.addTab, text="Emoji ID", font=("Verdana", 9)).place(relx=0.01, rely=0.5, anchor='w')
  self.statusMsgEmojiID = tk.StringVar(self.addTab, value="667324331654643732", name="emojiID")
  self.emojiIDEntry = ctk.CTkEntry(self.addTab, textvariable=self.statusMsgEmojiID, width=310, font=("Verdana", 9))
  self.emojiIDEntry.place(relx=0.4, rely=0.6, anchor='center')

  self.addButton = ctk.CTkButton(self.addTab, text="Add Status", command=lambda: self.set_statusline(self.statusMsg, self.statusMsgEmojiID, self.statusMsgEmojiName), width=20, corner_radius=8, font=("Verdana", 9))
  self.addButton.place(relx=0.5, rely=0.8, anchor='center')

  ## Load remove status tab elements
  tk.Label(self.removeTab, text="Status Lines", font=("Verdana", 9)).place(relx=0.01, rely=0.1, anchor='w')
  self.statusList = ctk.CTkComboBox(self.removeTab, width=310, font=("Verdana", 9), values=[status['msg'] for status in self.statusLines], state="readonly")
  self.statusList.place(relx=0.4, rely=0.2, anchor='center')

  self.removeButton = ctk.CTkButton(self.removeTab, text="Remove Status", command=lambda: self.remove_statusline(), width=20, corner_radius=8, font=("Verdana", 9))
  self.removeButton.place(relx=0.5, rely=0.4, anchor='center')

  ## Load config tab elements
  tk.Label(self.configTab, text="Token", font=("Verdana", 9)).place(relx=0.01, rely=0.1, anchor='w')
  self.tokenVar = tk.StringVar(self.configTab, value=self.token, name="token")
  self.tokenEntry = ctk.CTkEntry(self.configTab, textvariable=self.tokenVar, width=310, font=("Verdana", 9), show="*")
  self.tokenEntry.place(relx=0.4, rely=0.2, anchor='center')

  tk.Label(self.configTab, text="Time", font=("Verdana", 9)).place(relx=0.01, rely=0.3, anchor='w')
  self.timeVar = tk.StringVar(self.configTab, value=str(self.time), name="time")
  self.timeEntry = ctk.CTkEntry(self.configTab, textvariable=self.timeVar, width=310, font=("Verdana", 9))
  self.timeEntry.place(relx=0.4, rely=0.4, anchor='center')

  tk.Label(self.configTab, text="Start Minimized", font=("Verdana", 9)).place(relx=0.01, rely=0.5, anchor='w')
  self.startMinimizedVar = tk.BooleanVar(self.configTab, value=self.startMinimised, name="startMinimized")
  self.startMinimizedCheck = ctk.CTkCheckBox(self.configTab, text="", variable=self.startMinimizedVar, onvalue=True, offvalue=False, width=20, font=("Verdana", 9))
  self.startMinimizedCheck.place(relx=0.05, rely=0.6, anchor='center')

  tk.Label(self.configTab, text="Start on startup", font=("Verdana", 9)).place(relx=0.4, rely=0.5, anchor='w')
  self.startOnStartupVar = tk.BooleanVar(self.configTab, value=self.startOnStartup, name="startOnStartupVar")
  self.startOnStartup = ctk.CTkCheckBox(self.configTab, text="", variable=self.startOnStartupVar, onvalue=True, offvalue=False, width=20, font=("Verdana", 9))
  self.startOnStartup.place(relx=0.45, rely=0.6, anchor='center')

  self.saveConfigButton = ctk.CTkButton(self.configTab, text="Save Config", command=lambda: self.save_config(), width=20, corner_radius=8, font=("Verdana", 9))
  self.saveConfigButton.place(relx=0.5, rely=0.8, anchor='center')

  ## Load the theme
  sv_ttk.set_theme("dark")

 def check_status(self):
  self.statusLines = json.load(open(self.statusFile, 'r'))

 def start_update_process(self):
  if "update_status" in threading.enumerate():
   if self.update_status_proc and self.update_status_proc.is_alive():
    print("Status update process is already running.")
    return

  if not self.token:
   print("No token found, please set your token in the config.")
   return

  self.update_status_proc = threading.Thread(target=self.update_status, name="update_status", daemon=True)
  self.update_status_proc.start()
  print("Status update process started.")

  self.check_token_stop_event.set()
  print("Token check process stopped.")
 
 def check_token(self):
  foundToken = False
  while not foundToken and not self.check_token_stop_event.is_set():
   try:
    with open(self.configFile, 'r') as configFile:
     print("Checking for token in config file...")
     data = json.load(configFile)
     if data['TOKEN'] is not None and data['TOKEN'] != "":
      foundToken = True
      self.token = data['TOKEN']
      self.headers["authorization"] = self.token
      print("Token found, starting status update process.")
      self.start_update_process()
   except FileNotFoundError:
    print("Config file not found, waiting for it to be created.")
   self.check_token_stop_event.wait(5)

 def save_config(self):
  token = self.tokenVar.get()
  time = self.timeVar.get()
  startMinimized = self.startMinimizedVar.get()
  startOnStartup = self.startOnStartupVar.get()

  if not token or not time:
   CTkMessagebox(title="Error", message="Please fill all fields.", icon="cancel")
   return

  try:
   time = int(time)
   if time < 10:
    raise ValueError("Time must be at least 10 seconds.")
  except ValueError as e:
   CTkMessagebox(title="Error", message=str(e), icon="cancel")
   return
  
  if startOnStartup:
    if not check_startup():
      add_to_startup()
    else:
      print("Already set to start on startup.")
  else:
    if check_startup():
      remove_from_startup()

  self.data['TOKEN'] = token
  self.data['TIME'] = time
  self.data['START_MINIMISED'] = startMinimized
  self.data['START_ON_STARTUP'] = startOnStartup

  with open(self.configFile, 'w') as configFile:
   json.dump(self.data, configFile, indent=1)

  CTkMessagebox(title="Success", message="Config saved successfully.", icon="check")

 def close(self):
  if self.icon:
    self.icon.stop()

  app.check_token_stop_event.set()
  app.update_status_stop_event.set()

  if hasattr(app, 'check_token_proc'):
    app.check_token_proc.join(timeout=1)

  if hasattr(app, 'update_status_proc'):
    app.update_status_proc.join(timeout=1)
  
  time.sleep(2)
  self.root.destroy()

 def bring_to_front(self):
  self.root.deiconify()
  self.root.lift()
  self.root.focus_force()

 def open_window(self):
  self.icon.stop()
  self.root.after(10, self.bring_to_front())

 def minimise(self):
  self.root.withdraw()
  self.image = Image.open(icon_path)
  self.menu = (item('Open', self.open_window), item('Exit', self.close))
  self.icon = pystray.Icon("discord-status", self.image, "discord-status", self.menu)
  self.icon.run()

 def update_status(self):
  # refresh the status lines every cycle
  while not self.update_status_stop_event.is_set():
    self.check_status()
    if self.statusLines == []:
      print("No status lines found, waiting for them to be added.")
      self.update_status_stop_event.wait(self.data['TIME'])
      continue 

    for statusLine in self.statusLines:
      if self.update_status_stop_event.is_set():
        print("Status update process stopped.")
        break

      jsonData = {
        "custom_status": { "text": statusLine['msg'] }
      }

      if statusLine['emojiName'] != "" and statusLine['emojiID'] != "":
        jsonData['custom_status'].update({ "emoji_name": statusLine['emojiName'], "emoji_id": statusLine['emojiID'] })

      try:
        resp = requests.patch(patchURL, headers=self.headers, json=jsonData)
        if resp.status_code == 401:
          print("Invalid token. Please update your config.")
          return
      except Exception as e:
        print(f"Error updating status: {e}")
        continue

      self.update_status_stop_event.wait(self.data['TIME'])

 def remove_statusline(self):
  option = self.statusList.get()
  if not option:
   CTkMessagebox(title="Error", message="Please select a status line to remove.", icon="cancel")
   return
  
  for status in self.statusLines:
   if status['msg'] == option:
    self.statusLines.remove(status)
    with open(self.statusFile, 'w') as statusFile:
     json.dump(self.statusLines, statusFile, indent=1)
    CTkMessagebox(title="Success", message="Status line removed successfully.", icon="check")

  self.check_status()
  self.root.after(0, lambda: self.statusList.configure(values=[status['msg'] for status in self.statusLines]))

 def set_statusline(self, msg, emojiID, emojiName):
  if not msg.get():
    CTkMessagebox(title="Error", message="Please fill the message field.", icon="cancel")
    return
  
  if (emojiName.get() == "" and emojiID.get() != "") or (emojiName.get() != "" and emojiID.get() == ""):
    CTkMessagebox(title="Error", message="Please fill both emoji fields or leave both empty.", icon="cancel")
    return
  
  newStatus = {
   "msg": msg.get(),
   "emojiID": emojiID.get(),
   "emojiName": emojiName.get()
  }

  self.statusLines.append(newStatus)
  with open(self.statusFile, 'w') as statusFile:
   json.dump(self.statusLines, statusFile, indent=1)

  CTkMessagebox(title="Success", message="Status line added successfully.", icon="check")

  self.check_status()
  self.root.after(0, lambda: self.statusList.configure(values=[status['msg'] for status in self.statusLines]))

if __name__ == "__main__":
  try:
    print("Starting discord-status by @nero")
    app = App()
    app.root.mainloop()

  except KeyboardInterrupt:
    print("Exiting discord-status by @nero")
    if app.icon:
      app.icon.stop()
    
    app.check_token_stop_event.set()
    app.update_status_stop_event.set()

    if hasattr(app, 'check_token_proc'):
      app.check_token_proc.join(timeout=1)

    if hasattr(app, 'update_status_proc'):
      app.update_status_proc.join(timeout=1)

    app.root.destroy()
    print("Application closed successfully.")

  except Exception as e:
    print("Error happened so exiting discord-status by @nero")
    if app.icon:
      app.icon.stop()
    
    app.check_token_stop_event.set()
    app.update_status_stop_event.set()

    if hasattr(app, 'check_token_proc'):
      app.check_token_proc.join(timeout=1)

    if hasattr(app, 'update_status_proc'):
      app.update_status_proc.join(timeout=1)

    app.root.destroy()
    print("Application closed successfully.")
