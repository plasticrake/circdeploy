import re
import shutil
import sys
from pathlib import Path
from typing import Optional

import igittigitt
import typer
from circup import find_device, get_circuitpython_version
from rich import print


def include_file(file_path: Path, gitignore_parser):
    if gitignore_parser is not None:
        result = gitignore_parser.match(file_path)
        if result is True:
            return False

    if file_path.name.startswith("."):
        return False

    if re.search("^\\.pyc?$", file_path.suffix, re.IGNORECASE) is None:
        return False

    return True


def include_dir(dir_path: Path, gitignore_parser):
    if gitignore_parser is not None:
        result = gitignore_parser.match(dir_path)
        if result is True:
            return False

    if dir_path.name.startswith("."):
        return False

    return True


def collect_matches_for_path(source_path: Path, gitignore_parser: bool):

    source_files = []
    source_dirs = []

    for child in source_path.iterdir():

        if child.is_file():
            if include_file(child, gitignore_parser):
                source_files.append(child.resolve())
        elif child.is_dir():
            if include_dir(child, gitignore_parser):
                source_dirs.append(child.resolve())

    return (source_files, source_dirs)


def main():

    app = typer.Typer()

    @app.command()
    def deploy(
        source: Optional[str] = typer.Option(
            Path.cwd(),
            "--source",
            "--src",
            "-s",
            help="Deploy from this location.",
        ),
        destination: Optional[str] = typer.Option(
            None,
            "--destination",
            "--dest",
            "-d",
            help="Deploy to this location.",
            show_default="Device path automatically detected",
        ),
        use_gitignore: Optional[bool] = typer.Option(
            True,
            "--use-gitignore/--no-gitignore",
            help="Ignore files using .gitignore files relative to source path.",
        ),
        dry_run: Optional[bool] = typer.Option(
            False, "--dry-run", help="Don't copy files, only output what would be done."
        ),
    ):
        """Deploy current CircuitPython project"""
        if destination is None:
            destination = find_device()

        if destination is None:
            print("[bold red]Could not find a connected CircuitPython device.")
            sys.exit(1)
        else:
            if Path(destination, "boot_out.txt").is_file():
                CPY_VERSION, board_id = get_circuitpython_version(destination)
                print(
                    f"Found device ({board_id}) at {destination}, "
                    f"running CircuitPython {CPY_VERSION}\n"
                )

        destination_root_dir = Path(destination).resolve()
        source_root_dir = Path(source).resolve()

        print(f"From: {source_root_dir}")
        print(f"  To: {destination_root_dir}\n")

        if not source_root_dir.is_dir():
            print(
                "[bold red]"
                "Source path does not exist or is not a directory:"
                "[/bold red] "
                f"{source_root_dir}"
            )
            sys.exit(1)
        if not destination_root_dir.is_dir():
            print(
                "[bold red]"
                "Destination path does not exist or is not a directory:"
                "[/bold red] "
                f"{destination_root_dir}"
            )
            sys.exit(1)

        if use_gitignore:
            gitignore_parser = igittigitt.IgnoreParser()
            gitignore_parser.parse_rule_files(source_root_dir)
        else:
            gitignore_parser = None

        source_files: list[Path] = []
        source_dirs = [source_root_dir]

        while len(source_dirs) > 0:
            source_dir = source_dirs.pop()

            (source_files_for_path, source_dirs_for_path) = collect_matches_for_path(
                source_dir, gitignore_parser
            )
            source_files += source_files_for_path
            source_dirs += source_dirs_for_path

        for file in source_files:
            dest_file = destination_root_dir.joinpath(file.relative_to(source_root_dir))
            print(
                f"Copying ./{file.relative_to(source_root_dir)} to "
                f"./{dest_file.relative_to(destination_root_dir)}"
            )
            if not dry_run:
                try:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                except FileNotFoundError as err:
                    print(
                        f"Error while creating destination directory "
                        f"{dest_file.parent}, {err=}, {type(err)=}"
                    )
                    raise err
                try:
                    shutil.copy(file, dest_file)
                except (OSError, shutil.SameFileError) as err:
                    print(
                        f"Error while copying file: {file} to: {dest_file}, "
                        f"{err=}, {type(err)=}"
                    )
                    raise err

    app()
