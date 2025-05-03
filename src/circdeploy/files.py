import os
import re
from pathlib import Path

from igittigitt import IgnoreParser


def include_file(
    file_path: Path,
    exclude_files: list[Path] | None,
    gitignore_parser: IgnoreParser | None,
):
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


def include_dir(
    dir_path: Path,
    exclude_files: list[Path] | None,
    gitignore_parser: IgnoreParser | None,
):
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
    path: Path, exclude_files: list[Path] | None, gitignore_parser: IgnoreParser | None
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
    dir: Path, exclude_files: list[Path] | None, gitignore_parser: IgnoreParser | None
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
