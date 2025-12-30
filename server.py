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

# ✅ LiveKit API 클라이언트
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
    
    # 토큰 생성
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


# ✅ Room 삭제 API (선택사항 - Swift에서 직접 호출 가능)
@app.delete("/room/{room_name}")
async def delete_room(room_name: str):
    try:
        await lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name))
        return {"status": "deleted", "room": room_name}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)