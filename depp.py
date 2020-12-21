import ast
import click
import glob
import os
import platform
import subprocess

from poetry.repositories.pypi_repository import PyPiRepository
from typing import List, Iterator


def list_python_files(proj_path: str, venv_name: str) -> Iterator[str]:
    return filter(lambda file_path: venv_name not in file_path, glob.glob(f"{proj_path}/**/*.py", recursive=True))


# Referred to: https://stackoverflow.com/questions/44988487/regex-to-parse-import-statements-in-python#comment90395989_44988778
def list_dependencies(files: Iterator[str]) -> List[str]:
    modules: List[str] = []
    for file in files:
        with open(file) as f:
            for node in ast.walk(ast.parse(f.read())):
                if isinstance(node, ast.ImportFrom):
                    if not node.names[0].asname:  # excluding the 'as' part of import
                        modules.append(node.module)
                elif isinstance(node, ast.Import):  # excluding the 'as' part of import
                    if not node.names[0].asname:
                        modules.append(node.names[0].name)
    return modules


def setup_venv(filtered_dependencies: Iterator[str]) -> None:
    for dependency in filtered_dependencies:
        subprocess.run(f"poetry add {dependency}")


@click.command()
@click.option("--venv_name", default="", help="The name for the directory where the dependencies are installed")
@click.option("--proj_path", default=".", help="The path for the Python project")
def run(venv_name: str, proj_path: str) -> None:
    proj_path_is_dir = os.path.isdir(proj_path)
    proposed_venv_path = f"{proj_path}/{venv_name}"
    venv_is_correct = os.path.isdir(proposed_venv_path)

    if platform.system() == "Windows":
        venv_is_correct = venv_is_correct and os.listdir(proposed_venv_path) == ["Include", "Lib", "pyvenv.cfg", "Scripts"]
    else:
        venv_is_correct = venv_is_correct and os.listdir(proposed_venv_path) == ["include", "lib", "lib64", "bin", "pyvenv.cfg"]

    if not proj_path_is_dir:
        raise Exception(f"{proj_path} is not a directory.")
    if venv_is_correct:
        raise Exception(f"{proj_path} already has a Python virtual environment {venv_name}")

    files = list_python_files(proj_path, venv_name)
    dependencies = list_dependencies(files)
    filtered_dependencies = filter(lambda dependency: PyPiRepository().search(dependency), dependencies)
    setup_venv(filtered_dependencies)


if __name__ == "__main__":
    run()
