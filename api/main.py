""" FastAPI app: the JSON API under /api, and the built React front end (frontend/dist) everywhere else.

    uv run uvicorn api.main:app --port 8000     (or: uv run python -m api)
    During front end development, `npm run dev` in frontend/ proxies /api here """
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api import leaderboard, map as act_map, planner, simulator

app = FastAPI(title="D&D Damage Simulator")
app.add_middleware(GZipMiddleware, minimum_size=2000)
ROOT = Path(__file__).parent.parent
DIST = ROOT / "frontend" / "dist"

class Inputs(BaseModel):
    characters: list[dict]
    enemy: dict
    rounds_per_fight: int | None = 3

class Simulation(Inputs):
    graph: str = "DPR Distribution"
    num_rounds: int = Field(10000, ge=1, le=1_000_000)
    sweep_parameter: str = "Armor Class"
    ruleset: str = "bg3"
    seed: int | None = 1

class PresetRequest(BaseModel):
    preset: str
    level: int = Field(5, ge=1, le=20)
    ruleset: str = "bg3"

class TemplateRequest(BaseModel):
    value: str
    ability_stat: str | None = None
    level: int = 1
    ruleset: str = "bg3"

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/simulator/options")
def simulator_options():
    return simulator.options()

@app.get("/api/simulator/default")
def simulator_default():
    return simulator.default_session()

@app.post("/api/simulator/preset")
def simulator_preset(request: PresetRequest):
    return simulator.preset_character(request.preset, request.level, request.ruleset)

@app.get("/api/simulator/enemy")
def simulator_enemy(value: str):
    return simulator.enemy(value)

@app.post("/api/simulator/template")
def simulator_template(request: TemplateRequest):
    return simulator.template_attacks(request.value, request.ability_stat, request.level, request.ruleset)

@app.post("/api/simulator/expected")
def simulator_expected(inputs: Inputs):
    return simulator.expected(inputs.characters, inputs.enemy, inputs.rounds_per_fight)

@app.post("/api/simulator/simulate")
def simulator_simulate(sim: Simulation):
    return simulator.simulate(sim.characters, sim.enemy, sim.graph, sim.num_rounds, sim.rounds_per_fight, sim.sweep_parameter, sim.ruleset, sim.seed)

class VariantRequest(BaseModel):
    character: dict
    key: str

class ExportRequest(Simulation):
    kind: str = "Damage per round"

@app.post("/api/simulator/variant")
def simulator_variant(request: VariantRequest):
    return simulator.variant(request.character, request.key)

@app.post("/api/simulator/export")
def simulator_export(request: ExportRequest):
    csv, problems = simulator.export(request.characters, request.enemy, request.kind, request.num_rounds, request.rounds_per_fight,
                                     request.sweep_parameter, request.ruleset, request.seed)
    if problems:
        raise HTTPException(422, "; ".join(problems))
    name = request.kind.lower().replace(" ", "_")
    return PlainTextResponse(csv, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})

# ---------- Leaderboard

class PartyRequest(BaseModel):
    party: list[dict] = []

class SaveRequest(PartyRequest):
    label: str = ""
    with_variants: bool = False

@app.get("/api/leaderboard/options")
def leaderboard_options():
    return leaderboard.options()

@app.post("/api/leaderboard/entries")
def leaderboard_entries(request: PartyRequest):
    return leaderboard.entries(request.party)

@app.get("/api/leaderboard/runs")
def leaderboard_runs():
    return leaderboard.runs()

@app.get("/api/leaderboard/runs/{run_id}")
def leaderboard_run(run_id: int):
    return leaderboard.run_entries(run_id)

@app.post("/api/leaderboard/save")
def leaderboard_save(request: SaveRequest):
    return leaderboard.save(request.party, request.label, request.with_variants)

@app.get("/api/leaderboard/build/{fingerprint}")
def leaderboard_build(fingerprint: str):
    found = leaderboard.build(fingerprint)
    if found is None:
        raise HTTPException(404, "No saved build with that fingerprint")
    return found

# ---------- Act 1 map

@app.get("/api/map/data")
def map_data():
    return act_map.data()

@app.post("/api/map/party-gear")
def map_party_gear(request: PartyRequest, act: str = "1"):
    return act_map.party_gear(request.party, act)

# ---------- Party planner

class PlannerRequest(PartyRequest):
    enemy: dict | None = None
    rounds_per_fight: int = 3
    attack_bonus: int | None = None

class VariantsRequest(BaseModel):
    build: dict
    enemy: dict | None = None
    rounds_per_fight: int = 3
    enemies: int = 1
    attack_bonus: int = 6

class UseVariantRequest(BaseModel):
    build: dict
    index: int

class KitRequest(PartyRequest):
    selected: int
    kit: str
    act: str = "1"
    skip_taken: bool = True
    only_empty: bool = False

class PartyFightRequest(PlannerRequest):
    act: str = "2"
    active: list[str] | None = None
    hit_points: int = 300

class AdviceRequest(PlannerRequest):
    build: dict
    act: str = "1"
    slot: str = "melee_main"

@app.get("/api/planner/options")
def planner_options():
    return planner.options()

@app.post("/api/planner/evaluate")
def planner_evaluate(request: PlannerRequest):
    return planner.evaluate(request.party, request.enemy, request.rounds_per_fight, request.attack_bonus)

@app.post("/api/planner/variants")
def planner_variants(request: VariantsRequest):
    return planner.variants(request.build, request.enemy, request.rounds_per_fight, request.enemies, request.attack_bonus)

@app.post("/api/planner/use-variant")
def planner_use_variant(request: UseVariantRequest):
    return planner.use_variant(request.build, request.index)

@app.post("/api/planner/kit")
def planner_kit(request: KitRequest):
    return planner.apply_kit_to(request.party, request.selected, request.kit, request.act, request.skip_taken, request.only_empty)

@app.get("/api/planner/example")
def planner_example(name: str):
    found = planner.example(name)
    if found is None:
        raise HTTPException(404, "No example build with that name")
    return found

@app.post("/api/planner/party")
def planner_party(request: PartyFightRequest):
    return planner.party(request.party, request.act, request.active, request.enemy, request.rounds_per_fight, request.hit_points)

class SendRequest(PartyRequest):
    act: str | None = None # Every member at this act, or with selected: one member at every act
    selected: int | None = None

@app.post("/api/planner/to-simulator")
def planner_to_simulator(request: SendRequest):
    return planner.to_simulator(request.party, request.act, request.selected)

@app.post("/api/planner/advice")
def planner_advice(request: AdviceRequest):
    return planner.advice(request.build, request.party, request.act, request.slot, request.enemy, request.rounds_per_fight)

# ---------- The front end

app.mount("/assets/maps", StaticFiles(directory=ROOT / "assets" / "maps"), name="maps") # Before /assets so it wins

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def front_end(path: str):
        """ The single page app: real files as they are, every other path gets index.html (client side routes) """
        target = DIST / path
        return FileResponse(target if path and target.is_file() else DIST / "index.html")
