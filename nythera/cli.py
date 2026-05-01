# ====================================================================
#                       imports
# ====================================================================
import os
import sys
import configparser
# ================= DLL FIX (EARLY) =================
if os.name == "nt":
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        dll_path = os.path.join(base, "dlls")
        font_path = os.path.join(base, "fonts")
    else:
        dll_path = r"C:\msys64\ucrt64\bin"
        font_path = r"C:\msys64\ucrt64\etc\fonts"

    if os.path.exists(dll_path):
        os.add_dll_directory(dll_path)
        os.environ["PATH"] = dll_path + ";" + os.environ["PATH"]

    if os.path.exists(font_path):
        os.environ["FONTCONFIG_PATH"] = font_path

# ====================================================================

from contextlib import nullcontext
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from weasyprint import HTML, CSS
from nythera import __version__
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
# Icon style: auto | nerd | basic
icons = auto

# Show progress bar: true | false
progress = true


[output]
# Page rendering mode:
# strict    → exact HTML (no changes)
# a4        → force A4 layout
# flexible  → remove constraints
# auto      → detect from HTML
page_mode = strict

# Where to save generated PDFs
# Empty → same folder as input
# Set a path → always use it (overridden by -o or manual input)
default_dir =

# Overwrite existing PDFs: true | false
overwrite = false

# Open PDF after creation:
# ask     → prompt user
# always  → open automatically
# never   → do not open
open_after = ask


[theme]
# Theme mode (future use): dark | light | custom
mode = dark

primary_color = cyan
success_color = green
error_color = red
dim_color = grey50

header_style = bold
separator_style = dim


[advanced]
# Enable debug logs: true | false
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
        "default_dir": config.get("output", "default_dir", fallback=""),
    }


def show_help(config, icons):
    console.print(
        f"\n[{config['header_style']} {config['primary_color']}]"
        f"{icons['header']} NYTHERA"
        f"[/{config['header_style']} {config['primary_color']}] "
        f"[{config['dim_color']}]HTML → PDF[/{config['dim_color']}]\n"
    )

    console.print(f"[bold]Usage[/bold]")
    console.print("  nythera file.html")
    console.print("  nythera file.html -o D:\\PDFs")
    console.print("  nythera a.html b.html c.html\n")

    console.print(f"[bold]Options[/bold]")
    console.print("  -h, --help        Show this help message")
    console.print("  --config          Open config file")
    console.print("  -o, --output      Output directory")
    console.print("  --no-open         Do not open PDF after creation")
    console.print("  --guide           Show full usage guide\n")

    console.print(f"[bold]Examples[/bold]")
    console.print("  nythera file.html")
    console.print("  nythera file.html -o D:\\PDFs")
    console.print("  nythera a.html b.html\n")

    console.print(f"[{config['dim_color']}]Use 'nythera --guide' for full documentation[/{config['dim_color']}]\n")


