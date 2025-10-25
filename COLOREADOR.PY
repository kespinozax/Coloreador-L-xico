# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import re
import os

APP_TITLE = "🎨 Coloreador Léxico - C++"
DARK_BG = "#1e1e1e"
DARK_LINE = "#2a2a2a"

# ===== PALABRAS RESERVADAS =====
CPP_KEYWORDS = {
    "if", "else", "while", "for", "return", "int", "float", "double", "char", "bool",
    "true", "false", "void", "class", "public", "private", "protected", "include",
    "namespace", "using", "std", "cout", "cin", "endl", "switch", "case", "break",
    "continue", "struct", "const", "static", "virtual", "new", "delete", "try",
    "catch", "throw", "this"
}

# ===== COLORES =====
TOKEN_COLORS = {
    "KEYWORD": "#00BFFF",   # Azul
    "NUMBER": "#FFA500",    # Anaranjado
    "STRING": "#00FF7F",    # Verde
    "IDENT": "#FF69B4",     # Rosado
    "OP": "#FFFF00",        # Amarillo
    "GROUP": "#FFFFFF",     # Blanco
    "COMMENT": "#A9A9A9",   # Gris
    "ERROR": "#FFFFFF"      # Blanco sobre rojo
}

# ===== PATRONES =====
PATTERNS = [
    ("COMMENT", re.compile(r"//[^\n]*|/\*[\s\S]*?\*/")),
    ("STRING", re.compile(r"\".*?\"|\'.*?\'")),
    ("NUMBER", re.compile(r"\b\d+(\.\d+)?\b")),
    ("KEYWORD", re.compile(r"\b(" + "|".join(CPP_KEYWORDS) + r")\b")),
    ("IDENT", re.compile(r"\b[a-zA-Z_]\w*\b")),
    ("GROUP", re.compile(r"[\(\)\[\]\{\}]")),
    ("OP", re.compile(r"[+\-*/%=!<>&|^~;,.:]")),
    ("SPACE", re.compile(r"\s+")),
    ("UNKNOWN", re.compile(r"."))  # Cualquier otro carácter
]

# ===== FUNCIONES BASE =====
def compute_line_col(text, index):
    line = text.count("\n", 0, index) + 1
    last_nl = text.rfind("\n", 0, index)
    col = index - (last_nl + 1) + 1
    return line, col


def lex(text):
    """Analizador léxico con detección de errores fuera de contexto."""
    tokens = []
    i, n = 0, len(text)
    while i < n:
        for name, rx in PATTERNS:
            m = rx.match(text, i)
            if not m:
                continue
            s, e = m.span()
            val = text[s:e]

            if name == "SPACE":
                i = e
                break

            if name == "UNKNOWN":
                if not re.match(r"[a-zA-Z0-9_{}\[\]()\"';:,.<>+\-*/%=!&|^~#\s]", val):
                    line, col = compute_line_col(text, s)
                    return tokens, {"char": val, "start": s, "end": e, "line": line, "col": col}
                i = e
                break

            # Identificador fuera de contexto (después de ';' o '}')
            if name == "IDENT":
                prev = text[:s].rstrip()[-1:]
                if prev in [';', '}']:
                    line, col = compute_line_col(text, s)
                    return tokens, {"char": val, "start": s, "end": e, "line": line, "col": col}

            tokens.append({"type": name, "value": val, "start": s, "end": e})
            i = e
            break
        else:
            line, col = compute_line_col(text, i)
            return tokens, {"char": text[i], "start": i, "end": i+1, "line": line, "col": col}
    return tokens, None


