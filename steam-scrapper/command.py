import re
import shutil
from os import path

import typer

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


if __name__ == "__main__":
    app()
