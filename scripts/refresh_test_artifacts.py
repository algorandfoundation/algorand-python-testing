import logging
import multiprocessing
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENV_WITH_NO_COLOR = dict(os.environ) | {
    "NO_COLOR": "1",  # disable colour output
    "PYTHONUTF8": "1",  # force utf8 on windows
}


def get_artifact_folders(root_dir: str) -> Iterator[Path]:
    for folder in Path(root_dir).iterdir():
        if folder.is_dir() and (folder / "contract.py").exists():
            yield folder


def compile_contract(folder: Path) -> None:
    logger.info(f"Compiling: {folder}")
    contract_path = folder / "contract.py"
    (folder / "data").mkdir(exist_ok=True)
    compile_cmd = [
        "hatch",
        "run",
        "puyapy",
        str(contract_path),
        "--out-dir",
        "data",
    ]
    subprocess.run(
        compile_cmd,
        check=True,
        env=ENV_WITH_NO_COLOR,
        encoding="utf-8",
    )


def compile_folder(folder: Path) -> None:
    try:
        compile_contract(folder)
    except subprocess.CalledProcessError:
        logger.exception(f"Error processing folder {folder}")


def main() -> None:
    artifacts_dir = "tests/artifacts"
    folders = list(get_artifact_folders(artifacts_dir))

    with multiprocessing.Pool() as pool:
        try:
            pool.map(compile_folder, folders)
        except Exception:
            logger.exception("An error occurred during parallel processing")


if __name__ == "__main__":
    main()