# ===== INTERFAZ =====
class LexicalColorer:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1000x650")
        self.root.config(bg=DARK_BG)
        self.dark_mode = True

        # ---- BOTONES ----
        frame = tk.Frame(root, bg=DARK_BG)
        frame.pack(fill="x")

        tk.Button(frame, text="📂 Abrir Archivo", command=self.load_file,
                  bg="#007acc", fg="white", font=("Consolas", 11), relief="flat").pack(side="left", padx=5, pady=8)
        tk.Button(frame, text="🧩 Analizar", command=self.analyze,
                  bg="#28a745", fg="white", font=("Consolas", 11), relief="flat").pack(side="left", padx=5, pady=8)
        tk.Button(frame, text="📊 Resumen", command=self.show_summary,
                  bg="#ff9800", fg="white", font=("Consolas", 11), relief="flat").pack(side="left", padx=5, pady=8)
        tk.Button(frame, text="📝 Generar Reportes", command=self.generate_reports,
                  bg="#2196F3", fg="white", font=("Consolas", 11), relief="flat").pack(side="left", padx=5, pady=8)
        tk.Button(frame, text="🌗 Tema", command=self.toggle_theme,
                  bg="#6c63ff", fg="white", font=("Consolas", 11), relief="flat").pack(side="left", padx=5, pady=8)

        # ---- ÁREA DE TEXTO ----
        self.text = scrolledtext.ScrolledText(root, wrap=tk.WORD,
                                              font=("Consolas", 12),
                                              bg=DARK_BG, fg="white",
                                              insertbackground="white")
        self.text.pack(expand=True, fill="both")

        # ---- ESTADO ----
        self.status = tk.Label(root, text="Listo", anchor="w", bg=DARK_BG, fg="white", font=("Consolas", 10))
        self.status.pack(fill="x")

        self.configure_tags()
        self.text.bind("<KeyRelease>", self.highlight_realtime)
        self.highlight_current_line()

    # ===== COLORES =====
    def configure_tags(self):
        for tag, color in TOKEN_COLORS.items():
            if tag == "ERROR":
                self.text.tag_config(tag, foreground=color, background="red")
            else:
                self.text.tag_config(tag, foreground=color)
        self.text.tag_config("LINE", background=DARK_LINE)

    # ===== CARGA =====
    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos C++", "*.cpp *.h")])
        if not path:
            return
        encodings = ["utf-8", "latin-1", "windows-1252"]
        content = None
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except Exception:
                continue
        if content is None:
            messagebox.showerror("Error", "No se pudo abrir el archivo.")
            return
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.status.config(text=f"Archivo cargado: {os.path.basename(path)}")
        self.analyze()

    # ===== ANALIZAR =====
    def analyze(self):
        text = self.text.get("1.0", tk.END)
        for tag in TOKEN_COLORS:
            self.text.tag_remove(tag, "1.0", tk.END)
        tokens, error = lex(text)
        if error:
            self.mark_error(error)
            return
        for t in tokens:
            start, end, kind = f"1.0+{t['start']}c", f"1.0+{t['end']}c", t["type"]
            if kind in TOKEN_COLORS:
                self.text.tag_add(kind, start, end)
        self.status.config(text="Análisis completado correctamente ✅")

    # ===== ERROR =====
    def mark_error(self, error):
        start, end = f"1.0+{error['start']}c", f"1.0+{error['end']}c"
        self.text.tag_add("ERROR", start, end)
        self.text.see(start)
        msg = f"❌ Error léxico: '{error['char']}' en línea {error['line']}, columna {error['col']}"
        self.status.config(text=msg)
        messagebox.showerror("Error Léxico", msg)

    # ===== TIEMPO REAL =====
    def highlight_realtime(self, event=None):
        self.text.after_cancel(getattr(self, "_job", None))
        self._job = self.text.after(250, self.analyze)

    def highlight_current_line(self):
        self.text.tag_remove("LINE", "1.0", tk.END)
        self.text.tag_add("LINE", "insert linestart", "insert lineend+1c")
        self.text.after(100, self.highlight_current_line)

    # ===== RESUMEN =====
    def show_summary(self):
        text = self.text.get("1.0", tk.END)
        tokens, error = lex(text)
        counts = {t: 0 for t in TOKEN_COLORS.keys()}
        for t in tokens:
            if t["type"] in counts:
                counts[t["type"]] += 1
        if error:
            counts["ERROR"] += 1
        resumen = "\n".join(f"{k}: {v}" for k, v in counts.items())
        messagebox.showinfo("📊 Resumen de Tokens", resumen)

    # ===== REPORTES =====
    def generate_reports(self):
        """Genera los reportes heredados del Proyecto 1"""
        text = self.text.get("1.0", tk.END)
        tokens, error = lex(text)
        base_path = os.path.join(os.getcwd(), "reportes")
        os.makedirs(base_path, exist_ok=True)

        salida_path = os.path.join(base_path, "Salida.txt")
        resumen_path = os.path.join(base_path, "Resumen.txt")

        # --- Salida.txt (cadenas y clasificación) ---
        with open(salida_path, "w", encoding="utf-8") as f:
            f.write("=== REPORTE DE TOKENS Y LEXEMAS ===\n\n")
            for t in tokens:
                f.write(f"{t['value']:<20} → {t['type']}\n")
            if error:
                f.write(f"\nERROR LÉXICO: '{error['char']}' en línea {error['line']}, columna {error['col']}\n")

        # --- Resumen.txt (conteo total) ---
        counts = {t: 0 for t in TOKEN_COLORS.keys()}
        for t in tokens:
            if t["type"] in counts:
                counts[t["type"]] += 1
        if error:
            counts["ERROR"] += 1
        with open(resumen_path, "w", encoding="utf-8") as f:
            f.write("=== RESUMEN DE TOKENS ===\n\n")
            for k, v in counts.items():
                f.write(f"{k:<10}: {v}\n")

        messagebox.showinfo("Reportes generados",
                            f"Se guardaron en:\n{base_path}\n\n- Salida.txt\n- Resumen.txt")

    # ===== CAMBIO DE TEMA =====
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.text.config(bg=DARK_BG, fg="white", insertbackground="white")
            self.status.config(bg=DARK_BG, fg="white")
        else:
            self.text.config(bg="white", fg="black", insertbackground="black")
            self.status.config(bg="white", fg="black")


# ===== MAIN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = LexicalColorer(root)
    root.mainloop()
