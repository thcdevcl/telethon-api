from fastapi import FastAPI

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from pydantic import BaseModel

api_id = 'API_ID'
api_hash = 'API_HASH'
phone = '+PHONE'

class Dispatch(BaseModel):
    to: int
    messages: str

app = FastAPI()

client = TelegramClient(phone, api_id,api_hash)

@app.get("/connect")
async def connect_client():
    await client.connect()
    return {"connected": True}

@app.get("/check")
async def client_authorized():
    if client.is_connected():
        return {"authorized": await client.is_user_authorized(), "connected": True}
    else:
        return {"authorized": False, "connected": True}

@app.get("/send-code")
async def send_code_request():
    return await client.send_code_request(phone)

@app.get("/sign-in/{code}")
async def sign_in(code: str):
    return await client.sign_in(phone, code)

@app.get("/get-dialogs")
async def get_dialogs_request():
    last_date = None
    chunk_size = 200
    result = await client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=chunk_size,
        hash=0
    ))
    return result.chats

@app.get("/get-entity/{id}")
async def get_entity(id: int):
    return await client.get_entity(id)

@app.get("/get-participants/{id}")
async def get_participants(id: int):
    target = await client.get_entity(id)
    return await client.get_participants(target, aggressive=True)

@app.post("/send-message")
async def send_message(dispatch: Dispatch):
    res = await client.send_message(dispatch.to, dispatch.message)
    return res.out

