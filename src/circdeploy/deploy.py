import logging
import shutil
import sys
from pathlib import Path

from igittigitt import IgnoreParser
from rich import print  # noqa: A004

from circdeploy.file_cache import FileCache
from circdeploy.files import collect_matching_files

logger = logging.getLogger(__name__)


def delete_files(
    destination_root_dir: Path,
    exclude_files: list[Path],
    gitignore_parser: IgnoreParser | None,
    dry_run: bool,
):
    dest_files_to_delete = collect_matching_files(
        destination_root_dir,
        exclude_files=[*exclude_files, destination_root_dir.joinpath("lib")],
        gitignore_parser=gitignore_parser,
    )

    for file_to_delete in dest_files_to_delete:
        print(f"Deleting ./{file_to_delete.relative_to(destination_root_dir)}")

        if not dry_run:
            try:
                file_to_delete.unlink()
            except OSError as err:
                print(
                    f"Error while deleting file {file_to_delete}, {err=}, {type(err)=}"
                )
                raise


def deploy(
    source_root_dir: Path,
    destination_root_dir: Path,
    use_gitignore: bool,
    delete: bool,
    file_cache: FileCache | None,
    dry_run: bool,
):
    print(f"From: {source_root_dir}")
    print(f"  To: {destination_root_dir}\n")

    validate_directories(source_root_dir, destination_root_dir)

    gitignore_parser = setup_gitignore_parser(source_root_dir, use_gitignore)

    source_files = collect_matching_files(
        source_root_dir, exclude_files=None, gitignore_parser=gitignore_parser
    )

    dest_files_keep = copy_files(
        source_files, source_root_dir, destination_root_dir, file_cache, dry_run
    )

    if delete:
        delete_files(
            destination_root_dir,
            exclude_files=dest_files_keep,
            gitignore_parser=gitignore_parser,
            dry_run=dry_run,
        )


def validate_directories(source_root_dir: Path, destination_root_dir: Path):
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


def setup_gitignore_parser(source_root_dir: Path, use_gitignore: bool):
    if use_gitignore:
        gitignore_parser = IgnoreParser()
        gitignore_parser.parse_rule_files(source_root_dir)
        return gitignore_parser
    return None


def copy_files(
    source_files: list[Path],
    source_root_dir: Path,
    destination_root_dir: Path,
    file_cache: FileCache | None,
    dry_run: bool,
) -> list[Path]:
    dest_files_keep: list[Path] = []

    for file in source_files:
        dest_file = destination_root_dir.joinpath(file.relative_to(source_root_dir))
        dest_files_keep.append(dest_file)

        if (
            file_cache is not None
            and not file_cache.check_file_has_changed(file)
            and dest_file.exists()
        ):
            print(f"File {file} has not changed, skipping")
            continue

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
                raise
            try:
                shutil.copy(file, dest_file)
                if file_cache is not None:
                    file_cache.update(file)
            except (OSError, shutil.SameFileError) as err:
                print(
                    f"Error while copying file: {file} to: {dest_file}, "
                    f"{err=}, {type(err)=}"
                )
                raise
            if file_cache is not None:
                file_cache.save()

    return dest_files_keep
