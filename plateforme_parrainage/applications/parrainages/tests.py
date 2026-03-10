import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class ProfessionalDatabaseBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite Explorer Pro")
        self.root.geometry("1000x600")
        
        self.db_path = None
        
        # Style pour un look moderne
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=25)

        self._build_ui()

    def _build_ui(self):
        # --- Barre de contrôle supérieure ---
        top_panel = ttk.Frame(self.root, padding="10")
        top_panel.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top_panel, text="📁 Charger Base de Données", command=self.open_db).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(top_panel, text="Table :").pack(side=tk.LEFT, padx=(20, 5))
        self.table_selector = ttk.Combobox(top_panel, state="readonly", width=30)
        self.table_selector.pack(side=tk.LEFT, padx=5)
        self.table_selector.bind("<<ComboboxSelected>>", self.display_table_content)

        # --- Zone d'affichage centrale ---
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Création du Treeview avec barres de défilement
        self.tree = ttk.Treeview(self.main_frame, show="headings")
        
        vsb = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

    def open_db(self):
        """Ouvre le sélecteur de fichier et liste les tables."""
        path = filedialog.askopenfilename(filetypes=[("SQLite Files", "*.db *.sqlite *.sqlite3")])
        if path:
            self.db_path = path
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                # Récupère la liste de TOUTES les tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [t[0] for t in cursor.fetchall()]
                conn.close()

                if tables:
                    self.table_selector['values'] = tables
                    self.table_selector.current(0)
                    self.display_table_content()
                else:
                    messagebox.showwarning("Info", "Cette base de données est vide.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la lecture : {e}")

    def display_table_content(self, event=None):
        """Récupère et affiche les données de la table sélectionnée."""
        if not self.db_path:
            return

        table_name = self.table_selector.get()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Récupérer les données
            cursor.execute(f"SELECT * FROM `{table_name}`")
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            conn.close()

            # Mise à jour du Treeview
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columns

            for col in columns:
                self.tree.heading(col, text=col, anchor=tk.CENTER)
                self.tree.column(col, width=150, anchor=tk.W)

            for row in data:
                self.tree.insert("", tk.END, values=row)

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger la table : {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalDatabaseBrowser(root)
    root.mainloop()