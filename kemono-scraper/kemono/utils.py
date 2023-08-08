import json
from pathlib import Path
from zipfile import ZipFile

from kemono import settings


def compress_output(jsonl_path: str) -> None:
    # checking if file exists
    jsonl_path = Path(jsonl_path)
    if not jsonl_path.is_file():
        print("File not found.")
        return

    # get files from every entry in jsonl
    file_list = []
    with jsonl_path.open("r", encoding="utf-8") as jsonl_fp:
        for entry in jsonl_fp:
            entry = json.loads(entry)
            html_path = Path(settings.FILES_STORE, entry["html_file"])
            file_list.append(html_path)
            for image in entry["images"]:
                image_path = Path(settings.IMAGES_STORE, image["path"])
                file_list.append(image_path)

    # preparing variables used in the archiving process
    zip_count = 0
    zip_name_template = "kemono-output-{}.zip"
    zip_path = None
    zip_fp = None

    for filename in file_list:
        # create zipfile if not created yet
        if zip_fp is None:
            zip_name = zip_name_template.format(zip_count)
            zip_path = Path(settings.OUTPUT_FOLDER, zip_name)
            zip_fp = ZipFile(zip_path, "w")
            zip_count += 1

        zip_fp.write(filename, arcname=filename.name)

        # check if zip size is over the limit after every write
        max_size_reached = zip_path.stat().st_size > settings.MAX_ARCHIVE_SIZE
        if max_size_reached:
            zip_fp.close()
            zip_fp = None

    # close zipfile if not closed yet
    if zip_fp:
        zip_fp.close()

    # delete images after archiving
    for filename in file_list:
        filename.unlink(missing_ok=True)

    print("Done compressing.")
