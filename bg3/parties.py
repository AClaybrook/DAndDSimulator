""" Saved parties (bg3/data/parties.json): build doc builds with gear changes, variants for the trade-offs worked out for them, and the
    takeaways as notes. Members point at doc builds by number, so a re-import of the doc keeps them current """
import json
from copy import deepcopy

from bg3.build import Bg3Build
from bg3.items import DATA

def saved_parties():
    """ [{"name", "notes", "builds": [Bg3Build]}], skipping members whose doc build is gone """
    from bg3.doc_import import load # pylint: disable=import-outside-toplevel
    docs = {d["number"]: d["build"] for d in load()}
    with open(DATA / "parties.json", encoding="utf-8") as f:
        parties = json.load(f)["parties"]
    out = []
    for party in parties:
        builds = []
        for member in party["members"]:
            if member["doc"] not in docs:
                continue
            build = deepcopy(docs[member["doc"]])
            for act, gear in (member.get("equipment") or {}).items():
                build["equipment"][act] = {**build["equipment"].get(act, {}), **gear}
            build["buffs"] = {**build.get("buffs", {}), **(member.get("buffs") or {})}
            build["assumptions"] = {**build.get("assumptions", {}), **(member.get("assumptions") or {})}
            if member.get("boons") and build.get("character"):
                build["character"] = {**build["character"], "boons": member["boons"]}
            build["variants"] = [*build.get("variants", []), *member.get("variants", [])]
            builds.append(Bg3Build.from_dict(build))
        out.append({"name": party["name"], "notes": party.get("notes", []), "builds": builds})
    return out
