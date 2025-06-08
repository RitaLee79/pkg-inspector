import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import tempfile
import subprocess
import shutil
import threading
import mimetypes

class PKGInspector:
    def __init__(self, root):
        self.root = root
        self.root.title("PKG Inspector")
        self.root.geometry("1200x800")
        self.temp_dir = None
        self.payload_dir = None
        self.current_pkg = None
        self.tree_items = {}
        
        # Create menu
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open PKG", command=self.open_pkg)
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        root.config(menu=menubar)
        
        # Create panes
        main_pane = ttk.PanedWindow(root, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File tree frame
        file_frame = ttk.LabelFrame(main_pane, text="Files to be Installed")
        file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbars
        tree_container = ttk.Frame(file_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_container, columns=("location"), show="tree")
        self.tree.heading("#0", text="File/Folder")
        self.tree.heading("location", text="Installation Location")
        self.tree.column("location", width=500, stretch=tk.YES)
        
        # Configure tags for coloring
        self.tree.tag_configure('directory', foreground="#afafaf")
        self.tree.tag_configure('file', foreground='')
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Scripts frame
        script_frame = ttk.LabelFrame(main_pane, text="Installation Scripts")
        script_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.script_list = tk.Listbox(script_frame, height=5)
        script_scroll = ttk.Scrollbar(script_frame, orient="vertical", command=self.script_list.yview)
        self.script_list.configure(yscrollcommand=script_scroll.set)
        
        self.script_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        script_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add to panes
        main_pane.add(file_frame, weight=3)
        main_pane.add(script_frame, weight=1)
        
        # Create context menus
        self.file_menu = tk.Menu(root, tearoff=0)
        self.file_menu.add_command(label="Copy Path", command=self.copy_file_path)
        self.file_menu.add_command(label="Copy File to Clipboard", command=self.copy_file_content)
        self.file_menu.add_command(label="Show in Finder", command=self.show_in_finder)
        
        self.script_menu = tk.Menu(root, tearoff=0)
        self.script_menu.add_command(label="Open in Editor", command=self.open_script)
        
        # Bind events
        self.tree.bind("<Button-2>", self.show_file_menu)  # Right-click on macOS
        self.tree.bind("<Button-3>", self.show_file_menu)   # Right-click on Windows/Linux
        self.tree.bind("<Control-Button-1>", self.show_file_menu)  # Ctrl+click for macOS
        self.script_list.bind("<Button-2>", self.show_script_menu)
        self.script_list.bind("<Button-3>", self.show_script_menu)
        self.script_list.bind("<Control-Button-1>", self.show_script_menu)
        self.script_list.bind("<Double-1>", lambda e: self.open_script())
        
        # Status bar
        self.status = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, mode='determinate')
    
    def open_pkg(self):
        file_path = filedialog.askopenfilename(
            title="Select PKG File",
            filetypes=[("PKG files", "*.pkg"), ("All files", "*.*")]
        )
        if not file_path:
            return
            
        self.status.config(text=f"Processing: {os.path.basename(file_path)}...")
        self.progress.pack(fill=tk.X, pady=(0, 5))
        self.root.update()
        
        # Clear previous content
        self.tree.delete(*self.tree.get_children())
        self.script_list.delete(0, tk.END)
        self.tree_items = {}
        
        # Cleanup previous temp files
        self.cleanup_temp()
        
        # Run in thread to keep UI responsive
        threading.Thread(target=self.process_pkg, args=(file_path,), daemon=True).start()
    
    def process_pkg(self, file_path):
        try:
            # Create temp directory
            self.temp_dir = tempfile.mkdtemp(prefix="pkg_inspect_")
            self.current_pkg = file_path
            
            # Expand package
            self.expand_pkg(file_path)
            
            # Process package contents
            self.process_pkg_contents()
            
            self.status.config(text=f"Loaded: {os.path.basename(file_path)}")
            self.progress.pack_forget()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process package:\n{str(e)}")
            self.status.config(text="Error processing package")
            self.progress.pack_forget()
    
    def expand_pkg(self, pkg_path):
        # Create expand directory path
        expand_dir = os.path.join(self.temp_dir, "expanded")
        
        # Remove existing directory if it exists
        if os.path.exists(expand_dir):
            shutil.rmtree(expand_dir)
        
        # Run pkgutil to expand
        result = subprocess.run(
            ["pkgutil", "--expand", pkg_path, expand_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"pkgutil failed: {result.stderr}")
        
        # Find main payload
        for item in os.listdir(expand_dir):
            if item.endswith(".pkg"):
                pkg_dir = os.path.join(expand_dir, item)
                payload_path = os.path.join(pkg_dir, "Payload")
                
                if os.path.exists(payload_path):
                    # Extract payload
                    self.payload_dir = os.path.join(self.temp_dir, "payload")
                    
                    # Remove existing payload directory if it exists
                    if os.path.exists(self.payload_dir):
                        shutil.rmtree(self.payload_dir)
                    
                    os.makedirs(self.payload_dir, exist_ok=True)
                    
                    # Extract with cpio
                    with open(payload_path, 'rb') as f:
                        subprocess.run(
                            ["cpio", "-i", "-d"],
                            stdin=f,
                            cwd=self.payload_dir,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    return
        
        raise Exception("No valid payload found in package")
    
    def process_pkg_contents(self):
        # Process files
        self.process_files()
        
        # Process scripts
        self.process_scripts()
    
    def process_files(self):
        # Create root node with directory tag
        root_iid = self.tree.insert("", "end", text="/", values=("/",), open=True, tags=('directory',))
        self.tree_items["/"] = root_iid
        
        # Walk through extracted payload
        for root_path, dirs, files in os.walk(self.payload_dir):
            # Get relative path from payload root
            rel_path = os.path.relpath(root_path, self.payload_dir)
            if rel_path == ".":
                rel_path = ""
                
            # Get installation path
            install_path = "/" + rel_path
            
            # Create parent node if it doesn't exist
            parent_iid = self.tree_items.get(install_path, None)
            if not parent_iid and install_path != "/":
                # Create parent nodes recursively
                parts = install_path.strip("/").split("/")
                current_path = ""
                parent_iid = self.tree_items["/"]
                
                for part in parts:
                    current_path = current_path + "/" + part if current_path else "/" + part
                    if current_path not in self.tree_items:
                        parent_iid = self.tree.insert(
                            parent_iid, "end", 
                            text=part, 
                            values=(current_path,),
                            tags=('directory',)  # Directory tag
                        )
                        self.tree_items[current_path] = parent_iid
                    else:
                        parent_iid = self.tree_items[current_path]
        
            # Add directories with directory tag
            for dir_name in dirs:
                dir_path = os.path.join(install_path, dir_name)
                dir_iid = self.tree.insert(
                    parent_iid, "end", 
                    text=dir_name, 
                    values=(dir_path,),
                    tags=('directory',)  # Directory tag
                )
                self.tree_items[dir_path] = dir_iid
            
            # Add files with file tag
            for file_name in files:
                file_path = os.path.join(install_path, file_name)
                file_iid = self.tree.insert(
                    parent_iid, "end", 
                    text=file_name, 
                    values=(install_path,),
                    tags=("file",)  # File tag
                )
                self.tree_items[file_path] = file_iid
                
            self.root.update()
    
    def process_scripts(self):
        # Find scripts directory
        expanded_dir = os.path.join(self.temp_dir, "expanded")
        for item in os.listdir(expanded_dir):
            if item.endswith(".pkg"):
                pkg_dir = os.path.join(expanded_dir, item)
                scripts_dir = os.path.join(pkg_dir, "Scripts")
                
                if os.path.exists(scripts_dir):
                    # List all scripts
                    for script in os.listdir(scripts_dir):
                        if not script.startswith("."):  # Skip hidden files
                            self.script_list.insert(tk.END, script)
    
    def show_file_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.file_menu.post(event.x_root, event.y_root)
    
    def show_script_menu(self, event):
        index = self.script_list.nearest(event.y)
        if index >= 0:
            self.script_list.selection_clear(0, tk.END)
            self.script_list.selection_set(index)
            self.script_menu.post(event.x_root, event.y_root)
    
    def copy_file_path(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            file_name = self.tree.item(item, "text")
            location = self.tree.item(item, "values")[0]
            
            # Handle directories vs files
            if "file" in self.tree.item(item, "tags"):
                full_path = os.path.join(location, file_name)
            else:
                full_path = location
                
            self.root.clipboard_clear()
            self.root.clipboard_append(full_path)
            self.status.config(text=f"Copied: {full_path}")
    
    def copy_file_content(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        file_name = self.tree.item(item, "text")
        location = self.tree.item(item, "values")[0]
        
        # Only allow for files, not directories
        if "file" not in self.tree.item(item, "tags"):
            messagebox.showinfo("Info", "Please select a file, not a directory")
            return
            
        rel_path = os.path.join(location, file_name).lstrip("/")
        extracted_path = os.path.join(self.payload_dir, rel_path)
        
        if not os.path.exists(extracted_path):
            messagebox.showwarning("Not Found", "File not found in extracted payload")
            return
        
        # Check if it's a text file
        mime_type, _ = mimetypes.guess_type(extracted_path)
        if not mime_type or not mime_type.startswith('text/'):
            if not messagebox.askyesno("Confirm", 
                    "This doesn't appear to be a text file. Copy anyway?"):
                return
        
        try:
            with open(extracted_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
                self.status.config(text=f"Copied content of {file_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {str(e)}")
    
    def show_in_finder(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            file_name = self.tree.item(item, "text")
            location = self.tree.item(item, "values")[0]
            
            # Handle directories vs files
            if "file" in self.tree.item(item, "tags"):
                rel_path = os.path.join(location, file_name).lstrip("/")
            else:
                rel_path = location.lstrip("/")
                
            extracted_path = os.path.join(self.payload_dir, rel_path)
            
            if os.path.exists(extracted_path):
                subprocess.run(["open", "-R", extracted_path])
                self.status.config(text=f"Revealed in Finder: {file_name or os.path.basename(location)}")
            else:
                messagebox.showwarning("Not Found", "File not found in extracted payload")
    
    def open_script(self):
        selected = self.script_list.curselection()
        if selected:
            script_name = self.script_list.get(selected[0])
            
            # Find script path
            expanded_dir = os.path.join(self.temp_dir, "expanded")
            for item in os.listdir(expanded_dir):
                if item.endswith(".pkg"):
                    pkg_dir = os.path.join(expanded_dir, item)
                    scripts_dir = os.path.join(pkg_dir, "Scripts")
                    script_path = os.path.join(scripts_dir, script_name)
                    
                    if os.path.exists(script_path):
                        subprocess.run(["open", "-t", script_path])
                        self.status.config(text=f"Opened: {script_name}")
                        return
            
            messagebox.showwarning("Not Found", "Script file not found")
    
    def cleanup_temp(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Error cleaning temp: {e}")
    
    def on_closing(self):
        self.cleanup_temp()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PKGInspector(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()