def main():
    last_pdf = None
    config = load_config()
    icons = get_icons(config["icons"])

    parser = argparse.ArgumentParser(
        prog="nythera",
        add_help=False
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version"
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

    if args.version:
        console.print(f"nythera {__version__}")
        return
    
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

    if any(arg in ("-h", "--help") for arg in sys.argv):
        show_help(config, icons)
        return

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
            f"\n[{config['header_style']} {config['primary_color']}]"
            f"{icons['header']} NYTHERA GUIDE"
            f"[/{config['header_style']} {config['primary_color']}]\n"
        )

        console.print(f"[{config['dim_color']}]Convert HTML to PDF from the command line.[/{config['dim_color']}]\n")

        # --------------------------------------------------
        console.print("[bold]OVERVIEW[/bold]")
        console.print(
            f"[{config['dim_color']}]Nythera takes one or more HTML files, processes them using WeasyPrint, and generates PDF output based on your configuration or CLI options.[/{config['dim_color']}]\n"
        )

        # --------------------------------------------------
        console.print("[bold]INPUT[/bold]")
        console.print("  nythera file.html")
        console.print(
            f"[{config['dim_color']}]Provide one or more HTML files as arguments. Each file is processed independently.[/{config['dim_color']}]\n"
        )

        console.print("  nythera a.html b.html c.html")
        console.print(
            f"[{config['dim_color']}]Multiple files are supported. Each input generates its own PDF output.[/{config['dim_color']}]\n"
        )

        # --------------------------------------------------
        console.print("[bold]OUTPUT[/bold]")
        console.print("  nythera file.html -o D:\\PDFs")
        console.print(
            f"[{config['dim_color']}]Use -o to control where PDFs are saved. This overrides the config file.[/{config['dim_color']}]"
        )
        console.print(
            f"[{config['dim_color']}]If not provided, output follows this order:[/{config['dim_color']}]"
        )
        console.print("    1. default_dir (config)")
        console.print("    2. same folder as input\n")

        # --------------------------------------------------
        console.print("[bold]INTERACTIVE MODE[/bold]")
        console.print("  nythera")
        console.print(
            f"[{config['dim_color']}]Run without arguments to enter file paths and output directory manually.[/{config['dim_color']}]\n"
        )

        # --------------------------------------------------
        console.print("[bold]CONFIGURATION[/bold]")
        console.print("  nythera --config")
        console.print(
            f"[{config['dim_color']}]Opens the config file where default behavior is controlled.[/{config['dim_color']}]\n"
        )

        console.print("  Important settings:")
        console.print("    default_dir   → default output location")
        console.print("    overwrite     → replace or keep existing files")
        console.print("    open_after    → control auto opening")
        console.print("    page_mode     → rendering behavior\n")

        # --------------------------------------------------
        console.print("[bold]RENDERING MODES[/bold]")
        console.print("  strict")
        console.print(
            f"[{config['dim_color']}]Uses HTML exactly as written. Best when layout is already correct.[/{config['dim_color']}]\n"
        )

        console.print("  a4")
        console.print(
            f"[{config['dim_color']}]Forces A4 layout. Useful for printing and reports.[/{config['dim_color']}]\n"
        )

        console.print("  flexible")
        console.print(
            f"[{config['dim_color']}]Adjusts layout when content overflows or breaks.[/{config['dim_color']}]\n"
        )

        console.print("  auto")
        console.print(
            f"[{config['dim_color']}]Automatically decides based on HTML content.[/{config['dim_color']}]\n"
        )

        # --------------------------------------------------
        console.print("[bold]BEHAVIOR CONTROL[/bold]")
        console.print("  overwrite = false")
        console.print(
            f"[{config['dim_color']}]Creates new files instead of replacing existing ones.[/{config['dim_color']}]\n"
        )

        console.print("  overwrite = true")
        console.print(
            f"[{config['dim_color']}]Replaces existing files with the same name.[/{config['dim_color']}]\n"
        )

        console.print("  open_after = ask | always | never")
        console.print(
            f"[{config['dim_color']}]Controls whether PDFs are opened after creation.[/{config['dim_color']}]\n"
        )

        # --------------------------------------------------
        console.print("[bold]COMMON USE CASES[/bold]")

        console.print("  Convert one file")
        console.print("    nythera file.html\n")

        console.print("  Convert multiple files")
        console.print("    nythera a.html b.html\n")

        console.print("  Save to different folder")
        console.print("    nythera file.html -o D:\\PDFs\n")

        console.print("  Use in automation")
        console.print("    nythera file.html --no-open\n")

        console.print("  Fix layout issues")
        console.print("    page_mode = flexible (config)\n")

        console.print("  Print-ready output")
        console.print("    page_mode = a4\n")

        # ---------------------- Aliases guide ----------------------------
        console.print("[bold]SHORTCUTS (Aliases)[/bold]")

        console.print(
            f"[{config['dim_color']}]If you use Nythera frequently, you can create short commands (aliases) in your terminal so you don’t need to remember full arguments.[/{config['dim_color']}]\n"
        )

        console.print("Example:")
        console.print("  nythera file.html -o D:\\PDFs --no-open\n")

        console.print(
            f"[{config['dim_color']}]Instead of typing this every time, you can create a shortcut like 'npdf'.[/{config['dim_color']}]\n"
        )

        console.print("[bold]PowerShell[/bold]")
        console.print("  notepad $PROFILE")
        console.print("  Add:")
        console.print('    function npdf { nythera $args -o "D:\\PDFs" --no-open }')
        console.print(
            f"[{config['dim_color']}]Restart terminal and use: npdf file.html[/{config['dim_color']}]\n"
        )

        console.print("[bold]Git Bash / Bash[/bold]")
        console.print("  nano ~/.bashrc")
        console.print("  Add:")
        console.print('    alias npdf="nythera -o /d/PDFs --no-open"')
        console.print(
            f"[{config['dim_color']}]Run: source ~/.bashrc[/{config['dim_color']}]"
        )
        console.print(
            f"[{config['dim_color']}]Then use: npdf file.html[/{config['dim_color']}]\n"
        )

        console.print("[bold]Zsh (macOS / Linux)[/bold]")
        console.print("  nano ~/.zshrc")
        console.print("  Add:")
        console.print('    alias npdf="nythera -o ~/PDFs --no-open"')
        console.print(
            f"[{config['dim_color']}]Run: source ~/.zshrc[/{config['dim_color']}]\n"
        )

        # --------------------------------------------------
        console.print("[bold]NOTES[/bold]")
        console.print(f"[{config['dim_color']}]• Output folder must exist")
        console.print("• Use quotes for paths with spaces")
        console.print("• Drag & drop files into terminal")
        console.print("• Linux/mac require system libraries[/]\n")

        return

    if is_cli and args.files:
        html_files = [clean_path(f) for f in args.files]

        if not html_files:
            console.print(f"\n[bold {config['error_color']}]{icons['error']} No input files provided[/bold {config['error_color']}]")
            return

        if args.output:
            output_dir = clean_path(args.output)

        elif config.get("default_dir"):
            candidate = clean_path(config["default_dir"])

            if os.path.isdir(candidate):
                output_dir = candidate
                console.print(f"[{config['dim_color']}]Using default output directory[/{config['dim_color']}]")
            else:
                console.print(f"[{config['dim_color']}]Invalid default_dir, using input folder instead[/{config['dim_color']}]")
                output_dir = os.path.dirname(os.path.abspath(html_files[0])) or os.getcwd()

        else:
            output_dir = os.path.dirname(os.path.abspath(html_files[0])) or os.getcwd()
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
            output_dir = os.path.dirname(os.path.abspath(html_files[0])) or os.getcwd()
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

    elif setting == "ask":
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