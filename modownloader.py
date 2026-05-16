import os
import requests
from PIL import Image, ImageTk
from io import BytesIO
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

# ----------------------------
# CONFIG
# ----------------------------

# Custom font
APP_FONT = "Minecrafter"
# ----------------------------
MODRINTH_API = "https://api.modrinth.com/v2"

# Default Minecraft mods folder
MINECRAFT_MODS_FOLDER = os.path.join(
    os.getenv("APPDATA"), ".minecraft", "versions"
)

current_mods_folder = MINECRAFT_MODS_FOLDER

# ----------------------------
# MAIN WINDOW
# ----------------------------
root = tk.Tk()
root.title("Modownloader")
root.configure(bg="#222b22")

# Screen setup
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.geometry(f"{screen_width}x{screen_height}+0+0")
root.state("zoomed")
root.minsize(1000, 700)

icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print("Icon not found:", icon_path)

style = ttk.Style()
style.theme_use("clam")

# ----------------------------
# VARIABLES
# ----------------------------
mods_data = []
mod_icons = {}
versions_data = []
selected_project_id = None


# FUNCTIONS
def log(text):
    console.configure(state="normal")
    console.insert(tk.END, str(text) + "\n")
    console.see(tk.END)
    console.configure(state="disabled")


def load_mod_icon(url):
    try:
        response = requests.get(url, timeout=10)
        image = Image.open(BytesIO(response.content))
        image = image.resize((48, 48))
        return ImageTk.PhotoImage(image)
    except:
        return None


def get_current_project_type():
    project_type = content_type_var.get()

    if project_type == "mod":
        mods_label.config(text="Mods")
        install_button.config(text="Download & Install Mod")

    elif project_type == "resourcepack":
        mods_label.config(text="Resource Packs")
        install_button.config(text="Download & Install Resource Pack")

    else:
        mods_label.config(text="Shaderpacks")
        install_button.config(text="Download & Install Shaderpack")

    return project_type



    current_tab = notebook.tab(notebook.select(), "text")

    if current_tab == "Mods":
        return "mod"
    elif current_tab == "Resource Packs":
        return "resourcepack"
    return "shader"


def search_mods():
    global mods_data

    query = search_var.get().strip()
    if not query:
        messagebox.showwarning("Warning", "Enter a mod name.")
        return

    for widget in mods_inner_frame.winfo_children():
        widget.destroy()
    mods_listbox.delete(0, tk.END)
    versions_listbox.delete(0, tk.END)

    try:
        log(f"Searching for: {query}")

        response = requests.get(
            f"{MODRINTH_API}/search",
            params={
                "query": query,
                "limit": 25,
                "facets": f'[["project_type:{get_current_project_type()}\"]]'
            }
        )

        data = response.json()
        mods_data = data.get("hits", [])

        if not mods_data:
            log("No mods found.")
            return

        for i, mod in enumerate(mods_data):
            title = mod.get("title", "Unknown")
            downloads = mod.get("downloads", 0)
            icon_url = mod.get("icon_url")

            icon = None
            if icon_url:
                icon = load_mod_icon(icon_url)

            card = tk.Frame(
                mods_inner_frame,
                bg="#2a2a2a",
                highlightbackground="#3a3a3a",
                highlightthickness=1
            )

            if icon:
                icon_label = tk.Label(card, image=icon, bg="#2a2a2a")
                icon_label.image = icon
                icon_label.pack(side="left", padx=8, pady=8)

            info = tk.Frame(card, bg="#2a2a2a")
            info.pack(side="left", fill="both", expand=True)

            title_label = tk.Label(
                info,
                text=title,
                font=("Minecraft", 12, "bold"),
                bg="#2a2a2a",
                fg="white",
                anchor="w"
            )
            title_label.pack(fill="x")

            download_label = tk.Label(
                info,
                text=f"Downloads: {downloads}",
                font=(APP_FONT, 9),
                bg="#2a2a2a",
                fg="#bbbbbb",
                anchor="w"
            )
            download_label.pack(fill="x")

            def select_mod(event, idx=i):
                mods_listbox.selection_clear(0, tk.END)
                mods_listbox.selection_set(idx)
                load_versions()

            card.bind("<Button-1>", select_mod)
            title_label.bind("<Button-1>", select_mod)
            download_label.bind("<Button-1>", select_mod)

            card.pack(fill="x", padx=5, pady=4)

            mods_listbox.insert(tk.END, title)

        log(f"Found {len(mods_data)} mods.")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        log(f"Error: {e}")


