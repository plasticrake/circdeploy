import logging
import sys
from pathlib import Path

import typer
from circup import DiskBackend  # type: ignore
from circup import logger as circup_logger  # type: ignore
from circup.command_utils import find_device  # type: ignore
from platformdirs import user_cache_dir
from rich import print  # noqa: A004

from circdeploy.deploy import deploy as deploy_files
from circdeploy.file_cache import FileCache, calc_project_hash

__version__ = "1.0.0"

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)

    app = typer.Typer()

    @app.command()
    def deploy(
        source: str = typer.Option(
            Path.cwd(),
            "--source",
            "--src",
            "-s",
            help="Deploy from this location.",
        ),
        destination: str | None = typer.Option(
            None,
            "--destination",
            "--dest",
            "-d",
            help="Deploy to this location.",
            show_default="Device path automatically detected",
        ),
        delete: bool = typer.Option(
            True,
            help="Delete files in destination.",
        ),
        use_gitignore: bool = typer.Option(
            True,
            "--use-gitignore/--no-gitignore",
            help="Ignore files using .gitignore files relative to source path.",
        ),
        use_cache: bool = typer.Option(
            True,
            "--use-cache/--no-cache",
            help="Use file cache to skip unchanged files.",
        ),
        reset_cache: bool = typer.Option(
            False,
            "--reset-cache",
            help="Reset file cache.",
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Don't copy files, only output what would be done."
        ),
    ):
        """Deploy current CircuitPython project

        All .py and .pyc files in the current directory tree will be copied to the
        destination (device)\n
        All other .py and .pyc files in the destination directory tree (device)
        will be deleted except /lib/ (disable with --no-delete)
        """
        if destination is None:
            destination = find_device()

        if destination is None:
            print("[bold red]Could not find a connected CircuitPython device.")
            sys.exit(1)
        else:
            if Path(destination, "boot_out.txt").is_file():
                circuit_python_version, board_id = DiskBackend(
                    destination, circup_logger
                ).get_circuitpython_version()
                print(
                    f"Found device ({board_id}) at {destination}, "
                    f"running CircuitPython {circuit_python_version}\n"
                )

        destination_root_dir = Path(destination).resolve()
        source_root_dir = Path(source).resolve()

        cache_dir = user_cache_dir("circdeploy")
        project_hash = calc_project_hash(source_root_dir)
        cache_file_path = Path(cache_dir).joinpath(project_hash, "file_cache.pkl")
        logging.debug(f"Cache file path: {cache_file_path}")

        if reset_cache:
            print("Resetting file cache")
            try:
                cache_file_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as err:
                print(
                    f"Error while deleting file {cache_file_path}, {err=}, {type(err)=}"
                )
                raise

        if use_cache:
            file_cache = FileCache(cache_file_path)
            file_cache.load()
        else:
            file_cache = None

        deploy_files(
            source_root_dir,
            destination_root_dir,
            use_gitignore=use_gitignore,
            delete=delete,
            file_cache=file_cache,
            dry_run=dry_run,
        )

    app()
