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


def _delete_images(images: list, images_folder: Path):
    for image in images:
        image_path = images_folder / image
        image_path.unlink()


def run(output_dir: str, jsonl_file: str, images_folder: str):
    jsonl_file = Path(jsonl_file)
    images_folder = Path(images_folder)
    output_dir = Path(output_dir)
    new_output_dir = _init_export_folder(output_dir)
    generations_file = new_output_dir / "generations.json"

    unique_ids = set()
    images_to_delete = []

    with jsonl_file.open("r", encoding="utf-8") as sfp:
        with generations_file.open("w", encoding="utf-8") as dfp:
            for line in sfp:
                generation = json.loads(line)

                no_image = not generation["images"]
                not_downloaded = generation["images"][0]["status"] != "downloaded"
                not_unique_id = generation["id"] in unique_ids
                if no_image or not_downloaded or not_unique_id:
                    continue

                generation = _process_generation(
                    generation, images_folder, new_output_dir
                )
                unique_ids.add(generation["id"])
                dfp.write(json.dumps(generation) + "\n")
                images_to_delete.append(generation["images"][0]["path"])

    shutil.make_archive(
        base_name=str(output_dir / new_output_dir.name),
        format="zip",
        root_dir=new_output_dir,
    )
    _delete_images(images_to_delete, images_folder)
    shutil.rmtree(new_output_dir)
    jsonl_file.unlink()


if __name__ == "__main__":
    import fire

    fire.Fire(run)
