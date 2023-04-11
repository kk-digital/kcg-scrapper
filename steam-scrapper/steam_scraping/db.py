import random

from pysondb import PysonDB


def filter_by_status(status: str, data: dict) -> bool:
    if data['status'] == status:
        return True


def get_100_random(db: PysonDB):
    apps = db.get_all()
    apps = list(apps.items())
    random_apps = random.choices(apps, k=100)

    return dict(random_apps)


db = PysonDB("apps-db.json")
