# ====================================================================
#                       imports
# ====================================================================
import os
import sys
import configparser
# ================= DLL FIX (EARLY) =================
if os.name == "nt":
    if getattr(sys, "frozen", False):
        # Running as EXE → use bundled DLLs
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        dll_path = os.path.join(base, "dlls")
    else:
        # Development → use system DLLs
        dll_path = r"C:\msys64\ucrt64\bin"

    if os.path.exists(dll_path):
        os.add_dll_directory(dll_path)
        os.environ["PATH"] = dll_path + ";" + os.environ["PATH"]
from contextlib import nullcontext
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from weasyprint import HTML, CSS
import shlex
import subprocess
import argparse

# ====================================================================

console = Console()


def get_icons(mode):
    if mode == "auto":
        mode = "nerd"

    if mode == "nerd":
        return {
            "header": "󰕰",
            "file": "󰈔",
            "folder": "󰉋",
            "process": "󰔟",
            "success": "󰄬",
            "error": "󰅖",
            "arrow": "󰁔"
        }
    else:
        return {
            "header": "◆",
            "file": "📄",
            "folder": "📁",
            "process": "⏳",
            "success": "✔",
            "error": "✗",
            "arrow": "→"
        }


def clean_path(p):
    return p.strip().strip('"').strip("'")


def parse_windows_paths(input_str):
    try:
        parts = shlex.split(input_str, posix=False)
    except Exception:
        parts = []

    if not parts:
        return [clean_path(input_str)] if input_str.strip() else []

    return [clean_path(p) for p in parts if p.strip()]

def get_unique_pdf_path(output_dir, base_name):
    counter = 0
    while True:
        if counter == 0:
            filename = f"{base_name}.pdf"
        else:
            filename = f"{base_name} ({counter}).pdf"

        full_path = os.path.join(output_dir, filename)

        if not os.path.exists(full_path):
            return full_path

        counter += 1


