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

    return re.search(r"^\.pyc?$", file_path.suffix, re.IGNORECASE) is not None


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

    return not dir_path.name.startswith(".")


def collect_matches_for_path(
    path: Path, exclude_files: list[Path] | None, gitignore_parser: IgnoreParser | None
):
    files = []
    paths = []

    for child in path.iterdir():
        if child.is_file():
            if include_file(child, exclude_files, gitignore_parser):
                files.append(child.resolve())
        elif child.is_dir() and include_dir(child, exclude_files, gitignore_parser):
            paths.append(child.resolve())

    return (files, paths)


def collect_matching_files(
    path: Path, exclude_files: list[Path] | None, gitignore_parser: IgnoreParser | None
):
    paths = [path]
    files: list[Path] = []

    while len(paths) > 0:
        path = paths.pop()

        (files_for_path, dirs_for_path) = collect_matches_for_path(
            path, exclude_files, gitignore_parser
        )
        files += files_for_path
        paths += dirs_for_path

    return files
