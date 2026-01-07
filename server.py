import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
WAQI_TOKEN = os.environ.get("WAQI_TOKEN")
LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]

if not WAQI_TOKEN:
    raise RuntimeError("WAQI_TOKEN environment variable is required")

WAQI_BASE_URL = "https://api.waqi.info/feed"

lkapi = api.LiveKitAPI(
    url=LIVEKIT_URL,
    api_key=LIVEKIT_API_KEY,
    api_secret=LIVEKIT_API_SECRET,
)


@app.head("/")
@app.get("/")
async def health():
    return {"status": "ok", "service": "livekit-token-server"}


@app.get("/token")
async def get_token(room: str, identity: str):
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_name(identity) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )).to_jwt()
    
    return {
        "token": token,
        "url": LIVEKIT_URL,
        "room": room,
        "identity": identity,
    }


@app.delete("/room/{room_name}")
async def delete_room(room_name: str):
    try:
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name))
        return {"status": "deleted", "room": room_name}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/aqi")
async def get_aqi(location: str = "here"):
    """
    Fetch air quality data.
    
    - /aqi              → IP 기반 위치 (기본값)
    - /aqi?location=here → IP 기반 위치
    - /aqi?location=seoul → 도시명으로 검색
    """
    url = f"{WAQI_BASE_URL}/{location}/?token={WAQI_TOKEN}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
    
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to reach air quality service")
    
    data = response.json()
    
    if data.get("status") != "ok":
        error_msg = data.get("data", "Unknown error from air quality provider")
        raise HTTPException(status_code=400, detail=error_msg)
    
    aqi_info = data["data"]
    iaqi = aqi_info.get("iaqi", {})
    
    return {
        "aqi": aqi_info.get("aqi", -1),
        "city": aqi_info.get("city", {}).get("name", "Unknown"),
        "time": aqi_info.get("time", {}).get("s", ""),
        "dominant_pollutant": aqi_info.get("dominentpol", ""),
        "pollutants": {
            "pm25": iaqi.get("pm25", {}).get("v"),
            "pm10": iaqi.get("pm10", {}).get("v"),
            "o3": iaqi.get("o3", {}).get("v"),
            "no2": iaqi.get("no2", {}).get("v"),
            "so2": iaqi.get("so2", {}).get("v"),
            "co": iaqi.get("co", {}).get("v"),
        },
        "weather": {
            "temperature": iaqi.get("t", {}).get("v"),
            "humidity": iaqi.get("h", {}).get("v"),
            "pressure": iaqi.get("p", {}).get("v"),
            "wind": iaqi.get("w", {}).get("v"),
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)