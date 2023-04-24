import json

from pysondb import PysonDB

# be careful of running if db is already created, since will purge current db

with open("steamcmd_appid.json", "r", encoding="utf-8") as f:
    apps = json.load(f)["applist"]["apps"]

db = PysonDB("apps-db.json")
db.purge()

for app in apps:
    # 3 possible status pending, complete, failed, partial
    app["status"] = "pending"
    app["err_msg"] = ""

db.add_many(apps)
