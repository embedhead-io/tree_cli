import pathlib
import logging

logger = logging.getLogger(__name__)


def load_ignore_patterns(root_dir, ignore_file=".gitignore"):
    ignore_file_path = pathlib.Path(root_dir) / ignore_file
    ignore_patterns = []
    try:
        if ignore_file_path.is_file():
            with open(ignore_file_path, "r") as f:
                ignore_patterns = f.read().splitlines()
    except Exception as e:
        logger.error(f"Error while reading file {ignore_file_path}. Error: {str(e)}")
        raise

    return ignore_patterns


def find_project_root(path="."):
    path = pathlib.Path(path).resolve()

    while path != path.parent:  # Stop at the root of the file system
        if (path / ".git").exists() or (path / ".gitignore").exists():
            return str(path)
        path = path.parent

    raise Exception("No project root found")
