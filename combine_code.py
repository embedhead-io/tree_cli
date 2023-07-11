import os
import argparse
import logging
import pathlib
import pathspec

from utils import find_project_root, load_ignore_patterns
from generate_tree import DirectoryTree

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INSTRUCTIONS_FLAG = True
INSTRUCTIONS = """Act as Very Senior Python Engineer ("VSPE").
To start every message, you must:
1) Remind yourself of your Role ("VSPE") and Responsibilities (see below)
2) Produce a summary of the codebase, including:
    a) A description of the project structure
    b) A description of the codebase
    c) A description of the codebase's purpose
3) Produce a summary of the task at hand, including:
    a) A description of the task
    b) A description of the task's purpose
    c) A description of the task's requirements
4) Think aloud as you work through the task
5) Produce the requested deliverable(s) for review

First Task: Read and understand the contents, mechanics, and purpose of the following code as thoroughly and completely as possible. Then, identify areas of potential improvement and/or optimization. Finally, implement the improvements and/or optimizations you identified.

###BEGIN CODE###
"""


def get_output_file(output_dir):
    """
    Generates the output file path.

    :param output_dir: The directory where the output file will be saved.
    :return: A Path object representing the output file path.
    """
    try:
        return pathlib.Path(output_dir) / "combined_code.txt"
    except Exception as e:
        logger.error(f"Error while generating output file path. Error: {str(e)}")
        return None


def combine_files(root_dir, output_dir="./", ignore_file=".gitignore", **kwargs):
    """
    Combine files from root directory into one output file.

    :param root_dir: Root directory from which files are to be combined.
    :param output_dir: Directory where the output file will be stored.
    :param ignore_file: Name of the ignore file (default is .gitignore).
    """
    output_file = get_output_file(output_dir)

    ignore_patterns = load_ignore_patterns(root_dir, ignore_file)
    spec = pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern, ignore_patterns
    )

    directory_tree = DirectoryTree(root_dir, dir_only=False, output_file=output_file)
    directory_tree.generate()

    try:
        with output_file.open("w") as outfile:
            if INSTRUCTIONS_FLAG:
                outfile.write("# Instructions:\n")
                outfile.write(INSTRUCTIONS.strip() + "\n\n")
                outfile.write(f'# {"=" * 80}\n\n')

            outfile.write("# Project Structure:\n")
            formatted_structure = "\n".join(directory_tree._generator._tree)
            outfile.write(formatted_structure + "\n\n")

            for root, dirs, files in os.walk(root_dir):
                relative_root = pathlib.Path(root).relative_to(root_dir)
                for file_name in files:
                    if spec.match_file(str((relative_root / file_name).as_posix())):
                        continue
                    outfile.write(f'\n# {"=" * 80}\n')
                    outfile.write(f"# {relative_root / file_name}\n")
                    outfile.write(f'# {"=" * 80}\n\n')

                    file_path = pathlib.Path(root) / file_name
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        logger.error(
                            f"An error occurred while reading file: {file_path}. Error: {e}"
                        )
            logger.info(f"All code has been combined into {output_file}")
    except IOError as e:
        logger.error(
            f"An error occurred while writing to file: {output_file}. Error: {e}"
        )


def run():
    """
    Parses arguments and runs the combine_files function with the given parameters.
    """
    parser = argparse.ArgumentParser(
        prog="combine_code",
        description="Combine-Code, a tool for analyzing a project structure and combining its code into a single output file.",
    )

    parser.add_argument(
        "-r",
        "--root_dir",
        type=str,
        default=os.getcwd(),
        help="The root directory of the project to analyze. For example, '/path/to/myproject'. (default: current working directory)",
    )

    parser.add_argument(
        "-d",
        "--max_depth",
        type=int,
        default=3,
        help="The maximum depth for traversing the directory tree (default: 3).",
    )

    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default="./",
        help="The directory where the combined code file should be saved (default: './').",
    )

    parser.add_argument(
        "-i",
        "--ignore_file",
        type=str,
        default=".gitignore",
        help="The .gitignore file to use for excluding files and directories (default: '.gitignore').",
    )

    parser.add_argument(
        "-f",
        "--full-project",
        action="store_true",
        default=True,
        help="Perform a full project scan regardless of the location (default: False).",
    )

    args = parser.parse_args()

    root_dir = (
        find_project_root() if args.full_project else os.path.abspath(args.root_dir)
    )
    output_dir = os.path.abspath(args.output_dir)
    ignore_file = args.ignore_file
    max_depth = args.max_depth

    combine_files(root_dir, output_dir, ignore_file, max_depth=max_depth)


if __name__ == "__main__":
    run()