def is_a4_html(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()

        return "@page" in content and "a4" in content
    except Exception:
        return False


def get_config_path():
    if os.name == "nt":
        base = os.path.join(os.path.expanduser("~"), ".nythera")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config", "nythera")

    os.makedirs(base, exist_ok=True)

    return os.path.join(base, "nythera.ini")


def create_default_config(path):
    default_config = """[general]
icons = auto
progress = true

[output]
page_mode = strict
default_dir =
overwrite = false
open_after = ask

[theme]
mode = dark

primary_color = cyan
success_color = green
error_color = red
dim_color = grey50

header_style = bold
separator_style = dim

[advanced]
debug = false
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(default_config)


def load_config():
    config_path = get_config_path()

    if not os.path.exists(config_path):
        create_default_config(config_path)

    config = configparser.ConfigParser()
    config.read(config_path)

    return {
        "page_mode": config.get("output", "page_mode", fallback="auto"),

        "icons": config.get("general", "icons", fallback="auto"),
        "progress": config.getboolean("general", "progress", fallback=True),

        "primary_color": config.get("theme", "primary_color", fallback="cyan"),
        "success_color": config.get("theme", "success_color", fallback="green"),
        "error_color": config.get("theme", "error_color", fallback="red"),
        "dim_color": config.get("theme", "dim_color", fallback="grey50"),

        "header_style": config.get("theme", "header_style", fallback="bold"),
        "separator_style": config.get("theme", "separator_style", fallback="dim"),

        "debug": config.getboolean("advanced", "debug", fallback=False),

        "overwrite": config.getboolean("output", "overwrite", fallback=False),
        "open_after": config.get("output", "open_after", fallback="ask"),
    }


def main():
    last_pdf = None
    config = load_config()
    icons = get_icons(config["icons"])

    parser = argparse.ArgumentParser(
        prog="nythera",
        description="Convert HTML file(s) to PDF"
    )

    parser.add_argument(
        "--config",
        action="store_true",
        help="Open config file"
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="HTML file(s)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output directory"
    )

    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open PDF after creation"
    )

    parser.add_argument(
        "--guide",
        action="store_true",
        help="Show full usage guide"
    )

    args = parser.parse_args()
    if args.config:
        config_path = get_config_path()

        if sys.platform.startswith("win"):
            os.startfile(config_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", config_path])
        else:
            subprocess.Popen(["xdg-open", config_path])

        return
    is_cli = bool(args.files)

    if not args.guide and not any(arg in ("-h", "--help") for arg in sys.argv):
        console.print(
            f"\n[{config['header_style']} {config['primary_color']}]"
            f"{icons['header']} NYTHERA"
            f"[/{config['header_style']} {config['primary_color']}] "
            f"[{config['dim_color']}]HTML → PDF[/{config['dim_color']}]"
        )
        console.print(f"[{config['separator_style']}]────────────────────────────────────[/{config['separator_style']}]\n")
        if not is_cli:
            console.print(f"[{config['dim_color']}]Drag & drop file(s) or paste path(s)[/{config['dim_color']}]\n")

    if args.guide:
        console.print(
            f"[{config['header_style']} {config['primary_color']}]NYTHERA GUIDE[/{config['header_style']} {config['primary_color']}]\n"
        )

        console.print(f"[{config['dim_color']}]Convert HTML files to PDF using WeasyPrint[/{config['dim_color']}]\n")

        # ---------------- CLI USAGE ----------------
        console.print(
            f"[{config['header_style']} {config['primary_color']}]CLI Usage:[/{config['header_style']} {config['primary_color']}]"
        )
        console.print("  nythera file.html")
        console.print("  nythera file.html -o C:\\output")
        console.print("  nythera file1.html file2.html")
        console.print("  nythera file.html --no-open\n")

        # ---------------- INTERACTIVE ----------------
        console.print(
            f"[{config['header_style']} {config['primary_color']}]Interactive Mode:[/{config['header_style']} {config['primary_color']}]"
        )
        console.print(f"[{config['dim_color']}]Run without arguments:[/{config['dim_color']}]")
        console.print("  nythera")
        console.print(f"[{config['dim_color']}]Then follow prompts to enter file paths and output folder\n[/{config['dim_color']}]")

        # ---------------- CONFIG ----------------
        console.print(
            f"[{config['header_style']} {config['primary_color']}]Configuration:[/{config['header_style']} {config['primary_color']}]"
        )
        console.print(f"[{config['dim_color']}]Open config file:[/{config['dim_color']}]")
        console.print("  nythera --config")
        console.print(f"[{config['dim_color']}]Config controls themes, output behavior, and rendering mode\n[/{config['dim_color']}]")

        # ---------------- PAGE MODES ----------------
        console.print(
            f"[{config['header_style']} {config['primary_color']}]Page Modes:[/{config['header_style']} {config['primary_color']}]"
        )
        console.print("  strict     → exact HTML layout (no scaling, no margin fixes)")
        console.print("  a4         → force A4 layout")
        console.print("  flexible   → remove constraints")
        console.print("  auto       → detect from HTML\n")

        # ---------------- TIPS ----------------
        console.print(
            f"[{config['header_style']} {config['primary_color']}]Tips:[/{config['header_style']} {config['primary_color']}]"
        )
        console.print(f"[{config['dim_color']}]• Drag & drop files directly into terminal[/{config['dim_color']}]")
        console.print(f"[{config['dim_color']}]• Use quotes for paths with spaces[/{config['dim_color']}]")
        console.print(f"[{config['dim_color']}]• Multiple files are supported[/{config['dim_color']}]")

        return

    if is_cli and args.files:
        html_files = [clean_path(f) for f in args.files]

        if not html_files:
            console.print(f"\n[bold {config['error_color']}]{icons['error']} No input files provided[/bold {config['error_color']}]")
            return

        if args.output:
            output_dir = clean_path(args.output)
        else:
            output_dir = os.path.dirname(html_files[0]) or os.getcwd()
            console.print(f"[{config['dim_color']}]Using same folder as input[/{config['dim_color']}]")

    else:
        try:
            html_input = input(f"{icons['file']} HTML file(s) → ")
            if not html_input.strip():
                console.print(f"\n[bold {config['error_color']}]{icons['error']} No input provided[/bold {config['error_color']}]")
                return
        except KeyboardInterrupt:
            console.print(f"\n[bold {config['error_color']}]{icons['error']} Cancelled[/bold {config['error_color']}]")
            return
        html_files = parse_windows_paths(html_input)

        if not html_files:
            console.print(f"\n[bold {config['error_color']}]{icons['error']} No input files provided[/bold {config['error_color']}]")
            return

        try:
            output_dir = clean_path(input(f"{icons['folder']} Output dir → "))
        except KeyboardInterrupt:
            console.print(f"\n[bold {config['error_color']}]{icons['error']} Cancelled[/bold {config['error_color']}]")
            return

        if not output_dir.strip():
            output_dir = os.path.dirname(html_files[0]) or os.getcwd()
            console.print(f"[{config['dim_color']}]Using same folder as input[/{config['dim_color']}]")

    # Validation
    if not os.path.isdir(output_dir):
        console.print(f"\n[bold {config['error_color']}]{icons['error']} Output folder does not exist[/bold {config['error_color']}]")
        return


    results = []
    total = len(html_files)

    if config["progress"]:
        progress_ctx = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
        )
    else:
        progress_ctx = nullcontext()

    with progress_ctx as progress:

        if config["progress"]:
            task = progress.add_task("Processing", total=total)
        else:
            task = None

        mode = config["page_mode"]

        for html_file in html_files:


            if not os.path.exists(html_file):
                console.print(f"\n[bold {config['error_color']}]{icons['error']} Not found:[/bold {config['error_color']}] {html_file}")
                results.append(False)
                if config["progress"]:
                    progress.advance(task)
                continue

            if not html_file.lower().endswith((".html", ".htm")):
                console.print(f"\n[bold {config['error_color']}]{icons['error']} Invalid file:[/bold {config['error_color']}] {html_file}")
                results.append(False)
                if config["progress"]:
                    progress.advance(task)
                continue

            base_name = os.path.splitext(os.path.basename(html_file))[0]
            if config["overwrite"]:
                pdf_file = os.path.join(output_dir, f"{base_name}.pdf")
            else:
                pdf_file = get_unique_pdf_path(output_dir, base_name)

            try:
                if mode == "strict":
                    HTML(html_file).write_pdf(pdf_file)

                else:
                    if mode == "a4":
                        use_a4 = True
                    elif mode == "flexible":
                        use_a4 = False
                    else:
                        use_a4 = is_a4_html(html_file)

                    if use_a4:
                        css = """
                            @page {
                                size: A4;
                                margin: 0;
                            }

                            html, body {
                                width: 210mm;
                                min-height: 297mm;
                                margin: 0;
                                padding: 0;
                                font-family: Arial, Helvetica, sans-serif;
                            }

                            * {
                                box-sizing: border-box;
                            }
                        """
                    else:
                        css = """
                            @page {
                                margin: 0;
                            }

                            body {
                                margin: 0;
                                font-family: Arial, Helvetica, sans-serif;
                            }
                        """

                    HTML(html_file).write_pdf(
                        pdf_file,
                        stylesheets=[CSS(string=css)]
                    )
                last_pdf = pdf_file
                results.append(True)
            except Exception as e:
                console.print(f"\n[bold {config['error_color']}]{icons['error']} {e}[/bold {config['error_color']}]")
                results.append(False)

            if config["progress"]:
                progress.advance(task)

    success = sum(results)
    failed = len(results) - success

    console.print(f"\n[{config['header_style']} {config['primary_color']}]Summary[/{config['header_style']} {config['primary_color']}]")
    console.print(f"[{config['separator_style']}]──────────────[/{config['separator_style']}]")
    console.print(f"[{config['success_color']}]{icons['success']} Success : {success}[/{config['success_color']}]")
    console.print(f"[{config['error_color']}]{icons['error']} Failed  : {failed}[/{config['error_color']}]")


    if not last_pdf:
        console.print(f"\n[bold {config['error_color']}]{icons['error']} No valid files processed[/bold {config['error_color']}]")
        return
    # Ask AFTER processing (UI only)
    # if not is_cli:
    #     try:
    #         open_choice = input(f"\n{icons['arrow']} Open file? (y/n) → ").strip().lower()
    #     except KeyboardInterrupt:
    #         console.print(f"\n[bold {config['error_color']}]{icons['error']} Cancelled[/bold {config['error_color']}]")
    #         return

    #     open_after = open_choice in ("y", "yes")
    # Final decision
    setting = config["open_after"]

    if len(html_files) > 1:
        should_open = False

    elif setting == "always":
        should_open = True

    elif setting == "never":
        should_open = False

    elif setting == "ask" and not is_cli:
        try:
            choice = input(f"\n{icons['arrow']} Open file? (y/n) → ").strip().lower()
            should_open = choice in ("y", "yes")
        except KeyboardInterrupt:
            should_open = False

    else:
        should_open = not args.no_open

    if should_open:
        if sys.platform.startswith("win"):
            os.startfile(last_pdf)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", last_pdf])
        else:
            subprocess.Popen(["xdg-open", last_pdf])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Cancelled[/bold red]")