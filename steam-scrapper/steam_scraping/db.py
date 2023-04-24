import random

from pysondb import PysonDB

from settings import JOBS_DB_NAME


def filter_by_status(status: str, data: dict) -> bool:
    if data["status"] == status:
        return True


def get_100_random(db: PysonDB):
    apps = db.get_all()
    apps = list(apps.items())
    random_apps = random.choices(apps, k=100)

    return dict(random_apps)


def add_app(db: PysonDB, app_id: str):
    app_id = int(app_id)
    exists = db.get_by_query(lambda data: data["appid"] == app_id)
    if exists:
        return

    app = dict(appid=app_id, status="pending", err_msg="")

    db.add(app)


db = PysonDB(JOBS_DB_NAME)
