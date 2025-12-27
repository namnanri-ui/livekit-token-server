import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from livekit import api

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]


@app.get("/")
async def health():
    return {"status": "ok", "service": "livekit-token-server"}


@app.get("/token")
async def get_token(room: str, identity: str):
    token = api.AccessToken(
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )
    token.identity = identity
    token.ttl = 3600
    token.add_grants(
        api.VideoGrants(
            room=room,
            room_join=True,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
    )
    return {
        "token": token.to_jwt(),
        "url": LIVEKIT_URL,
        "room": room,
        "identity": identity,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
