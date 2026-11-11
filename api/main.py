""" FastAPI app: the JSON API under /api, and the built React front end (frontend/dist) everywhere else.

    uv run uvicorn api.main:app --port 8000     (or: uv run python -m api)
    During front end development, `npm run dev` in frontend/ proxies /api here """
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api import leaderboard, map as act_map, planner, schemas, simulator

app = FastAPI(title="D&D Damage Simulator")
# A hosted copy is shared by its visitors, so nothing they send may change what the others see: set DAMAGE_LAB_READ_ONLY=1 there
READ_ONLY = os.environ.get("DAMAGE_LAB_READ_ONLY", "").lower() in ("1", "true", "yes")

def writable(what):
    if READ_ONLY:
        raise HTTPException(403, f"{what} is switched off on this shared copy. Run the app on your own machine to use it")

app.add_middleware(GZipMiddleware, minimum_size=2000)
ROOT = Path(__file__).parent.parent
DIST = ROOT / "frontend" / "dist"

def stale_front_end():
    """ Whether the built front end (frontend/dist, not in git) is older than its source, i.e. after pulling new code without building """
    built, source = DIST / "index.html", ROOT / "frontend" / "src"
    if not built.exists() or not source.exists():
        return False
    return max((p.stat().st_mtime for p in source.rglob("*") if p.is_file()), default=0) > built.stat().st_mtime + 1

STALE = stale_front_end()
if STALE:
    print("\n  The built front end is older than its source. Rebuild it:  cd frontend && npm install && npm run build\n")

@app.get("/api/status")
def status():
    return {"staleFrontEnd": STALE}

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

@app.get("/api/simulator/options", response_model=schemas.SimulatorOptions)
def simulator_options():
    return simulator.options()

@app.get("/api/simulator/default", response_model=schemas.Session)
def simulator_default():
    return simulator.default_session()

@app.post("/api/simulator/preset", response_model=schemas.Loose)
def simulator_preset(request: PresetRequest):
    return simulator.preset_character(request.preset, request.level, request.ruleset)

@app.get("/api/simulator/enemy", response_model=schemas.Loose)
def simulator_enemy(value: str):
    return simulator.enemy(value)

@app.post("/api/simulator/template", response_model=list[schemas.Loose])
def simulator_template(request: TemplateRequest):
    return simulator.template_attacks(request.value, request.ability_stat, request.level, request.ruleset)

@app.post("/api/simulator/expected", response_model=schemas.Expected, response_model_exclude_unset=True)
def simulator_expected(inputs: Inputs):
    return simulator.expected(inputs.characters, inputs.enemy, inputs.rounds_per_fight)

@app.post("/api/simulator/simulate", response_model=schemas.SimulationResult, response_model_exclude_unset=True)
def simulator_simulate(sim: Simulation):
    return simulator.simulate(sim.characters, sim.enemy, sim.graph, sim.num_rounds, sim.rounds_per_fight, sim.sweep_parameter, sim.ruleset, sim.seed)

class VariantRequest(BaseModel):
    character: dict
    key: str

class ExportRequest(Simulation):
    kind: str = "Damage per round"

@app.post("/api/simulator/variant", response_model=schemas.VariantResult, response_model_exclude_unset=True)
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
    party: list[schemas.Build] = []

    def builds(self):
        """ The party as plain dictionaries, which the planner modules read """
        return [b.model_dump(mode="json") for b in self.party]

class SaveRequest(PartyRequest):
    label: str = ""
    with_variants: bool = False

@app.get("/api/leaderboard/options", response_model=schemas.LeaderboardOptions)
def leaderboard_options():
    return {**leaderboard.options(), "readOnly": READ_ONLY}

@app.post("/api/leaderboard/entries", response_model=list[schemas.LeaderboardEntry])
def leaderboard_entries(request: PartyRequest):
    return leaderboard.entries(request.builds())

@app.get("/api/leaderboard/runs", response_model=list[schemas.Run])
def leaderboard_runs():
    return leaderboard.runs()

@app.get("/api/leaderboard/runs/{run_id}", response_model=list[schemas.LeaderboardEntry])
def leaderboard_run(run_id: int):
    return leaderboard.run_entries(run_id)

@app.post("/api/leaderboard/save", response_model=schemas.Saved)
def leaderboard_save(request: SaveRequest):
    writable("Saving leaderboard runs")
    return leaderboard.save(request.builds(), request.label, request.with_variants)

@app.get("/api/leaderboard/build/{fingerprint}")
def leaderboard_build(fingerprint: str):
    found = leaderboard.build(fingerprint)
    if found is None:
        raise HTTPException(404, "No saved build with that fingerprint")
    return found

# ---------- Act 1 map

