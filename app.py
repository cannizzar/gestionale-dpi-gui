import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
import os

DB_NAME = "gestione_dpi.db"

class DPIManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestionale Magazzino DPI - Sicurezza Lavoro")
        self.root.geometry("1050x680")
        self.root.minsize(950, 600)

        # Inizializzazione Database
        self.init_db()

        # Configurazione Stile TTK
        self.setup_styles()

        # Creazione Struttura a Schede (Notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Inizializzazione delle Schede
        self.tab_inventario = ttk.Frame(self.notebook)
        self.tab_consegna = ttk.Frame(self.notebook)
        self.tab_rientri = ttk.Frame(self.notebook)
        self.tab_storico = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_inventario, text=" 📦 Inventario DPI ")
        self.notebook.add(self.tab_consegna, text=" 📋 Nuova Consegna ")
        self.notebook.add(self.tab_rientri, text=" 🔄 Rientri e Dismissioni ")
        self.notebook.add(self.tab_storico, text=" 📜 Storico Movimenti ")

        # Costruzione componenti per ciascuna scheda
        self.build_tab_inventario()
        self.build_tab_consegna()
        self.build_tab_rientri()
        self.build_tab_storico()

        # Caricamento iniziale dei dati
        self.refresh_all()

    # --- DATABASE ---
    def get_connection(self):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dpi_articoli (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    quantita INTEGER NOT NULL DEFAULT 0,
                    soglia_minima INTEGER NOT NULL DEFAULT 5,
                    scadenza DATE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consegne (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dpi_id INTEGER NOT NULL,
                    lavoratore TEXT NOT NULL,
                    quantita INTEGER NOT NULL,
                    data_consegna DATETIME DEFAULT CURRENT_TIMESTAMP,
                    stato TEXT NOT NULL DEFAULT 'IN USO',
                    data_rientro DATETIME,
                    FOREIGN KEY (dpi_id) REFERENCES dpi_articoli (id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    # --- STILI GRAFICI ---
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Color Palette
        style.configure(".", font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e1e8ed", foreground="#1e293b")
        style.configure("Treeview", rowheight=28)
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#0f172a")

    # --- SCHEDA 1: INVENTARIO ---
    def build_tab_inventario(self):
        # Frame Superiore: Form e Ricerca
        top_frame = ttk.LabelFrame(self.tab_inventario, text=" Gestione Articolo / Aggiunta ", padding=15)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Griglia Inserimento
        ttk.Label(top_frame, text="Nome DPI:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_nome = ttk.Entry(top_frame, width=22)
        self.ent_nome.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top_frame, text="Categoria:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.ent_cat = ttk.Entry(top_frame, width=18)
        self.ent_cat.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(top_frame, text="Quantità:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.ent_qta = ttk.Spinbox(top_frame, from_=1, to=10000, width=8)
        self.ent_qta.grid(row=0, column=5, padx=5, pady=5)
        self.ent_qta.set(10)

        ttk.Label(top_frame, text="Soglia Min.:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_soglia = ttk.Spinbox(top_frame, from_=1, to=1000, width=8)
        self.ent_soglia.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.ent_soglia.set(5)

        ttk.Label(top_frame, text="Scadenza (AAAA-MM-GG):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.ent_scad = ttk.Entry(top_frame, width=18)
        self.ent_scad.grid(row=1, column=3, padx=5, pady=5)

        btn_salva = ttk.Button(top_frame, text="➕ Aggiungi / Ricarica", command=self.salva_dpi)
        btn_salva.grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky=tk.EW)

        # Tabella Inventario
        table_frame = ttk.Frame(self.tab_inventario, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Nome", "Categoria", "Giacenza", "Soglia Min.", "Scadenza", "Stato")
        self.tree_inv = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree_inv.heading("ID", text="ID")
        self.tree_inv.heading("Nome", text="Nome Articolo")
        self.tree_inv.heading("Categoria", text="Categoria")
        self.tree_inv.heading("Giacenza", text="Giacenza")
        self.tree_inv.heading("Soglia Min.", text="Soglia Min.")
        self.tree_inv.heading("Scadenza", text="Scadenza")
        self.tree_inv.heading("Stato", text="Stato Scorta / Scadenza")

        self.tree_inv.column("ID", width=50, anchor=tk.CENTER)
        self.tree_inv.column("Nome", width=220)
        self.tree_inv.column("Categoria", width=140)
        self.tree_inv.column("Giacenza", width=90, anchor=tk.CENTER)
        self.tree_inv.column("Soglia Min.", width=90, anchor=tk.CENTER)
        self.tree_inv.column("Scadenza", width=120, anchor=tk.CENTER)
        self.tree_inv.column("Stato", width=200)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_inv.yview)
        self.tree_inv.configure(yscroll=scrollbar.set)

        self.tree_inv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag per formattazione righe
        self.tree_inv.tag_configure("alert_all", background="#fee2e2", foreground="#991b1b")
        self.tree_inv.tag_configure("alert_qta", background="#ffedd5", foreground="#9a3412")
        self.tree_inv.tag_configure("alert_scad", background="#fef3c7", foreground="#92400e")
        self.tree_inv.tag_configure("ok", background="#f0fdf4", foreground="#166534")

    def salva_dpi(self):
        nome = self.ent_nome.get().strip()
        categoria = self.ent_cat.get().strip()
        scadenza = self.ent_scad.get().strip() or None

        try:
            qta = int(self.ent_qta.get())
            soglia = int(self.ent_soglia.get())
        except ValueError:
            messagebox.showerror("Errore Input", "Quantità e Soglia devono essere numeri interi.")
            return

        if not nome or not categoria:
            messagebox.showerror("Errore Input", "Inserire sia il Nome che la Categoria del DPI.")
            return

        if scadenza:
            try:
                datetime.strptime(scadenza, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Errore Data", "Formato data non valido. Usa AAAA-MM-GG.")
                return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, quantita FROM dpi_articoli WHERE LOWER(nome) = LOWER(?)", (nome,))
            row = cursor.fetchone()

            if row:
                dpi_id, qta_attuale = row
                nuova_qta = qta_attuale + qta
                cursor.execute("UPDATE dpi_articoli SET quantita = ?, soglia_minima = ? WHERE id = ?", (nuova_qta, soglia, dpi_id))
                messagebox.showinfo("Aggiornamento", f"Giacenza aggiornata per '{nome}'. Nuova disponibilità: {nuova_qta}")
            else:
                cursor.execute("""
                    INSERT INTO dpi_articoli (nome, categoria, quantita, soglia_minima, scadenza)
                    VALUES (?, ?, ?, ?, ?)
                """, (nome, categoria, qta, soglia, scadenza))
                messagebox.showinfo("Successo", f"Nuovo articolo '{nome}' inserito nell'inventario.")

            conn.commit()

        # Pulizia campi
        self.ent_nome.delete(0, tk.END)
        self.ent_cat.delete(0, tk.END)
        self.ent_scad.delete(0, tk.END)
        self.refresh_all()

    def load_inventario(self):
        for item in self.tree_inv.get_children():
            self.tree_inv.delete(item)

        oggi = datetime.now().date()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, categoria, quantita, soglia_minima, scadenza FROM dpi_articoli")
            rows = cursor.fetchall()

            for row in rows:
                art_id, nome, cat, qta, soglia, scad = row
                stato = "OK - Regolare"
                tag = "ok"

                is_scorta_bassa = qta <= soglia
                is_scaduto = False
                is_in_scadenza = False

                if scad:
                    data_s = datetime.strptime(scad, "%Y-%m-%d").date()
                    if data_s < oggi:
                        is_scaduto = True
                    elif (data_s - oggi).days <= 30:
                        is_in_scadenza = True

                if is_scorta_bassa and is_scaduto:
                    stato = "⚠️ Scorta Bassa & SCADUTO"
                    tag = "alert_all"
                elif is_scaduto:
                    stato = "⛔ SCADUTO"
                    tag = "alert_all"
                elif is_scorta_bassa:
                    stato = "⚠️ Scorta Bassa"
                    tag = "alert_qta"
                elif is_in_scadenza:
                    stato = "⏳ In Scadenza (<30gg)"
                    tag = "alert_scad"

                self.tree_inv.insert("", tk.END, values=(art_id, nome, cat, qta, soglia, scad or "N/A", stato), tags=(tag,))

    # --- SCHEDA 2: NUOVA CONSEGNA ---
    def build_tab_consegna(self):
        frame = ttk.LabelFrame(self.tab_consegna, text=" Registra Consegna DPI a Lavoratore ", padding=25)
        frame.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        ttk.Label(frame, text="Seleziona DPI:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        self.combo_dpi = ttk.Combobox(frame, width=35, state="readonly")
        self.combo_dpi.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(frame, text="Nome e Cognome Lavoratore:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        self.ent_lavoratore = ttk.Entry(frame, width=38)
        self.ent_lavoratore.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(frame, text="Quantità da Consegnare:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        self.spn_qta_consegna = ttk.Spinbox(frame, from_=1, to=100, width=10)
        self.spn_qta_consegna.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        self.spn_qta_consegna.set(1)

        btn_consegna = ttk.Button(frame, text="✔ Registra Consegna", command=self.registra_consegna)
        btn_consegna.grid(row=3, column=0, columnspan=2, pady=20, sticky=tk.EW)

    def registra_consegna(self):
        selezionato = self.combo_dpi.get()
        lavoratore = self.ent_lavoratore.get().strip()

        if not selezionato or not lavoratore:
            messagebox.showerror("Errore", "Selezionare un DPI e specificare il nome del lavoratore.")
            return

        try:
            qta = int(self.spn_qta_consegna.get())
        except ValueError:
            messagebox.showerror("Errore", "Inserire una quantità valida.")
            return

        dpi_id = int(selezionato.split(" - ")[0])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantita, nome FROM dpi_articoli WHERE id = ?", (dpi_id,))
            row = cursor.fetchone()

            if not row:
                messagebox.showerror("Errore", "DPI selezionato non trovato.")
                return

            disp, nome_dpi = row
            if qta > disp:
                messagebox.showerror("Giacenza Insufficiente", f"Disponibilità insufficiente a magazzino ({disp} pezzi disponibili).")
                return

            cursor.execute("UPDATE dpi_articoli SET quantita = quantita - ? WHERE id = ?", (qta, dpi_id))
            cursor.execute("INSERT INTO consegne (dpi_id, lavoratore, quantita, stato) VALUES (?, ?, ?, 'IN USO')",
                           (dpi_id, lavoratore, qta))
            conn.commit()

        messagebox.showinfo("Successo", f"Consegna di {qta}x '{nome_dpi}' registrata per {lavoratore}.")
        self.ent_lavoratore.delete(0, tk.END)
        self.refresh_all()

    # --- SCHEDA 3: RIENTRI E DISMISSIONI ---
    def build_tab_rientri(self):
        table_frame = ttk.Frame(self.tab_rientri, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(table_frame, text="DPI Attualmente 'IN USO' presso i Lavoratori:", style="Header.TLabel").pack(anchor=tk.W, pady=5)

        cols = ("ID Cons.", "DPI", "Lavoratore", "Q.tà", "Data Consegna")
        self.tree_rientri = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        for col in cols:
            self.tree_rientri.heading(col, text=col)
            self.tree_rientri.column(col, anchor=tk.CENTER)

        self.tree_rientri.column("DPI", width=220, anchor=tk.W)
        self.tree_rientri.column("Lavoratore", width=220, anchor=tk.W)

        self.tree_rientri.pack(fill=tk.BOTH, expand=True, pady=10)

        # Bottom Frame per bottoni azione
        btn_frame = ttk.Frame(self.tab_rientri, padding=10)
        btn_frame.pack(fill=tk.X)

        btn_rientro = ttk.Button(btn_frame, text="↩ Restituisci al Magazzino", command=lambda: self.gestisci_rientro("RESTITUITO"))
        btn_rientro.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        btn_dismetti = ttk.Button(btn_frame, text="🗑 Dismetti (Danneggiato / Usurato)", command=lambda: self.gestisci_rientro("DISMESSO"))
        btn_dismetti.pack(side=tk.RIGHT, padx=10, expand=True, fill=tk.X)

    def load_rientri(self):
        for item in self.tree_rientri.get_children():
            self.tree_rientri.delete(item)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, a.nome, c.lavoratore, c.quantita, c.data_consegna
                FROM consegne c
                JOIN dpi_articoli a ON c.dpi_id = a.id
                WHERE c.stato = 'IN USO'
                ORDER BY c.data_consegna DESC
            """)
            for row in cursor.fetchall():
                self.tree_rientri.insert("", tk.END, values=row)

    def gestisci_rientro(self, nuovo_stato):
        selected = self.tree_rientri.selection()
        if not selected:
            messagebox.showwarning("Selezione Mancante", "Selezionare una consegna dalla lista prima di proseguire.")
            return

        values = self.tree_rientri.item(selected[0], "values")
        consegna_id = values[0]
        nome_dpi = values[1]
        lavoratore = values[2]
        qta = int(values[3])

        msg = f"Confermi la restituzione di {qta}x '{nome_dpi}' da parte di {lavoratore}?" if nuovo_stato == "RESTITUITO" \
            else f"Confermi la DISMISSIONE di {qta}x '{nome_dpi}' (non tornerà a magazzino)?"

        if not messagebox.askyesno("Conferma Operazione", msg):
            return

        ora_attuale = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dpi_id FROM consegne WHERE id = ?", (consegna_id,))
            dpi_id = cursor.fetchone()[0]

            if nuovo_stato == "RESTITUITO":
                cursor.execute("UPDATE dpi_articoli SET quantita = quantita + ? WHERE id = ?", (qta, dpi_id))

            cursor.execute("UPDATE consegne SET stato = ?, data_rientro = ? WHERE id = ?", (nuovo_stato, ora_attuale, consegna_id))
            conn.commit()

        messagebox.showinfo("Operazione Completata", f"Stato aggiornato a '{nuovo_stato}'.")
        self.refresh_all()

    # --- SCHEDA 4: STORICO E ESPORTAZIONE CSV ---
    def build_tab_storico(self):
        table_frame = ttk.Frame(self.tab_storico, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "DPI", "Lavoratore", "Q.tà", "Stato", "Data Consegna", "Data Rientro/Dism.")
        self.tree_storico = ttk.Treeview(table_frame, columns=cols, show="headings")

        for col in cols:
            self.tree_storico.heading(col, text=col)
            self.tree_storico.column(col, anchor=tk.CENTER)

        self.tree_storico.column("DPI", width=180, anchor=tk.W)
        self.tree_storico.column("Lavoratore", width=180, anchor=tk.W)

        self.tree_storico.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_frame = ttk.Frame(self.tab_storico, padding=10)
        btn_frame.pack(fill=tk.X)

        btn_export = ttk.Button(btn_frame, text="📁 Esporta Storico in CSV / Excel", command=self.esporta_csv)
        btn_export.pack(side=tk.RIGHT, padx=10)

    def load_storico(self):
        for item in self.tree_storico.get_children():
            self.tree_storico.delete(item)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, a.nome, c.lavoratore, c.quantita, c.stato, c.data_consegna, COALESCE(c.data_rientro, '-')
                FROM consegne c
                JOIN dpi_articoli a ON c.dpi_id = a.id
                ORDER BY c.data_consegna DESC
            """)
            for row in cursor.fetchall():
                self.tree_storico.insert("", tk.END, values=row)

    def esporta_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Salva Storico Consegne"
        )
        if not filepath:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, a.nome, c.lavoratore, c.quantita, c.stato, c.data_consegna, COALESCE(c.data_rientro, '-')
                FROM consegne c
                JOIN dpi_articoli a ON c.dpi_id = a.id
                ORDER BY c.data_consegna DESC
            """)
            rows = cursor.fetchall()

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["ID Consegna", "Articolo DPI", "Lavoratore", "Quantità", "Stato", "Data Consegna", "Data Rientro/Dismissione"])
                writer.writerows(rows)
            messagebox.showinfo("Esportazione Completata", f"Dati esportati con successo in:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Errore Esportazione", f"Impossibile salvare il file: {e}")

    # --- AGGIORNAMENTO DATI GENERALI ---
    def refresh_all(self):
        self.load_inventario()
        self.load_rientri()
        self.load_storico()

        # Aggiorna menu a tendina DPI per la scheda consegne
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, quantita FROM dpi_articoli WHERE quantita > 0")
            items = [f"{row[0]} - {row[1]} (Disp: {row[2]})" for row in cursor.fetchall()]
            self.combo_dpi['values'] = items
            if items:
                self.combo_dpi.current(0)
            else:
                self.combo_dpi.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = DPIManagerGUI(root)
    root.mainloop()
