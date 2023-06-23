import os
import argparse
import logging
import pathlib
import pathspec
from utils import load_ignore_patterns
from generate_tree import DirectoryTree


INSTRUCTIONS_1 = """
Act as a Very Senior Python Engineer. Your goal is to review the provided codebase and generate a comprehensive report of your findings. You should identify issues, propose improvements, and provide corrected code snippets or files. Follow these steps:

0. **Project Summary (File-by-File)**: Provide a brief summary of each file in the codebase. Then, provide a detailed summary of the project as a whole. Include the project's purpose, the technologies used, and any other relevant information.

1. **Code Review and Issue Identification**: Review the code line by line, paying attention to code quality, modularity, efficiency, and error handling. As you identify potential issues, explain why they are problematic or how they could be improved.

2. **Code Improvements**: Propose and illustrate improvements for every problem you identify. Provide corrected code snippets or full files.

3. **Summary of Changes**: Summarize the changes you've suggested and explain how they improve the codebase.

4. **Self-Critique**: Reflect on the effectiveness of your suggestions. Consider alternative approaches or trade-offs.

5. **Final Report**: Produce a comprehensive final report, including your summary, critique, and any modified files.

Do not lose focus, and continually remind yourself of the goal: to improve the codebase. You are not expected to be familiar with every library or technology used in the codebase. If you are unfamiliar with a library or technology, you should still be able to identify issues and propose improvements.
"""

# This is the text that will be written to the top of the output file.
INSTRUCTIONS = INSTRUCTIONS_1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_output_file(output_dir):
    """
    This function generates the output file path.

    :param output_dir: The directory where the output file will be saved.
    :return: A Path object representing the output file path.
    """
    try:
        return pathlib.Path(output_dir) / "combined_code.txt"
    except Exception as e:
        print(f"Error while generating output file path. Error: {str(e)}")
        return None


def combine_files(root_dir, output_dir="./", ignore_file=".gitignore", **kwargs):
    output_file = get_output_file(output_dir)

    ignore_patterns = load_ignore_patterns(root_dir, ignore_file)

    spec = pathspec.PathSpec.from_lines(
        pathspec.patterns.GitWildMatchPattern, ignore_patterns
    )

    directory_tree = DirectoryTree(root_dir, dir_only=False, output_file=output_file)
    directory_tree.generate()
    formatted_structure = "\n".join(directory_tree._generator._tree)

    try:
        with output_file.open("w") as outfile:
            outfile.write("# Instructions:\n")
            outfile.write(INSTRUCTIONS.strip() + "\n\n")
            outfile.write(f'# {"=" * 80}\n\n')

            outfile.write("# Project Structure:\n")
            outfile.write(formatted_structure + "\n\n")

            for root, dirs, files in os.walk(root_dir):
                relative_root = pathlib.Path(root).relative_to(root_dir)
                for file_name in files:
                    file_path = pathlib.Path(root) / file_name
                    if spec.match_file(str(file_path.relative_to(root_dir))):
                        continue
                    outfile.write(f'\n# {"=" * 80}\n')
                    outfile.write(f"# {relative_root / file_name}\n")
                    outfile.write(f'# {"=" * 80}\n\n')
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as infile:
                            outfile.write(infile.read())
                    except Exception as e:  # broaden exception handling
                        logger.error(
                            f"An error occurred while reading file: {file_path}. Error: {e}"
                        )
            logger.info(f"All code has been combined into {output_file}")
    except IOError as e:
        logger.error(
            f"An error occurred while writing to file: {output_file}. Error: {e}"
        )


def find_project_root():
    cur_dir = os.getcwd()

    while True:
        if os.path.exists(os.path.join(cur_dir, ".git")) or os.path.exists(
            os.path.join(cur_dir, ".gitignore")
        ):
            return cur_dir
        else:
            parent_dir = os.path.dirname(cur_dir)
            if parent_dir == cur_dir:
                raise Exception("No project root found")
            cur_dir = parent_dir


def run():
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
