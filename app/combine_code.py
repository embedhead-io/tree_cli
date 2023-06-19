import os
import argparse
import logging
import pathlib
import pathspec
from .utils import load_ignore_patterns
from .generate_tree import DirectoryTree


INSTRUCTIONS = """
You are a Senior Python Engineer tasked with conducting a comprehensive code review of the provided codebase. Your goal is to identify any issues, provide code improvements, and produce a detailed report of your code review.

Follow these instructions to complete the task:

    Code Review: Go through the codebase line by line, thinking aloud and identifying any issues you encounter. Consider aspects such as code quality, best practices, efficiency, modularity, and error handling.

    Issue Identification: When you identify an issue, briefly explain why you think it is problematic or could be improved. Be specific and provide clear reasoning for each issue.

    Code Improvements: Propose first-draft corrections and improvements for each issue you identified. Provide code blocks to illustrate the suggested changes. Ensure that your improvements address the identified issues effectively.

    Summary of Changes: Write a brief summary outlining the suggested changes you made to the codebase. Summarize the rationale behind each change and how it improves the codebase.

    Self-Critique: Critique your own code and changes. Reflect on the effectiveness of your proposed improvements and consider alternative approaches or potential trade-offs.

    Final Report: Produce a detailed final report of your code review. Include your summary, critique, and all files that were modified as part of your code review. Ensure that the modified files are clearly labeled with the proposed changes incorporated.

For the code review, pay particular attention to the following criteria:

    Code quality: Assess the overall readability, maintainability, and adherence to best practices.
    Modularity: Evaluate the organization of code into modules and the proper separation of concerns.
    Efficiency: Identify any potential performance bottlenecks or areas for optimization.
    Error handling: Assess the robustness of error handling and exception types used.

Feel free to modify the provided code directly and provide code blocks to illustrate your proposed improvements.
"""

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


def combine_files(root_dir, output_dir="./", ignore_file=".gitignore"):
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

    max_depth = args.max_depth
    output_dir = os.path.abspath(args.output_dir)
    ignore_file = args.ignore_file

    combine_files(root_dir, output_dir, ignore_file)


if __name__ == "__main__":
    run()