@app.get("/api/map/data", response_model=schemas.MapData)
def map_data():
    return act_map.data()

@app.post("/api/map/party-gear", response_model=list[schemas.PartyGear])
def map_party_gear(request: PartyRequest, act: str = "1"):
    return act_map.party_gear(request.builds(), act)

# ---------- Party planner

class PlannerRequest(PartyRequest):
    enemy: dict | None = None
    rounds_per_fight: int = 3
    attack_bonus: int | None = None
    synergies: bool = False # Damage against the enemy as the party's every-fight synergies leave it

class VariantsRequest(BaseModel):
    build: schemas.Build
    party: list[schemas.Build] = []
    synergies: bool = False
    enemy: dict | None = None
    rounds_per_fight: int = 3
    enemies: int = 1
    attack_bonus: int = 6

class UseVariantRequest(BaseModel):
    build: schemas.Build
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
    build: schemas.Build
    act: str = "1"
    slot: str = "melee_main"

@app.get("/api/planner/options", response_model=schemas.PlannerOptions)
def planner_options():
    return {**planner.options(), "readOnly": READ_ONLY}

@app.post("/api/planner/evaluate", response_model=schemas.Evaluation)
def planner_evaluate(request: PlannerRequest):
    return planner.evaluate(request.builds(), request.enemy, request.rounds_per_fight, request.attack_bonus)

@app.post("/api/planner/variants", response_model=list[schemas.VariantRow])
def planner_variants(request: VariantsRequest):
    return planner.variants(request.build.model_dump(mode="json"), request.enemy, request.rounds_per_fight, request.enemies, request.attack_bonus,
                            [b.model_dump(mode="json") for b in request.party], request.synergies)

@app.post("/api/planner/use-variant", response_model=schemas.Build)
def planner_use_variant(request: UseVariantRequest):
    return planner.use_variant(request.build.model_dump(mode="json"), request.index)

@app.post("/api/planner/kit", response_model=schemas.KitResult)
def planner_kit(request: KitRequest):
    return planner.apply_kit_to(request.builds(), request.selected, request.kit, request.act, request.skip_taken, request.only_empty)

class BestGearRequest(PlannerRequest):
    selected: int
    acts: list[str] = ["3"]
    goal: str = "damage" # damage, ac or score
    enemies: int = 1
    weapons: bool = True
    skip_taken: bool = True
    keep_uncounted: bool = True # Worn items with effects the damage doesn't count are harder to swap out

@app.post("/api/planner/best-gear", response_model=schemas.BestGear)
def planner_best_gear(request: BestGearRequest):
    return planner.best_gear_for(request.builds(), request.selected, request.acts, request.goal, request.enemy, request.rounds_per_fight,
                                 request.enemies, request.attack_bonus, request.weapons, request.skip_taken, request.synergies, request.keep_uncounted)

@app.post("/api/planner/deconflict", response_model=schemas.Deconflict)
def planner_deconflict(request: PlannerRequest):
    return planner.deconflict(request.builds(), request.enemy, request.rounds_per_fight)

@app.get("/api/planner/example", response_model=schemas.Build)
def planner_example(name: str):
    found = planner.example(name)
    if found is None:
        raise HTTPException(404, "No example build with that name")
    return found

@app.post("/api/planner/party", response_model=schemas.PartyAnalysis)
def planner_party(request: PartyFightRequest):
    return planner.party(request.builds(), request.act, request.active, request.enemy, request.rounds_per_fight, request.hit_points)

class ImportRequest(BaseModel):
    source: str # A link to the build reference document

@app.post("/api/planner/import-doc", response_model=schemas.ImportResult, response_model_exclude_unset=True)
def planner_import_doc(request: ImportRequest):
    writable("Importing a build document")
    return planner.import_doc(request.source.strip())

class SendRequest(PartyRequest):
    act: str | None = None # Every member at this act, or with selected: one member at every act
    selected: int | None = None

@app.post("/api/planner/to-simulator", response_model=list[schemas.Loose])
def planner_to_simulator(request: SendRequest):
    return planner.to_simulator(request.builds(), request.act, request.selected)

@app.post("/api/planner/advice", response_model=schemas.Advice)
def planner_advice(request: AdviceRequest):
    return planner.advice(request.build.model_dump(mode="json"), request.builds(), request.act, request.slot, request.enemy, request.rounds_per_fight, request.synergies)

# ---------- The front end

app.mount("/assets/maps", StaticFiles(directory=ROOT / "assets" / "maps"), name="maps") # Before /assets so it wins

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def front_end(path: str):
        """ The single page app: real files as they are, every other path gets index.html (client side routes) """
        target = DIST / path
        return FileResponse(target if path and target.is_file() else DIST / "index.html")
