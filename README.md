# NYTHERA

> HTML → PDF conversion, done properly.

Nythera is a CLI tool that converts HTML files into PDF using WeasyPrint.
It focuses on **predictable output**, **local execution**, and **simple control**.

---

# ⚡ Quick Start (30 seconds)

1. Download `nythera.exe`
2. Open terminal in that folder
3. Run:

```bash
nythera file.html
```

PDF will be created in the same folder.

---

# 📦 Installation

## Windows

Download **`nythera.exe`** from Releases.

---

### ▶ Run directly

Open a terminal in the download folder and run:

```bash
nythera.exe
```

---

### ▶ Use from anywhere (recommended)

Move the executable to a permanent location:

```text
C:\tools\nythera
```

Add this folder to your system **`PATH`**:

1. Open **Environment Variables**
2. Edit **Path** under System Variables
3. Add `C:\tools\nythera`

Now you can run from any terminal:

```bash
nythera
```

---

### 💡 Tip

Keeping `nythera.exe` in a dedicated folder (like `C:\tools\nythera`) helps avoid accidental deletion and keeps your setup clean.

---

## Linux / macOS

Requires:

* Python `3.10+`
* System libraries: `cairo`, `pango`, `gdk-pixbuf`

If something fails, install the missing dependency mentioned in the error.

```bash
git clone https://github.com/developer-sumit-web/nythera.git
cd nythera
pip install .
```

Run:

```pwsh
nythera file.html
```

---

## ⚙️ Config File

```pwsh
nythera --config
```

Opens (or creates) your config file so you can control default behavior instead of passing flags every time.

Location:

* Windows → `C:\Users\<user>\.nythera\nythera.ini`
* Linux/macOS → `~/.config/nythera/nythera.ini`

Example:

```ini
[output]
page_mode = strict
default_dir =
overwrite = false
open_after = ask
```

---

# ❓ Why Nythera Exists

Designing in HTML is easy.
Getting the same result in PDF is not.

Most tools either:

* break layout
* give inconsistent output
* require uploads
* or become painful in repeated use

If you're already building something in HTML, converting it into PDF should not require redesigning it.

Nythera exists to:

* keep layout **predictable**
* work **fully offline**
* support **multiple files**
* avoid **external dependencies**

---

# 🚀 Features

Nythera focuses on a few things, but does them properly:

* **Exact rendering (`strict`)** → no layout surprises
* **Multiple files support** → batch conversion
* **Config-based control** → no repeated flags
* **Safe output handling** → no accidental overwrite
* **Interactive + CLI usage** → both workflows supported

---

# 🧩 Usage

## Convert a file

```bash
nythera file.html
```

Converts a single HTML file into a PDF.
Output is saved in the **same folder** unless configured otherwise, making it the quickest way to generate a PDF.

---

## Convert multiple files

```bash
nythera a.html b.html c.html
```

Processes all files in one run.
Each file generates its own PDF, which makes it useful for batch operations or exporting multiple pages at once.

---

## Set output directory

```bash
nythera file.html -o D:\PDFs
```

Overrides all config and saves output to the specified directory.
This is useful when you want temporary output control without changing your config.

---

## Disable opening

```bash
nythera file.html --no-open
```

Prevents automatic opening of the generated PDF.
Useful when processing many files or running scripts.

---

## Interactive mode

```bash
nythera
```

Starts prompt-based workflow:

* enter file paths
* choose output directory

Best when you don’t want to remember flags or are testing quickly.

---

# ⚙️ Configuration (important)

## Output directory

```ini
default_dir = D:\PDFs
```

Used when `-o` is not provided.
Fallback → input file folder.
Set this if you always want outputs in a fixed location.

---

## Overwrite

```ini
overwrite = false
```

Prevents overwriting:

```bash
file.pdf
file (1).pdf
```

```ini
overwrite = true
```

Replaces existing files.
Enable this only if you’re sure you don’t need older versions.

