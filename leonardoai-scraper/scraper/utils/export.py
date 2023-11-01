import json
from pathlib import Path, PurePosixPath
from datetime import date
import shutil


def _init_export_folder(output_dir: Path) -> Path:
    dir_name = f"leonardo-scraper-export-{date.today().isoformat()}"
    new_dir = output_dir / dir_name
    new_dir.mkdir()
    (new_dir / "images").mkdir()

    return new_dir


def _process_generation(
    generation: dict, images_folder: Path, output_dir: Path
) -> dict:
    image_basename = generation["images"][0]["path"] = PurePosixPath(
        generation["images"][0]["path"]
    ).name
    shutil.copyfile(
        images_folder / image_basename, output_dir / "images" / image_basename
    )

    return generation


def _delete_images(generations: list, images_folder: Path):
    for generation in generations:
        image_path = images_folder / generation["images"][0]["path"]
        image_path.unlink()


def run(output_dir: str, jsonl_file: str, images_folder: str):
    jsonl_file = Path(jsonl_file)
    images_folder = Path(images_folder)
    output_dir = Path(output_dir)
    new_output_dir = _init_export_folder(output_dir)

    generations = []

    with jsonl_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            generation = json.loads(line)
            if (
                not generation["images"]
                or generation["images"][0]["status"] != "downloaded"
            ):
                continue

            generation = _process_generation(generation, images_folder, new_output_dir)
            generations.append(generation)

    generations_file = new_output_dir / "generations.json"
    generations_file.write_text(json.dumps(generations, indent=2, sort_keys=True))
    _delete_images(generations, images_folder)

    shutil.make_archive(
        base_name=str(output_dir / new_output_dir.name),
        format="zip",
        root_dir=new_output_dir,
    )
    shutil.rmtree(new_output_dir)
    jsonl_file.unlink()


if __name__ == "__main__":
    import fire

    fire.Fire(run)
