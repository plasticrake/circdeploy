import hashlib
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


def calc_project_hash(project_path: Path) -> str:
    """Calculate the hash of a project directory."""
    hasher = hashlib.new("sha1")
    hasher.update(project_path.as_posix().encode("utf-8"))
    return hasher.hexdigest()  # type: ignore[attr-defined]


def calc_file_hash(file_path: Path) -> str:
    """Calculate the hash of a file."""
    hasher = hashlib.new("sha1")
    with Path.open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()  # type: ignore[attr-defined]


class FileCacheEntry:
    __slots__ = ("checksum", "st_mtime", "st_size")

    def __init__(
        self,
        st_mtime: float | None = None,
        st_size: int | None = None,
        checksum: str | None = None,
    ):
        self.st_mtime = st_mtime
        self.st_size = st_size
        self.checksum = checksum

    def __repr__(self):
        return f"FileCacheEntry(st_mtime={self.st_mtime}, st_size={self.st_size},\
            checksum={self.checksum})"

    def update(self, file_path: Path):
        stat = file_path.stat()
        self.st_mtime = stat.st_mtime
        self.st_size = stat.st_size
        self.checksum = calc_file_hash(file_path)
        return self


class FileCache:
    __slots__ = ("cache_path", "file_cache")

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.file_cache: dict[str, FileCacheEntry] = {}

    def load(self) -> None:
        try:
            with Path.open(self.cache_path, "rb") as f:
                self.file_cache.update(pickle.load(f))
        except (OSError, EOFError):
            self.file_cache = {}
        except pickle.UnpicklingError:
            pass

    def _get(self, file_path: Path) -> FileCacheEntry | None:
        key = file_path.as_posix()
        fc = self.file_cache.get(key, None)
        if fc is None:
            return None
        return fc

    def _set(self, file_path: Path) -> None:
        key = file_path.as_posix()
        self.file_cache[key] = FileCacheEntry().update(file_path)

    def update(self, file_path: Path) -> None:
        fc = self._get(file_path)
        if fc is None:
            logger.debug(f"update: creating new entry {file_path}")
            self._set(file_path)
        else:
            logger.debug(f"update: exiting entry {file_path}")
            fc.update(file_path)

    def save(self) -> None:
        # create the directory if it does not exist
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with Path.open(self.cache_path, "wb") as f:
            pickle.dump(self.file_cache, f)

    def check_file_has_changed(self, file_path: Path) -> bool:
        fc = self._get(file_path)
        if fc is None:
            logger.debug(f"check_file_has_changed: File {file_path} cache miss")
            return True

        stat = file_path.stat()

        # Check if the file modification time or size has changed
        if stat.st_mtime != fc.st_mtime or stat.st_size != fc.st_size:
            logger.debug(f"File {file_path} has changed (stat)")
            return True

        # Check if the file checksum has changed
        checksum = calc_file_hash(file_path)
        if checksum != fc.checksum:
            logger.debug(f"File {file_path} has changed (checksum)")
            fc.checksum = checksum
            return True

        return False
