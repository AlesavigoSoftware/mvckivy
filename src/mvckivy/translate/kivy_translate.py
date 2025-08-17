import argparse
import json
import os
import pathlib
from configparser import ConfigParser
from shutil import copyfile
from subprocess import run

invalid_arg_message = "use `get` or `make` mode"
available_modes = ("get", "make")
cwd = os.getcwd()
pot_path = f"{cwd}/locale/kivyapp.pot"
excluded_folders = {"__pycache__", ".buildozer", ".git", "bin"}
filter_extensions = (".py",)
verbose = False

settings = {
    "translator_name": "Not provided",
    "translator_email": "Not provided",
    "suppoted_languages": [],
    "main_file": "main.py",
    "excluded_folders": excluded_folders,
}

exts = {
    "py": "python",
    # kv not implemented yet
}


def print_colored(text, color=None):
    color_reset = "\033[0m"

    colors = {
        "error": "\33[31m",
        "warn": "\33[33m",
        "ok": "\33[32m",
    }

    color = colors.get(color) or color_reset

    if color:
        print(f"{color}{text}{color_reset}")

    else:
        print(text)


def print_verbose(*text, **kwargs):
    if verbose:
        print_colored(*text, **kwargs)


def subprocess_wrapper(command):
    proc = run(command)

    if proc.returncode:
        print_verbose(proc.returncode)
        print_colored(proc.stdout, "ok")
        print_colored(proc.stderr, "error")

    return proc.returncode == 0


def parse_config():
    cfg_file = f"{cwd}/.kivy_translate.cfg"

    try:
        cfg = ConfigParser(allow_no_value=True)
        cfg.read(cfg_file)

    except Exception as ex:
        print_colored(ex, "error")
        return

    settings["translator_name"] = cfg["settings"]["translator_name"]
    settings["translator_email"] = cfg["settings"]["translator_email"]
    settings["suppoted_languages"] = set(json.loads(cfg["settings"]["supported_languages"]))
    settings["main_file"] = [cfg["files"]["main_file"]]
    settings["filter_extensions"] = tuple(cfg["files"]["filter_extensions"])

    cfg_excluded_folders = set(json.loads(cfg["files"]["excluded_folders"]))
    cfg_excluded_folders.update(excluded_folders)

    settings["excluded_folders"] = tuple(cfg_excluded_folders)


def copy_file_if_doesnt_exist(filepath):
    if os.path.exists(filepath):
        return

    print_colored(f"creating file {filepath}")
    source = pot_path
    target = filepath
    copyfile(source, target)
    print_colored(f"file {filepath} created", "ok")


def create_folders():
    for lang in settings["suppoted_languages"]:
        pathlib.Path(f"{cwd}/locale/{lang}/LC_MESSAGES").mkdir(parents=True, exist_ok=True)

    if not os.path.isfile(pot_path):
        print_colored("creating POT file")

        with open(pot_path, "x"):
            pass

        print_colored("ok", "ok")


def get_all_files():
    loc_files = []
    path = f"{cwd}"

    project_folders = os.listdir(path=path)

    for folder in project_folders:
        if folder in settings["excluded_folders"]:
            continue

        for root, dirs, files in os.walk(f"{path}/{folder}"):
            for file in files:
                if file.endswith(settings["filter_extensions"]):
                    loc_files.append(os.path.relpath(os.path.join(root, file), "."))

    return loc_files


def collect_po():
    files = get_all_files()

    for file_ in files:
        file_ext = file_.split(".")[1]

        ext = exts.get(file_ext, None)

        if not ext:
            print_verbose(f"extension {file_ext} not supported, skipping", "warn")
            continue

        ext = ""
        print_verbose(file_)
        command = ["xgettext", "-Lpython", "-j", "--from-code=UTF-8", f"--output={pot_path}", file_]
        subprocess_wrapper(command)

        # fix charset
        command = ["sed", "-i", "-e", "s/charset=CHARSET/charset=UTF-8/g", pot_path]
        subprocess_wrapper(command)

    for lang in settings["suppoted_languages"]:
        target = f"{cwd}/locale/{lang}/LC_MESSAGES/kivyapp.po"
        copy_file_if_doesnt_exist(target)
        command = ["msgmerge", "--update", "--no-fuzzy-matching", "--backup=off", target, pot_path]
        subprocess_wrapper(command)


def compile_po():
    for lang in settings["suppoted_languages"]:
        print_colored(f"processing language: {lang}", "warn")
        command = [
            "msgfmt",
            "-c",
            "-o",
            f"{cwd}/locale/{lang}/LC_MESSAGES/kivyapp.mo",
            f"{cwd}/locale/{lang}/LC_MESSAGES/kivyapp.po",
        ]
        subprocess_wrapper(command)
        print_colored(f"processed", "ok")


def get_messages():
    create_folders()

    try:
        collect_po()

    finally:
        # remove POT file
        os.remove(pot_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        dest="mode",
        type=str,
        choices=["get", "make"],
        required=True,
        help="Mode of operation",
    )
    parser.add_argument(
        "--verbose", dest="verbose", action="store_true", help="Surname of the candidate"
    )
    args = parser.parse_args()

    # if args.verbose:
    #     verbose = True

    parse_config()

    if args.mode == "get":
        get_messages()

    elif args.mode == "make":
        compile_po()


if __name__ == "__main__":
    main()

