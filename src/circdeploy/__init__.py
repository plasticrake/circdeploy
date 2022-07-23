# this is needed to support list[Path] typing on python 3.8
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

import igittigitt
import typer
from circup import find_device, get_circuitpython_version
from rich import print

__version__ = "0.2.0"


def include_file(file_path: Path, exclude_files: list[Path] | None, gitignore_parser):

    if exclude_files is not None:
        realpath = os.path.realpath(file_path)
        for f in exclude_files:
            if os.path.realpath(f) == realpath:
                return False

    if gitignore_parser is not None:
        result = gitignore_parser.match(file_path)
        if result is True:
            return False

    if file_path.name.startswith("."):
        return False

    if re.search("^\\.pyc?$", file_path.suffix, re.IGNORECASE) is None:
        return False

    return True


def include_dir(dir_path: Path, exclude_files: list[Path] | None, gitignore_parser):

    if exclude_files is not None:
        realpath = os.path.realpath(dir_path)
        for f in exclude_files:
            if os.path.realpath(f) == realpath:
                return False

    if gitignore_parser is not None:
        result = gitignore_parser.match(dir_path)
        if result is True:
            return False

    if dir_path.name.startswith("."):
        return False

    return True


def collect_matches_for_path(
    path: Path, exclude_files: list[Path], gitignore_parser: bool
):

    files = []
    dirs = []

    for child in path.iterdir():

        if child.is_file():
            if include_file(child, exclude_files, gitignore_parser):
                files.append(child.resolve())
        elif child.is_dir():
            if include_dir(child, exclude_files, gitignore_parser):
                dirs.append(child.resolve())

    return (files, dirs)


def collect_matching_files(
    dir: Path, exclude_files: list[Path], gitignore_parser: bool
):
    dirs = [dir]
    files: list[Path] = []

    while len(dirs) > 0:
        dir = dirs.pop()

        (files_for_path, dirs_for_path) = collect_matches_for_path(
            dir, exclude_files, gitignore_parser
        )
        files += files_for_path
        dirs += dirs_for_path

    return files


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
        delete: Optional[bool] = typer.Option(
            True,
            help="Delete files in destination.",
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
        """Deploy current CircuitPython project

        All .py and .pyc files in the current directory tree will be copied to the
        destination (device)\n
        All other .py and .pyc files in the destination directory tree (device)
        will be deleted except /lib/
        """
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

        source_files = collect_matching_files(source_root_dir, None, gitignore_parser)

        # files copied to destination
        dest_files_copied: list[Path] = []

        for file in source_files:
            dest_file = destination_root_dir.joinpath(file.relative_to(source_root_dir))
            dest_files_copied.append(dest_file)

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

        dest_files_to_delete = collect_matching_files(
            destination_root_dir,
            dest_files_copied + [destination_root_dir.joinpath("lib")],
            gitignore_parser,
        )

        for file_to_delete in dest_files_to_delete:
            print(f"Deleting ./{file_to_delete.relative_to(destination_root_dir)}")

            if not dry_run:
                try:
                    os.remove(file_to_delete)
                except (OSError) as err:
                    print(
                        f"Error while deleting file "
                        f"{file_to_delete}, {err=}, {type(err)=}"
                    )
                    raise err

    app()
