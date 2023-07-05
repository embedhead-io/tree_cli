import argparse
import os
import pathlib
import pathspec
import sys
from utils import load_ignore_patterns

# Constants to define tree structure
PIPE = "|"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "


class DirectoryTree:
    """
    Class to represent a directory tree.

    Attributes:
        _ignore_patterns: List of patterns to be ignored during tree generation.
        _output_file: File where the tree will be printed. If None, tree will be printed on console.
        _include_hidden: Boolean to decide if hidden files/directories should be included.
        _limit_depth: The maximum depth of tree. If None, full depth will be covered.
        _generator: Instance of _TreeGenerator class to generate directory tree.
    """
    def __init__(
        self, root_dir, dir_only=False, include_hidden=False, limit_depth=None, output_file=sys.stdout, ignore_file=".gitignore"
    ):
        # Load ignore patterns, if any
        self._ignore_patterns = load_ignore_patterns(root_dir, ignore_file)
        self._output_file = output_file
        self._include_hidden = include_hidden
        self._limit_depth = limit_depth

        # Instantiate _TreeGenerator class with necessary parameters
        self._generator = _TreeGenerator(root_dir, dir_only, self._ignore_patterns, self._include_hidden, self._limit_depth)

    def generate(self):
        """Method to generate the directory tree"""
        tree = self._generator.build_tree()

        # Write to either output file or stdout
        with (
            open(self._output_file, "w") if self._output_file else sys.stdout
        ) as stream:
            for entry in tree:
                print(entry, file=stream)


class _TreeGenerator:
    """
    Class to generate a directory tree.

    Attributes:
        _root_dir: Root directory for tree generation.
        _dir_only: Boolean to decide if only directories should be included in tree.
        _ignore_patterns: List of patterns to be ignored during tree generation.
        _include_hidden: Boolean to decide if hidden files/directories should be included.
        _limit_depth: The maximum depth of tree. If None, full depth will be covered.
        _tree: List where the tree elements will be stored.
    """
    def __init__(self, root_dir, dir_only=False, ignore_patterns=[], include_hidden=False, limit_depth=None):
        self._root_dir = pathlib.Path(root_dir)
        self._dir_only = dir_only
        self._ignore_patterns = ignore_patterns
        self._include_hidden = include_hidden
        self._limit_depth = limit_depth
        self._tree = []

    def _tree_head(self):
        """Append root directory name to the tree list."""
        self._tree.append(f"{self._root_dir.name}{os.sep}")

    def _tree_body(self, directory, prefix="", depth=0):
        """Recursively scan the directories and files and append them to the tree list."""
        if self._limit_depth is not None and depth > self._limit_depth:
            return

        entries = self._prepare_entries(directory)
        entries_count = len(entries)

        for index, entry in enumerate(entries):
            connector = ELBOW if index == entries_count - 1 else TEE

            if entry.is_dir():
                if entry.name != "__pycache__":  # Exclude __pycache__ directories
                    self._add_directory(entry, index, entries_count, prefix, connector)
            elif not self._dir_only:  # If not directory-only mode, add files as well
                self._add_file(entry, prefix, connector)

    def _add_file(self, file, prefix, connector):
        """
        Add a file to the tree list.

        :param file: File to be added.
        :param prefix: Prefix to be added before the file name.
        :param connector: Connector to be added before the file name.
        """
        self._tree.append("{}{} {}".format(prefix, connector, file.name))

    def _prepare_entries(self, directory):
        """Prepare the entries (files/directories) to be added to the tree."""
        entries = directory.iterdir()

        # Exclude hidden files/directories if not included
        if not self._include_hidden:
            entries = [entry for entry in entries if not entry.name.startswith('.')]

        # Exclude ignored files/directories based on .gitignore
        if self._ignore_patterns:
            spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, self._ignore_patterns)
            entries = [entry for entry in entries if not spec.match_file(str(entry.relative_to(self._root_dir)))]

        return sorted(entries, key=lambda entry: entry.is_file())

    def _add_directory(self, directory, index, entries_count, prefix, connector):
        """Add a directory to the tree list and recursively add its files and directories."""
        self._tree.append(f"{prefix}{connector} {directory.name}{os.sep}")

        if index != entries_count - 1:
            prefix += PIPE_PREFIX
        else:
            prefix += SPACE_PREFIX

        # Continue with the body of the directory
        self._tree_body(directory, prefix, depth=depth+1)
        self._tree.append(prefix.rstrip())


def find_project_root(path="."):
    """
    Find the root directory of the project by looking for a directory containing a .git directory or file.

    :param path: The path where to start looking for the project root. Default is current directory.
    :returns: Absolute path of the project root directory.
    :raises Exception: If no project root found.
    """
    path = pathlib.Path(path).resolve()

    while path != path.parent:  # Stop at the root of the file system
        if (path / ".git").exists() or (path / ".gitignore").exists():
            return str(path)
        path = path.parent

    raise Exception("No project root found")


def run():
    """
    Main function to run the script. Parses arguments, prepares required parameters and runs directory tree generation.
    """
    parser = argparse.ArgumentParser(
        prog="DirectoryTree",
        description="DirectoryTree, a tool for visualizing a directory structure.",
    )

    # Make root_dir an optional argument instead of positional
    parser.add_argument(
        "-r",
        "--root_dir",
        type=str,
        default=".",  # Default to the current directory
        help="The root directory of the project to analyze.",
    )

    # Optional argument for the output file
    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        help="The file where the directory structure should be written (default: stdout).",
    )

    # Optional argument to show directories only
    parser.add_argument(
        "-d",
        "--dir_only",
        action="store_true",
        help="Set this flag to display directories only (default: false).",
    )

    # Optional argument to show full project
    parser.add_argument(
        "-f",
        "--full_project",
        action="store_true",
        default=True,
        help="Set this flag to display the full project tree regardless of the script location (default: false).",
    )

    # Optional argument to include hidden files
    parser.add_argument(
        "-i",
        "--include_hidden",
        action="store_true",
        help="Set this flag to include hidden files and directories in the output (default: false).",
    )

    # Optional argument to limit tree depth
    parser.add_argument(
        "-l",
        "--limit_depth",
        type=int,
        help="Use this argument to limit the depth of the directory tree (default: no limit).",
    )

    args = parser.parse_args()


    # If full_project flag is set, override the root directory
    root_dir = (
        find_project_root() if args.full_project else os.path.abspath(args.root_dir)
    )

    output_file = args.output_file
    dir_only = args.dir_only

    dtree = DirectoryTree(root_dir, dir_only, args.include_hidden, args.limit_depth, output_file)
    dtree.generate()


if __name__ == "__main__":
    run()