def load_versions(event=None):
    global versions_data
    global selected_project_id

    selected = mods_listbox.curselection()
    if not selected:
        return

    index = selected[0]
    mod = mods_data[index]

    selected_project_id = mod["project_id"]

    versions_listbox.delete(0, tk.END)

    minecraft_version = version_var.get().strip()

    try:
        log(f"Loading versions for {mod['title']}...")

        response = requests.get(
            f"{MODRINTH_API}/project/{selected_project_id}/version"
        )

        versions_data = response.json()

        filtered_versions = []

        for version in versions_data:
            game_versions = version.get("game_versions", [])

            if minecraft_version:
                if minecraft_version in game_versions:
                    filtered_versions.append(version)
            else:
                filtered_versions.append(version)

        versions_data = filtered_versions

        if not versions_data:
            log("No compatible versions found.")
            return

        for version in versions_data:
            version_name = version.get("name", "Unnamed")
            loaders = ", ".join(version.get("loaders", []))
            game_versions = ", ".join(version.get("game_versions", []))

            versions_listbox.insert(
                tk.END,
                f"{version_name} | {loaders} | MC: {game_versions}"
            )

        log(f"Loaded {len(versions_data)} versions.")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        log(f"Error: {e}")


def download_mod():
    selected = versions_listbox.curselection()

    if not selected:
        messagebox.showwarning("Warning", "Select a mod version first.")
        return

    version = versions_data[selected[0]]

    files = version.get("files", [])

    if not files:
        messagebox.showerror("Error", "No downloadable file found.")
        return

    primary_file = None

    for file in files:
        if file.get("primary"):
            primary_file = file
            break

    if not primary_file:
        primary_file = files[0]

    download_url = primary_file["url"]
    filename = primary_file["filename"]

    try:
        os.makedirs(current_mods_folder, exist_ok=True)

        filepath = os.path.join(current_mods_folder, filename)

        log(f"Downloading {filename}...")

        response = requests.get(download_url, stream=True)

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        start_time = time.time()

        progress_bar["maximum"] = total_size

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    progress_bar["value"] = downloaded

                    elapsed = max(time.time() - start_time, 0.1)
                    speed = downloaded / elapsed / 1024

                    progress_label.config(
                        text=f"{downloaded // 1024} KB / {total_size // 1024} KB"
                    )

                    speed_label.config(
                        text=f"Speed: {speed:.1f} KB/s"
                    )

                    root.update_idletasks()

        log(f"Downloaded to: {filepath}")
        messagebox.showinfo("Success", f"Installed: {filename}")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        log(f"Error: {e}")


def change_mods_folder():
    global current_mods_folder

    selected_folder = filedialog.askdirectory(
        title="Select Minecraft Mods Folder"
    )

    if selected_folder:
        current_mods_folder = selected_folder
        folder_path_label.config(text=current_mods_folder)
        log(f"Mods folder changed to: {current_mods_folder}")


def open_mods_folder():
    os.makedirs(current_mods_folder, exist_ok=True)
    os.startfile(current_mods_folder)


# ----------------------------
# UI
# ----------------------------

search_frame = tk.Frame(root, bg="#1e1e1e")
search_frame.pack(fill="x", padx=10)

search_var = tk.StringVar()
version_var = tk.StringVar()

search_entry = tk.Entry(
    search_frame,
    textvariable=search_var,
    font=("Mojangles", 12),
    width=35,
    bg="#2b2b2b",
    fg="white",
    insertbackground="white"
)
search_entry.grid(row=1, column=0, padx=5, pady=20)

version_entry = tk.Entry(
    search_frame,
    textvariable=version_var,
    font=("Mojangles", 12),
    width=15,
    bg="#2b2b2b",
    fg="white",
    insertbackground="white"
)
version_entry.grid(row=1, column=1, padx=5)
version_entry.insert(0, "1.21.11")

search_button = tk.Button(
    search_frame,
    text="Search",
    command=search_mods,
    bg="#00aa55",
    fg="white",
    font=("Minecrafter", 16)
)
search_button.grid(row=1, column=2, padx=5)

search_after_id = None

search_entry.bind("<KeyRelease>")

folder_button = tk.Button(
    search_frame,
    text="Open Mods Folder",
    command=open_mods_folder,
    bg="#00aa55",
    fg="white",
    font=("Minecrafter", 16)
)
folder_button.grid(row=1, column=3, padx=5)

change_folder_button = tk.Button(
    search_frame,
    text="Change Folder",
    command=change_mods_folder,
    bg="#666666",
    fg="white",
    font=("Minecrafter", 16)
)
change_folder_button.grid(row=1, column=4, padx=5)

folder_path_label = tk.Label(
    root,
    text="  " + current_mods_folder,
    bg="#1e1e1e",
    fg="#00ff88",
    font=("Minecraft", 9),
    anchor="w"
)
folder_path_label.pack(fill="x", padx=10, pady=(0, 5))

# ----------------------------
# CONTENT TYPE SELECTOR
# ----------------------------
content_type_var = tk.StringVar(value="mod")

