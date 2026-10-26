#!/usr/bin/env python3
"""PGN Cleaner — bezplatný grafický nástroj pro hromadnou úpravu šachových partií."""
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import re
import unicodedata

FIELDS = [
    ("Event", "Turnaj / událost"),
    ("Site", "Místo"),
    ("Date", "Datum (YYYY.MM.DD)"),
    ("Round", "Kolo"),
    ("ECO", "ECO"),
]


def remove_diacritics(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", text)


def set_tag(header, tag, value):
    pattern = re.compile(r'^\[' + re.escape(tag) + r'\s+"[^"]*"\]\s*$', re.MULTILINE)
    replacement = f'[{tag} "{value}"]'
    if pattern.search(header):
        return pattern.sub(lambda _m: replacement, header, count=1)
    return header.rstrip() + "\n" + replacement


def split_header_moves(game):
    lines = game.splitlines(keepends=True)
    header, moves = [], []
    in_moves = False
    for line in lines:
        s = line.strip()
        if not in_moves and s.startswith("[") and s.endswith("]"):
            header.append(line)
        elif not in_moves and not s and header:
            header.append(line)
        elif not in_moves and not s and not header:
            header.append(line)
        else:
            in_moves = True
            moves.append(line)
    return "".join(header).strip(), "".join(moves)


def clean_moves(moves):
    out = []
    brace_depth = 0
    variation_depth = 0
    semicolon = False
    for ch in moves:
        if semicolon:
            if ch in "\r\n":
                semicolon = False
                if brace_depth == 0 and variation_depth == 0:
                    out.append(ch)
            continue
        if brace_depth:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
            continue
        if ch == "{":
            brace_depth = 1
            continue
        if variation_depth:
            if ch == "(":
                variation_depth += 1
            elif ch == ")":
                variation_depth -= 1
            continue
        if ch == "(":
            variation_depth = 1
            continue
        if ch == ";":
            semicolon = True
            continue
        out.append(ch)

    text = "".join(out)
    text = re.sub(r'\$\d+\b', '', text)
    text = re.sub(r'(?<=\S)(?:!!|\?\?|!\?|\?!|!|\?)(?=\s|$)', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n[ \t]*', '\n', text)
    return text.strip()


def process_pgn(text, values, remove_diacritics_flag, clean_flag):
    # Standardní PGN partie zpravidla začínají hlavičkou [Event "..."].
    chunks = re.split(r'(?=^\[Event\s+")', text, flags=re.MULTILINE)
    output = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        header, moves = split_header_moves(chunk)
        for tag, value in values.items():
            if value:
                header = set_tag(header, tag, value)
        if clean_flag:
            moves = clean_moves(moves)
        part = header
        if moves.strip():
            part += "\n\n" + moves.strip()
        if remove_diacritics_flag:
            part = remove_diacritics(part)
        output.append(part.strip())
    return "\n\n".join(output) + "\n"


class App:
    def __init__(self, root):
        self.root = root
        root.title("PGN Cleaner — hromadná úprava šachových partií")
        root.geometry("850x690")
        root.minsize(760, 620)
        self.files = []

        tk.Label(root, text="PGN Cleaner", font=("Sans", 16, "bold")).pack(pady=(10, 2))
        tk.Label(root, text="Vyberte jednu nebo více PGN partií. Originály zůstanou beze změny.").pack(pady=(0, 7))

        pick_row = tk.Frame(root)
        pick_row.pack(pady=2)
        tk.Button(pick_row, text="Přidat PGN soubory", command=self.choose_files, width=22).pack(side="left", padx=4)
        tk.Button(pick_row, text="Vymazat seznam", command=self.clear_list, width=16).pack(side="left", padx=4)

        list_frame = tk.Frame(root)
        list_frame.pack(padx=14, pady=7, fill="both", expand=True)
        self.listbox = tk.Listbox(list_frame, height=5, width=90)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame = tk.LabelFrame(root, text="Hromadná změna hlavičky (zaškrtněte jen údaje, které chcete změnit)")
        frame.pack(padx=14, pady=4, fill="x")
        self.vars, self.entries = {}, {}
        for i, (tag, label) in enumerate(FIELDS):
            var = tk.BooleanVar(value=False)
            self.vars[tag] = var
            tk.Checkbutton(frame, text=label, variable=var).grid(row=i, column=0, sticky="w", padx=7, pady=2)
            ent = tk.Entry(frame, width=45)
            ent.grid(row=i, column=1, padx=7, pady=2, sticky="ew")
            self.entries[tag] = ent
        frame.columnconfigure(1, weight=1)

        options = tk.LabelFrame(root, text="Čištění a výstup")
        options.pack(padx=14, pady=4, fill="x")
        self.clean = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options,
            text="Odstranit komentáře, vedlejší varianty a značky hodnocení tahů (!, ?, $1 apod.)",
            variable=self.clean
        ).pack(anchor="w", padx=7, pady=2)
        self.diacritic = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options, text="Odstranit diakritiku z celého PGN", variable=self.diacritic
        ).pack(anchor="w", padx=7, pady=2)
        self.merge = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options, text="Sloučit všechny vybrané soubory do jednoho nového PGN",
            variable=self.merge
        ).pack(anchor="w", padx=7, pady=2)

        buttons = tk.Frame(root)
        buttons.pack(pady=5)
        tk.Button(buttons, text="Zpracovat PGN", command=self.process, width=20, height=1).pack(side="left", padx=5)
        tk.Button(buttons, text="Konec", command=root.destroy, width=12, height=1).pack(side="left", padx=5)
        self.status = tk.Label(root, text="Není vybrán žádný soubor.")
        self.status.pack(pady=(0, 7))

    def choose_files(self):
        files = filedialog.askopenfilenames(
            title="Vyberte PGN soubory",
            filetypes=[("PGN soubory", "*.pgn"), ("Všechny soubory", "*.*")]
        )
        if not files:
            return
        known = {str(p.resolve()) for p in self.files}
        added = 0
        for filename in files:
            p = Path(filename)
            key = str(p.resolve())
            if key not in known:
                self.files.append(p)
                known.add(key)
                self.listbox.insert(tk.END, str(p))
                added += 1
        self.status.config(text=f"Vybráno souborů: {len(self.files)} (nově přidáno: {added})")

    def clear_list(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)
        self.status.config(text="Seznam souborů je prázdný.")

    def process(self):
        if not self.files:
            messagebox.showwarning("PGN Cleaner", "Nejdříve vyberte PGN soubory.")
            return
        values = {tag: self.entries[tag].get().strip() for tag, _ in FIELDS if self.vars[tag].get()}
        if not values and not self.diacritic.get() and not self.clean.get() and not self.merge.get():
            messagebox.showwarning("PGN Cleaner", "Nejdříve vyberte alespoň jednu úpravu.")
            return

        merge_path = None
        if self.merge.get():
            merge_name = filedialog.asksaveasfilename(
                title="Uložit sloučené PGN jako",
                defaultextension=".pgn",
                initialfile="sloucene_partie.pgn",
                filetypes=[("PGN soubory", "*.pgn"), ("Všechny soubory", "*.*")]
            )
            if not merge_name:
                return
            merge_path = Path(merge_name).resolve()
            if any(merge_path == p.resolve() for p in self.files):
                messagebox.showerror("PGN Cleaner", "Výstupní soubor nesmí být jedním ze vstupních souborů.")
                return

        count, errors, merged_parts, successful = 0, [], [], []
        for src in self.files:
            try:
                raw = src.read_bytes()
                try:
                    input_text = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    input_text = raw.decode("cp1250")
                new_text = process_pgn(input_text, values, self.diacritic.get(), self.clean.get())
                if self.merge.get():
                    merged_parts.append(new_text.strip())
                else:
                    out = src.with_name(src.stem + "_cisty.pgn")
                    if out.resolve() == src.resolve():
                        raise ValueError("Výstup by přepsal vstupní soubor.")
                    out.write_text(new_text, encoding="utf-8")
                successful.append(src)
                count += 1
            except Exception as exc:
                errors.append(f"{src.name}: {exc}")

        if self.merge.get() and merged_parts:
            try:
                merge_path.write_text("\n\n".join(merged_parts) + "\n", encoding="utf-8")
            except Exception as exc:
                errors.append(f"Sloučený soubor: {exc}")

        msg = f"Zpracováno vstupních souborů: {count}"
        if self.merge.get() and merged_parts:
            msg += f"\nSloučený soubor uložen jako:\n{merge_path}"
        elif not self.merge.get():
            msg += "\nVýsledky mají příponu _cisty.pgn."
        if errors:
            msg += "\n\nChyby:\n" + "\n".join(errors)
        messagebox.showinfo("PGN Cleaner", msg)

        if not errors:
            self.clear_list()
        else:
            # Ponechá jen soubory, které se nepodařilo zpracovat.
            self.files = [p for p in self.files if p not in successful]
            self.listbox.delete(0, tk.END)
            for p in self.files:
                self.listbox.insert(tk.END, str(p))
            self.status.config(text=f"Zbývá souborů k opravě: {len(self.files)}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
