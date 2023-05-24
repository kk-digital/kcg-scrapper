import os
import re
import shutil
from os import path

import typer

import settings
from steam_scraping.db import db, add_app

app = typer.Typer()


@app.command()
def clean_db_and_output():
    db.purge()
    shutil.rmtree("output", ignore_errors=True)
    print("DB purged and output folder deleted.")


@app.command()
def extract_apps(file: str):
    file_exists = path.isfile(file)
    if not file_exists:
        print("Could not find file.")
        raise typer.Exit()

    with open(file, "r", encoding="utf-8") as fh:
        file_content = fh.read()

    regex = r"https://store\.steampowered\.com/app/(\d+)"
    matches = re.findall(regex, file_content)
    app_ids = list(set(matches))

    for app_id in app_ids:
        add_app(db, app_id)

    print("Apps added.")


@app.command()
def compress_output():
    while True:
        proceed = input(
            "The output folder location specified in settings will be used. Proceed? (y/n): "
        )
        if proceed == "y":
            break
        elif proceed == "n":
            raise typer.Exit()

    print("Compressing, please wait.")

    zip_dest = path.join(settings.OUTPUT_FOLDER, "compressed-apps")
    os.makedirs(zip_dest, exist_ok=True)
    for file in os.listdir(settings.FILES_STORE):
        zip_name = path.join(zip_dest, file)
        shutil.make_archive(
            base_name=zip_name,
            format="zip",
            root_dir=settings.FILES_STORE,
            base_dir=file,
        )
        shutil.rmtree(path.join(settings.FILES_STORE, file))

    for file in os.listdir(zip_dest):
        zip_file = path.join(zip_dest, file)
        new_dest = path.join(settings.FILES_STORE, file)
        shutil.move(src=zip_file, dst=new_dest)

    shutil.rmtree(zip_dest)

    print(f"Done. Check {zip_dest}.")


if __name__ == "__main__":
    app()