content_type_frame = tk.Frame(root, bg="#1e1e1e")
content_type_frame.pack(fill="x", padx=10, pady=(0, 8))

content_label = tk.Label(
    content_type_frame,
    text="Content Type:",
    bg="#1e1e1e",
    fg="white",
    font=(APP_FONT, 11)
)
content_label.pack(side="left", padx=(0, 10))

mods_radio = tk.Radiobutton(
    content_type_frame,
    text="Mods",
    variable=content_type_var,
    value="mod",
    bg="#1e1e1e",
    fg="#aff1d0",
    selectcolor="#aff1d0",
    activebackground="#1e1e1e",
    activeforeground="white",
    font=(APP_FONT, 10)
)
mods_radio.pack(side="left", padx=5)

resourcepacks_radio = tk.Radiobutton(
    content_type_frame,
    text="Resource Packs",
    variable=content_type_var,
    value="resourcepack",
    bg="#1e1e1e",
    fg="#aff1d0",
    selectcolor="#aff1d0",
    activebackground="#1e1e1e",
    activeforeground="white",
    font=(APP_FONT, 10)
)
resourcepacks_radio.pack(side="left", padx=5)

shaderpacks_radio = tk.Radiobutton(
    content_type_frame,
    text="Shaderpacks",
    variable=content_type_var,
    value="shader",
    bg="#1e1e1e",
    fg="#aff1d0",
    selectcolor="#aff1d0",
    activebackground="#1e1e1e",
    activeforeground="white",
    font=(APP_FONT, 10)
)
shaderpacks_radio.pack(side="left", padx=5)

lists_frame = tk.Frame(root, bg="#1e1e1e")
lists_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Mods list
mods_frame = tk.Frame(lists_frame, bg="#1e1e1e")
mods_frame.pack(side="left", fill="both", expand=True, padx=5)

mods_label = tk.Label(
    mods_frame,
    text="Mods",
    bg="#1e1e1e",
    fg="white",
    font=("Minecraft", 14, "bold")
)
mods_label.pack(fill="x", pady=5)

mods_listbox = tk.Listbox(mods_frame)
mods_listbox.pack_forget()

mods_container = tk.Frame(mods_frame, bg="#1e1e1e")
mods_container.pack(fill="both", expand=True)

mods_scrollbar = tk.Scrollbar(mods_container)
mods_scrollbar.pack(side="right", fill="y")

mods_canvas = tk.Canvas(
    mods_container,
    bg="#1f1f1f",
    highlightthickness=0,
    yscrollcommand=mods_scrollbar.set
)
mods_canvas.pack(side="left", fill="both", expand=True)

mods_scrollbar.config(command=mods_canvas.yview)

mods_inner_frame = tk.Frame(mods_canvas, bg="#1f1f1f")

mods_canvas.create_window(
    (0, 0),
    window=mods_inner_frame,
    anchor="nw"
)

mods_inner_frame.bind(
    "<Configure>",
    lambda e: mods_canvas.configure(scrollregion=mods_canvas.bbox("all"))
)


def _on_mousewheel(event):
    mods_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

mods_canvas.bind_all("<MouseWheel>", _on_mousewheel)

mods_listbox.bind("<<ListboxSelect>>", load_versions)

# Versions list
versions_frame = tk.Frame(lists_frame, bg="#1e1e1e")
versions_frame.pack(side="right", fill="both", expand=True, padx=5)

versions_label = tk.Label(
    versions_frame,
    text="Versions",
    bg="#1e1e1e",
    fg="white",
    font=("Minecraft", 14, "bold")
)
versions_label.pack()

versions_listbox = tk.Listbox(
    versions_frame,
    bg="#2b2b2b",
    fg="white",
    font=("Minecraft", 10),
    selectbackground="#4444aa"
)
versions_listbox.pack(fill="both", expand=True)

# Download button
install_button = tk.Button(
    root,
    text="Download & Install Mod",
    command=download_mod,
    bg="#cc5500",
    fg="white",
    font=("Minecrafter", 14, "bold"),
    height=2
)
install_button.pack(fill="x", padx=10, pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate")
progress_bar.pack(fill="x", padx=10)

progress_label = tk.Label(
    root,
    text="Waiting for download...",
    bg="#1e1e1e",
    fg="white",
    font=(APP_FONT, 10)
)
progress_label.pack(pady=2)

speed_label = tk.Label(
    root,
    text="Speed: 0 KB/s",
    bg="#1e1e1e",
    fg="#00ff88",
    font=(APP_FONT, 10)
)
speed_label.pack()

# Console
console = ScrolledText(
    root,
    height=8,
    bg="#101010",
    fg="#00ff88",
    font=("Minecraft", 10)
)
console.pack(fill="both", padx=10, pady=10)
console.configure(state="disabled")

log("Minecraft mods folder:")
log(current_mods_folder)
log("Ready.")

root.mainloop()
