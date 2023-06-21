import os
import argparse
import logging
import pathlib
import pathspec
from utils import load_ignore_patterns
from generate_tree import DirectoryTree


INSTRUCTIONS = """
Act as a Very Senior Python Engineer. Review the provided codebase line-by-line, file-by-file. Produce complete, corrected files, with any and all improvements, corrections, etc., implemented fully and accurately. Your primary goal is to identify any issues, propose code improvements, and generate a detailed report of your code review findings. As part of this task, you are expected to produce complete, accurate code snippets and files to illustrate your suggestions for improvement.

To successfully complete this task, please follow these steps:

1. **Code Review**: Go through the codebase line by line, verbally annotating your thought process, and identifying any potential issues. Pay close attention to code quality, adherence to best practices, efficiency, modularity, and error handling.

2. **Issue Identification**: When you come across an issue, briefly explain why it's problematic or where it could be improved. Be precise and provide clear reasoning for each issue you identify.

3. **Code Improvements**: For every problem you identify, propose a first-draft correction or improvement. To help clarify your suggestions, provide complete code snippets or full files that demonstrate the recommended changes. It's essential that your improvements effectively address the issues you've pinpointed.

4. **Summary of Changes**: Compose a concise summary that outlines the changes you've suggested for the codebase. For each change, summarize the reasoning behind it and explain how it improves the codebase.

5. **Self-Critique**: Critically evaluate your own code and proposed changes. Reflect on the effectiveness of your suggestions and consider potential alternative approaches or trade-offs.

6. **Final Report**: Produce a comprehensive final report of your code review. Include your summary, critique, and any modified files resulting from your code review. Be sure to clearly label the modified files and incorporate your suggested changes.

Throughout the code review, focus on these key areas:

- **Code quality**: Assess the overall readability, maintainability, and adherence to best practices.
- **Modularity**: Examine the organization of code into modules and the proper separation of concerns.
- **Efficiency**: Identify any potential performance bottlenecks or areas for optimization.
- **Error handling**: Evaluate the robustness of error handling mechanisms and the appropriateness of the exception types used.

At the beginning of each response you send back to me, you will: 1) State your title; 2) Produce a succint, accurate summary of the project, the task at hand, and the progress you have made thus far; and 3) Produce a clear, concise list of the next steps you plan to take, why you plan to take them, and how you plan to take them. You will then proceed to complete the next steps you have outlined, and repeat this process until the task is complete. Please return all of your work to me in code blocks and snippets, each representing one of the files contained in the codebase below. Please begin!
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
