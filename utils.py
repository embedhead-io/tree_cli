import pathlib
import logging

logger = logging.getLogger(__name__)


def load_ignore_patterns(root_dir, ignore_file=".gitignore"):
    """
    Loads patterns to be ignored during tree generation.

    :param root_dir: Root directory of the project.
    :param ignore_file: File containing ignore patterns (default is .gitignore).
    :returns: List of patterns to be ignored.
    :raises Exception: If an error occurs while reading the file.
    """
    # Construct the full ignore file path
    ignore_file_path = pathlib.Path(root_dir) / ignore_file
    ignore_patterns = []

    try:
        # If the ignore file is a file, read and split its lines into patterns
        if ignore_file_path.is_file():
            with open(ignore_file_path, "r") as f:
                ignore_patterns = f.read().splitlines()
    except Exception as e:
        # Log error and re-raise if an error occurs during file reading
        logger.error(f"Error while reading file {ignore_file_path}. Error: {str(e)}")
        raise

    return ignore_patterns


def find_project_root(path="."):
    """
    Finds the root directory of the project by looking for a directory containing a .git directory or file.

    :param path: The path where to start looking for the project root. Default is current directory.
    :returns: Absolute path of the project root directory.
    :raises Exception: If no project root found.
    """
    # Resolve the absolute path
    path = pathlib.Path(path).resolve()

    # Loop up the directory tree until the root of the file system is reached
    while path != path.parent:
        # If a .git directory or .gitignore file is found, this directory is the project root
        if (path / ".git").exists() or (path / ".gitignore").exists():
            return str(path)
        # Move one level up in the directory tree
        path = path.parent

    # If no project root was found, raise an exception
    raise Exception("No project root found")
