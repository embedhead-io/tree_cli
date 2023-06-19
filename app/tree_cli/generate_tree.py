import argparse
import os
import pathlib
import pathspec
import sys
from ..utils import load_ignore_patterns

PIPE = "|"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "


class DirectoryTree:
    def __init__(
        self, root_dir, dir_only=False, output_file=sys.stdout, ignore_file=".gitignore"
    ):
        self._ignore_patterns = load_ignore_patterns(root_dir, ignore_file)
        self._output_file = output_file
        self._generator = _TreeGenerator(root_dir, dir_only, self._ignore_patterns)

    def generate(self):
        tree = self._generator.build_tree()
        with (
            open(self._output_file, "w") if self._output_file else sys.stdout
        ) as stream:
            for entry in tree:
                print(entry, file=stream)


class _TreeGenerator:
    def __init__(self, root_dir, dir_only=False, ignore_patterns=[]):
        self._root_dir = pathlib.Path(root_dir)
        self._dir_only = dir_only
        self._ignore_patterns = ignore_patterns
        self._tree = []

    def build_tree(self):
        self._tree_head()
        self._tree_body(self._root_dir)
        return self._tree

    def _tree_head(self):
        self._tree.append(f"{self._root_dir.name}{os.sep}")

    def _tree_body(self, directory, prefix=""):
        entries = self._prepare_entries(directory)
        entries_count = len(entries)
        for index, entry in enumerate(entries):
            connector = ELBOW if index == entries_count - 1 else TEE
            if entry.is_dir():
                if entry.name != "__pycache__":  # Exclude __pycache__ directories
                    self._add_directory(entry, index, entries_count, prefix, connector)
            else:
                self._add_file(entry, prefix, connector)

    def _prepare_entries(self, directory):
        entries = directory.iterdir()

        if self._ignore_patterns:
            spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, self._ignore_patterns
            )
            entries = [
                entry
                for entry in entries
                if not spec.match_file(str(entry.relative_to(self._root_dir)))
            ]

        if self._dir_only:
            entries = [entry for entry in entries if entry.is_dir()]
        else:
            entries = sorted(entries, key=lambda entry: entry.is_file())

        return entries

    def _add_directory(self, directory, index, entries_count, prefix, connector):
        self._tree.append(f"{prefix}{connector} {directory.name}{os.sep}")
        if index != entries_count - 1:
            prefix += PIPE_PREFIX
        else:
            prefix += SPACE_PREFIX
        self._tree_body(directory, prefix)
        self._tree.append(prefix.rstrip())

    def _add_file(self, file, prefix, connector):
        self._tree.append(f"{prefix}{connector} {file.name}")


def find_project_root(path="."):
    """
    Find the root directory of the project by looking for a directory containing a .git directory or file.
    """
    path = pathlib.Path(path).resolve()

    while path != path.parent:  # Stop at the root of the file system
        if (path / ".git").exists() or (path / ".gitignore").exists():
            return str(path)
        path = path.parent

    raise Exception("No project root found")


def run():
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

    args = parser.parse_args()

    # If full_project flag is set, override the root directory
    root_dir = (
        find_project_root() if args.full_project else os.path.abspath(args.root_dir)
    )

    output_file = args.output_file
    dir_only = args.dir_only

    dtree = DirectoryTree(root_dir, dir_only, output_file)
    dtree.generate()


if __name__ == "__main__":
    run()
