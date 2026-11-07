""" FastAPI app: the JSON API under /api, and the built React front end (frontend/dist) everywhere else.

    uv run uvicorn api.main:app --port 8000     (or: uv run python -m api)
    During front end development, `npm run dev` in frontend/ proxies /api here """
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api import simulator

app = FastAPI(title="D&D Damage Simulator")
DIST = Path(__file__).parent.parent / "frontend" / "dist"

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

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def front_end(path: str):
        """ The single page app: real files as they are, every other path gets index.html (client side routes) """
        target = DIST / path
        return FileResponse(target if path and target.is_file() else DIST / "index.html")
