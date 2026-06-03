import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import threading
import os

import importlib.util
_backend_path = os.path.join(os.path.dirname(__file__), '[git commit -m]_p2p_file_sharing.py')
_spec = importlib.util.spec_from_file_location('p2p_backend', _backend_path)
_backend_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_backend_mod)
PeerNode = _backend_mod.PeerNode

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class P2PApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("P2P File Sharing System - CMP2204")
        
        screen_height = self.winfo_screenheight()
        if screen_height < 900:
            self.geometry("820x700")
        else:
            self.geometry("850x780")
            
        self.peer = None
        self.setup_treeview_style()
        self.create_widgets()

    def setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=35,
                        fieldbackground="#2b2b2b",
                        borderwidth=0,
                        font=('Segoe UI', 10))
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#3b3b3b", foreground="white", relief="flat", font=('Segoe UI', 11, 'bold'))

    def create_widgets(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=10)

        header_frame = ctk.CTkFrame(self.main_container, corner_radius=12)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Client Configuration", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 10), sticky="w")

        ctk.CTkLabel(header_frame, text="User:", font=ctk.CTkFont(size=13, weight="bold")).grid(row=1, column=0, padx=20, pady=8, sticky="w")
        self.user_ent = ctk.CTkEntry(header_frame, width=350, height=40, placeholder_text="Enter Username...", font=('Segoe UI', 12))
        self.user_ent.grid(row=1, column=1, padx=5, pady=8)

        ctk.CTkLabel(header_frame, text="File:", font=ctk.CTkFont(size=13, weight="bold")).grid(row=2, column=0, padx=20, pady=8, sticky="w")
        self.file_ent = ctk.CTkEntry(header_frame, width=350, height=40, placeholder_text="Select a file to host...", font=('Segoe UI', 12))
        self.file_ent.grid(row=2, column=1, padx=5, pady=8)
        
        self.browse_btn = ctk.CTkButton(header_frame, text="Browse", width=100, height=40, fg_color="#4b4b4b", hover_color="#5b5b5b", font=ctk.CTkFont(weight="bold"), command=self.get_file)
        self.browse_btn.grid(row=2, column=2, padx=15, pady=8)

        btn_grid = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_grid.grid(row=3, column=0, columnspan=3, pady=(15, 20), sticky="we")
        btn_grid.grid_columnconfigure((0,1), weight=1)

        self.start_btn = ctk.CTkButton(btn_grid, text="INITIALIZE SYSTEM", height=48, fg_color="#28a745", hover_color="#218838", font=ctk.CTkFont(size=14, weight="bold"), command=self.run_system)
        self.start_btn.grid(row=0, column=0, padx=(20, 10), sticky="we")

        self.stop_btn = ctk.CTkButton(btn_grid, text="STOP SYSTEM", height=48, fg_color="#4b4b4b", hover_color="#dc3545", font=ctk.CTkFont(size=14, weight="bold"), state="disabled", command=self.stop_system)
        self.stop_btn.grid(row=0, column=1, padx=(10, 20), sticky="we")

        list_frame = ctk.CTkFrame(self.main_container, corner_radius=12)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(list_frame, text="Network Content Discovery", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        tree_container = ctk.CTkFrame(list_frame, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=20, pady=5)

        self.tree = ttk.Treeview(tree_container, columns=("Content", "Status"), show='headings')
        self.tree.heading("Content", text="File Name")
        self.tree.heading("Status", text="Availability Status")
        self.tree.column("Content", width=400)
        self.tree.column("Status", width=200)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ctk.CTkScrollbar(tree_container, orientation="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        dl_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        dl_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.dl_btn = ctk.CTkButton(dl_frame, text="Standard Download", width=190, height=40, font=ctk.CTkFont(weight="bold"), command=lambda: self.download_trigger(False))
        self.dl_btn.pack(side="left", padx=5)

        self.sdl_btn = ctk.CTkButton(dl_frame, text="Secure Download (DES)", width=210, height=40, fg_color="#6f42c1", hover_color="#59369c", font=ctk.CTkFont(weight="bold"), command=lambda: self.download_trigger(True))
        self.sdl_btn.pack(side="left", padx=5)

        bottom_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.stat_msg = ctk.StringVar(value="System Ready")
        ctk.CTkLabel(bottom_frame, textvariable=self.stat_msg, text_color="gray", font=('Segoe UI', 11)).pack(side="left", padx=10)

        ctk.CTkButton(bottom_frame, text="View Logs", width=120, height=32, fg_color="transparent", border_width=1, text_color="gray", command=self.open_logs).pack(side="right", padx=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.file_ent.configure(state="normal")
            self.file_ent.delete(0, ctk.END)
            self.file_ent.insert(0, f)

    def run_system(self):
        u, p = self.user_ent.get().strip(), self.file_ent.get().strip()
        if not u or not p:
            messagebox.showwarning("Warning", "Fields cannot be empty!")
            return
        try:
            self.peer = PeerNode(username=u, file_path=p)
            self.peer.start()
            self.start_btn.configure(state="disabled", text="ONLINE", fg_color="#4b4b4b")
            self.stop_btn.configure(state="normal", fg_color="#dc3545")
            self.user_ent.configure(state="disabled"); self.file_ent.configure(state="disabled"); self.browse_btn.configure(state="disabled")
            self.stat_msg.set(f"Online: {u}"); self.auto_update()
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_system(self):
        if self.peer: self.peer.stop(); self.peer = None
        self.start_btn.configure(state="normal", text="INITIALIZE SYSTEM", fg_color="#28a745")
        self.stop_btn.configure(state="disabled", fg_color="#4b4b4b")
        self.user_ent.configure(state="normal"); self.file_ent.configure(state="normal"); self.browse_btn.configure(state="normal")
        self.stat_msg.set("System Offline"); [self.tree.delete(i) for i in self.tree.get_children()]

    def auto_update(self):
        if not self.peer: return
        [self.tree.delete(i) for i in self.tree.get_children()]
        files = {}
        for chunk in self.peer.content_dict:
            name = chunk.rsplit('_', 1)[0]
            files[name] = files.get(name, 0) + 1
        for name, count in files.items():
            self.tree.insert("", "end", values=(name, f"{count}/3 Chunks"))
        self.after(5000, self.auto_update)

    def download_trigger(self, is_secure):
        item = self.tree.selection()
        if not item: return messagebox.showwarning("!", "Select a file first.")
        fname = self.tree.item(item[0])['values'][0]
        self.stat_msg.set(f"Downloading {fname}...")
        threading.Thread(target=self.do_download, args=(fname, is_secure), daemon=True).start()

    def do_download(self, fname, is_secure):
        try:
            needed_chunks = sorted([c for c in self.peer.content_dict if c.startswith(fname + "_")])
            downloaded_data = {}
            for chunk_name in needed_chunks:
                ips = self.peer.content_dict.get(chunk_name, [])
                success = False
                for ip in ips:
                    try:
                        data = self.peer._download_secure_chunk(ip, chunk_name) if is_secure else self.peer._download_unsecure_chunk(ip, chunk_name)
                        if data:
                            downloaded_data[chunk_name] = data
                            with open(chunk_name, 'wb') as cf: cf.write(data)
                            success = True; break
                    except: continue
                if not success: raise Exception(f"Failed {chunk_name}")
            output_path = os.path.join(os.getcwd(), fname)
            with open(output_path, 'wb') as f:
                for key in sorted(downloaded_data.keys()): f.write(downloaded_data[key])
            self.stat_msg.set(f"Done: {fname}")
            self.after(0, lambda: messagebox.showinfo("Success", f"{fname} reassembled."))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda m=msg: messagebox.showerror("Error", m))

    def open_logs(self):
        log_win = ctk.CTkToplevel(self); log_win.title("Logs"); log_win.geometry("600x450"); log_win.attributes("-topmost", True)
        txt = ctk.CTkTextbox(log_win, font=('Consolas', 11), corner_radius=10); txt.pack(fill="both", expand=True, padx=15, pady=15)
        c = "=== LOGS ===\n"
        if os.path.exists("download_log.txt"):
            with open("download_log.txt", "r") as f: c += f.read()
        txt.insert("1.0", c); txt.configure(state="disabled")

    def on_closing(self):
        self.stop_system(); self.destroy()

if __name__ == "__main__":
    app = P2PApp()
    app.mainloop()