---

## Open behavior

```ini
open_after = ask | always | never
```

Controls whether PDFs open after generation.
Set `never` for automation workflows, or `ask` for manual usage.

---

## Rendering modes

```ini
page_mode = strict | a4 | flexible | auto
```

* `strict` → exact HTML
* `a4` → optimized for print
* `flexible` → adjusts layout
* `auto` → detects automatically

Choose based on whether you prioritize layout accuracy or print formatting.

---

## UI options

```ini
icons = auto | nerd | basic
progress = true | false
```

Controls CLI appearance and feedback.
Use `nerd` if your terminal supports Nerd Fonts for better visuals.

---

# 📁 Execution Flow

```bash
INPUT → PROCESS → OUTPUT → OPTIONAL OPEN
```

---

# 📂 Project Structure

```bash
nythera/
├── nythera/
│   ├── cli.py
│   └── __init__.py
├── dlls/              # Windows runtime dependencies
├── fonts/             # Optional font configs
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# ⚠️ Notes

* Output folder must exist
* HTML must be valid
* `.exe` works only on Windows
* Linux/mac require system libraries

---

# 🤝 Contributing

> [!NOTE]
> Nythera is a focused tool. Contributions are welcome, but they should align with how the project is being shaped.

This section exists to keep the codebase **simple**, **consistent**, and **easy to reason about**.

---

## 🎯 What This Project Needs

Nythera is not meant to become a large or complex system.
The goal is to keep it:

* **simple to use**
* **predictable in output**
* **easy to maintain**

Contributions that help most:

* improving **HTML → PDF consistency**
* fixing **layout edge cases**
* improving **CLI experience** (inputs, prompts, flow)
* improving behavior across different systems
* reducing friction in real-world usage

---

## 🧩 Good Contributions

If you're looking for where to start:

* fix small bugs or unexpected behavior
* improve error messages and handling
* improve config clarity or behavior
* refine CLI output and usability
* add practical documentation examples

Small, well-thought changes are preferred over large changes.

---

## ⚠️ Contribution Approach

> [!IMPORTANT]
> Keep changes focused and avoid unnecessary complexity.

When contributing:

* keep changes **focused**
* avoid touching unrelated parts of the code
* prefer **straightforward solutions**
* don’t introduce extra layers unless there is a clear need

The goal is to keep the project understandable at a glance.

---

## 🧠 What to Include in a PR

Every pull request should include:

* what was changed
* why the change was needed
* any tradeoffs or decisions made

Clear explanation matters as much as the code itself.

---

## 🤖 About AI Usage

AI-assisted code is fine, but it should not replace understanding.

* don’t submit code you can’t explain
* avoid dumping large generated blocks without context
* keep contributions readable and intentional

If AI was used, make sure the final result is something you understand and can justify.

---

## 📌 Platform Support Status

* **Windows** → fully supported (prebuilt executable available)
* **Linux / macOS** → supported via source install

Prebuilt binaries for Linux/macOS are not available yet.

Work on those is planned, but being handled gradually alongside core development.

> [!IMPORTANT]
> Improving cross-platform support (Linux/macOS) is one of the most valuable contributions right now.

---

## 🐞 Reporting Issues

👉 **[`Report an Issue`](https://github.com/developer-sumit-web/nythera/issues)**

When reporting, include:

* command used
* input file (if possible)
* expected vs actual behavior
* any error output

---

## 🚀 How to Contribute

1. Fork the repository
2. Create a branch
3. Make your change
4. Open a pull request

---

# 📜 License

```license
MIT License
```

Licensed under the **MIT License**.
See [`LICENSE`](./LICENSE) for full terms.

---

## 💬 Note

This project is being developed while I’m actively learning and improving my understanding of Python.

That means:

* decisions are intentional, but still evolving
* clarity and simplicity are prioritized over complexity
* contributions that keep things understandable are highly appreciated

---
