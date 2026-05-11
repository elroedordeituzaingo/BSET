import asyncio
import os
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

API_KEY = os.getenv("BRAWL_API_KEY", "")
PLAYER_TAG = os.getenv("PLAYER_TAG", "").replace("#", "%23")
POLL_INTERVAL = 30

session = {
    "ign": "",
    "icon_id": None,
    "current_elo": None,
    "current_rank": "",
    "current_rank_tier": None,
    "history": [],
    "wins": 0,
    "losses": 0,
    "session_delta": 0,
    "initialized": False,
    "error": None,
}


def parse_rank_name(rank_name: str):
    """
    Parsea el nombre oficial de la API tipo "GOLD III"
    y devuelve (key, tier) en minúsculas: ("gold", "III")
    """
    parts = rank_name.strip().split()
    if not parts:
        return None, None
    key = parts[0].lower()  # "gold", "bronze", etc.
    tier = parts[1] if len(parts) > 1 else None
    return key, tier


def extract_elo(data: dict) -> int | None:
    candidates = [
        data.get("rankedElo"),
        data.get("currentRankedSeason", {}).get("score"),
        data.get("currentSeason", {}).get("score"),
        data.get("rankedScore"),
        data.get("rankedPoints"),
    ]
    for v in candidates:
        if v is not None:
            return int(v)
    print("[DEBUG] Could not find ELO. Keys:", list(data.keys()))
    return None


async def poll_loop():
    print(f"[POLL] Starting — {PLAYER_TAG.replace('%23', '#')}")
    while True:
        try:
            url = f"https://api.brawlstars.com/v1/players/{PLAYER_TAG}"
            headers = {"Authorization": f"Bearer {API_KEY}"}
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
                data = r.json()

            rank_name = data.get("rankedRankName")
            elo = data.get("rankedElo")

            if not rank_name or elo is None:
                # fallback por si el jugador no tiene rango ranked activo
                elo = extract_elo(data)
                if elo is None:
                    session["error"] = "Ranked data not found — check server console"
                else:
                    session["error"] = "Player has no active Ranked rank"
            else:
                rank_key, rank_tier = parse_rank_name(rank_name)
                name = data.get("name", "Unknown")
                icon_id = data.get("icon", {}).get("id")

                session["error"] = None
                if icon_id is not None:
                    session["icon_id"] = icon_id

                if not session["initialized"]:
                    session["ign"] = name
                    session["current_elo"] = elo
                    session["current_rank"] = rank_key
                    session["current_rank_tier"] = rank_tier
                    session["initialized"] = True
                    print(
                        f"[INIT] {name} — {elo} pts — {rank_key} {rank_tier or ''} — icon: {icon_id}"
                    )

                elif elo != session["current_elo"]:
                    delta = elo - session["current_elo"]
                    session["history"].append(
                        {
                            "elo": elo,
                            "rank": rank_key,
                            "rank_tier": rank_tier,
                            "delta": delta,
                        }
                    )
                    if len(session["history"]) > 7:
                        session["history"] = session["history"][-7:]
                    session["wins"] += 1 if delta > 0 else 0
                    session["losses"] += 1 if delta < 0 else 0
                    session["session_delta"] += delta
                    session["current_elo"] = elo
                    session["current_rank"] = rank_key
                    session["current_rank_tier"] = rank_tier
                    print(
                        f"[GAME] {delta:+d} → {elo} ({rank_key} {rank_tier or ''}) | "
                        f"{session['wins']}W-{session['losses']}L | "
                        f"Session: {session['session_delta']:+d}"
                    )

        except httpx.HTTPStatusError as e:
            msg = f"HTTP {e.response.status_code}"
            if e.response.status_code == 403:
                msg += " — IP incorrecta en la key?"
            if e.response.status_code == 404:
                msg += " — player tag not found"
            session["error"] = msg
            print(f"[ERROR] {msg}")
        except Exception as e:
            session["error"] = str(e)
            print(f"[ERROR] {e}")

        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not API_KEY or not PLAYER_TAG:
        print("[ERROR] BRAWL_API_KEY o PLAYER_TAG faltantes en .env")
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
async def root():
    return FileResponse("widget.html")


@app.get("/state")
async def get_state():
    return {
        "ign": session["ign"],
        "icon_id": session["icon_id"],
        "current_elo": session["current_elo"],
        "current_rank": session["current_rank"],
        "current_rank_tier": session.get("current_rank_tier"),
        "history": session["history"],
        "wins": session["wins"],
        "losses": session["losses"],
        "session_delta": session["session_delta"],
        "initialized": session["initialized"],
        "error": session["error"],
    }


@app.get("/debug")
async def debug():
    url = f"https://api.brawlstars.com/v1/players/{PLAYER_TAG}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers)
        return r.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=6767, reload=False)
