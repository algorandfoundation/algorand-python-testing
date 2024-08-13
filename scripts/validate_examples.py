import logging
import multiprocessing
import os
import shutil
import subprocess
import tempfile
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
        if folder.is_dir() and (
            (folder / "contract.py").exists() or (folder / "signature.py").exists()
        ):
            yield folder


def compile_contract(folder: Path) -> Path:
    logger.info(f"Compiling: {folder}")
    contract_path = folder / "contract.py"
    if not contract_path.exists():
        contract_path = folder / "signature.py"
    out_dir = tempfile.mkdtemp()
    compile_cmd = [
        "hatch",
        "run",
        "puyapy",
        str(contract_path),
        "--out-dir",
        out_dir,
    ]
    subprocess.run(
        compile_cmd,
        check=True,
        env=ENV_WITH_NO_COLOR,
        encoding="utf-8",
    )
    return Path(out_dir)


def generate_client(folder: Path) -> None:
    logger.info(f"Generating typed client for: {folder}")
    client_path = folder / "client.py"
    generate_cmd = [
        "algokit",
        "generate",
        "client",
        str(folder),
        "--language",
        "python",
        "--output",
        str(client_path),
    ]
    try:
        subprocess.run(
            generate_cmd,
            check=True,
            env=ENV_WITH_NO_COLOR,
            encoding="utf-8",
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if "No app specs" in e.stderr:
            logger.warning(f"No app spec found for: {folder}, skipping...")
        else:
            raise


def process_folder(folder: Path) -> None:
    try:
        out_dir = compile_contract(folder)
        generate_client(out_dir)
        shutil.rmtree(out_dir)
    except subprocess.CalledProcessError:
        logger.exception(f"Error processing folder {folder}")


def main() -> None:
    artifacts_dir = "examples"
    folders = list(get_artifact_folders(artifacts_dir))

    with multiprocessing.Pool() as pool:
        try:
            pool.map(process_folder, folders)
        except Exception:
            logger.exception("An error occurred during parallel processing")


if __name__ == "__main__":
    main()
