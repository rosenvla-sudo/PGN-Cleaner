# PGN Cleaner — bezplatný nástroj pro šachové partie

PGN Cleaner je malá česká aplikace s grafickým rozhraním pro hromadnou úpravu souborů PGN.

## Funkce
- vybrání více PGN souborů najednou;
- hromadná změna hlaviček Event, Site, Date, Round a ECO;
- odstranění komentářů, vedlejších variant a značek hodnocení tahů;
- volitelné odstranění diakritiky;
- volitelné sloučení vybraných souborů do jednoho nového PGN;
- originální soubory se nepřepisují;
- po úspěšném zpracování se seznam souborů automaticky vymaže.

## Windows — stažení hotového EXE
Hotový `PGN-Cleaner.exe` se sestavuje automaticky pomocí GitHub Actions.
- Po nahrání změn otevřete kartu **Actions** a vyberte poslední běh workflow.
- V dolní části běhu stáhněte artefakt **PGN-Cleaner-Windows** (ZIP obsahující EXE).
- Pro veřejné vydání vytvořte a odešlete tag ve tvaru `v1.0.0`. Workflow vytvoří GitHub Release a přiloží `PGN-Cleaner.exe`.

## Spuštění na Linuxu
Vyžaduje Python 3 a Tkinter. Na Ubuntu lze v případě potřeby doinstalovat Tkinter:
`sudo apt install python3-tk`
Potom spusťte:
`python3 pgn_cleaner.py`

## Poznámka
Aplikace pracuje s běžnými textovými PGN soubory. Před hromadnými úpravami si ponechte záložní kopie důležitých dat.
