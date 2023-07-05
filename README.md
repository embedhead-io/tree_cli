# tree_cli

# Code Review and Enhancement Tool 

This Python-based tool works by compiling the complete codebase of a project into a text file. The output file is intended to be submitted to a Language Learning Model (LLM) for review and potential enhancement suggestions.

## How it Works

The tool walks through your project’s directory structure, parsing and collating all code into a single output file. It’s highly configurable with options such as excluding certain directories, including hidden files, limiting tree depth, and obeying `.gitignore` patterns. This ensures you have fine-grained control over which parts of your codebase are included in the final output.

## Usage

This project includes a command-line interface. Here are the available options:

- `-r`, `—root_dir`: The root directory of the project to analyze. Default is the current directory.
- `-o`, `—output_file`: The file where the code will be written (default: stdout).
- `-d`, `—dir_only`: Set this flag to display directories only (default: false).
- `-f`, `—full_project`: Set this flag to display the full project tree regardless of the script location (default: false).
- `-i`, `—include_hidden`: Set this flag to include hidden files and directories in the output (default: false).
- `-l`, `—limit_depth`: Use this argument to limit the depth of the directory tree (default: no limit).

## Example

The command to generate the codebase of a project might look like this:

```
python3 main.py -r /path/to/your/project -o code_output.txt
```

This command will parse the entire project located at `/path/to/your/project`, and it will write the resulting codebase into a file named `code_output.txt`.

## Contribution

Feel free to submit pull requests to help improve this project!

## License

This project is licensed under the terms of the MIT license.