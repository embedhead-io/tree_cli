import os
import argparse
import logging
import pathlib
import pathspec
from utils import find_project_root, load_ignore_patterns
from generate_tree import DirectoryTree

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
INSTRUCTIONS_FLAG = False
INSTRUCTIONS = """
Act as a Python Engineer. Navigate to the bottom of this message, then read from the bottom up. Produce a summary of what you have read. THEN, POPULATE THE unpack_code.py AND unpack_struc.py so that unpack_struc.py unpacks the project structure from combined_code.txt (contained in the project tree at the top of the file) into the working directory, where the highest level directory is the folder created. Then, once the subfolders have also been created, create ALL of the code files in ALL of the folders within the project, complete with their code. The files are named between lines of hash symbols and the code for each is BELOW the title. Begin:
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
                outfile.write(
                    "# Instructions:\n"
                    + INSTRUCTIONS.strip()
                    + "\n\n"
                    + f'# {"=" * 80}\n\n'
                )

            outfile.write(f'# {"=" * 80}\n# Project Structure:\n# {"=" * 80}\n\n')
            formatted_structure = "\n".join(directory_tree._generator._tree)
            outfile.write(formatted_structure + "\n\n")

            for root, dirs, files in os.walk(root_dir):
                relative_root = pathlib.Path(root).relative_to(root_dir)
                for file_name in files:
                    if spec.match_file(str((relative_root / file_name).as_posix())):
                        continue
                    outfile.write(
                        f'\n# {"=" * 80}\n# {relative_root / file_name}\n# {"=" * 80}\n\n'
                    )
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
        "--full_project",
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

    combine_files(root_dir, output_dir, ignore_file)


if __name__ == "__main__":
    run()
