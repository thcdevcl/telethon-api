from fastapi import FastAPI, Header

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.sessions import StringSession

import os

# Dict to maintain clients signing in
signing = {}

app = FastAPI()


# Endpoint to do the sign-in . First, just phone is needed, after that, also the code
@app.get("/sign-in")
async def sign_in(*, api_id: str = Header(None), api_hash: str = Header(None), phone: str = Header(None), uid: str = Header(None), session_string: str = Header(None), code: str = Header(None)):
    if not phone:
        return {"error": "No valid phone"}
    if not uid:
        return {"error": "No valid uid"}

    # We save in memory the clients about to sign in. We need the same instance of the client for this
    # TODO - in the future, we should do smth to clean this dict, which will be just emptied when restarting the server
    if not uid in signing.keys():
        client = TelegramClient(None, api_id, api_hash)
        await client.connect()
        signing[uid] = client
    else:
        client = signing[uid]

    if code:
        signed_response = await client.sign_in(phone=phone, code=code)
    else:
        signed_response = await client.sign_in(phone=phone)

    is_user_authorized = await client.is_user_authorized()

    new_session_string = StringSession.save(client.session)

    return {"is_user_authorized":  is_user_authorized, "session_string": new_session_string, "signed_response": signed_response}


# Endpoint to check if the session_string is valid
@app.get("/check")
async def check(*, api_id: str = Header(None), api_hash: str = Header(None), session_string: str = Header(None)):
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    is_user_authorized = await client.is_user_authorized()

    new_session_string = StringSession.save(client.session)

    if is_user_authorized:
        me = await client.get_me()
        return {"authorized": is_user_authorized, "connected": client.is_connected(), "session_string": new_session_string, "me": me}
    else:
        return {"authorized": is_user_authorized, "connected": client.is_connected(), "session_string": new_session_string}


# I'll maintain this endpoint, but it shouldn't be used
@app.get("/send-code")
async def send_code_request(*, api_id: str = Header(None), api_hash: str = Header(None), phone: str = Header(None), uid: str = Header(None)):
    if not phone:
        return {"error": "No valid phone"}
    if not uid:
        return {"error": "No valid uid"}

    client = TelegramClient(None, api_id, api_hash)
    await client.connect()
    signing[uid] = client

    code_request = await client.send_code_request(phone)

    is_user_authorized = await client.is_user_authorized()

    return {"is_user_authorized":  is_user_authorized, "code_request": code_request}


# I'll maintain this endpoint, but it shouldn't be used
@app.get("/verify-code")
async def send_code_request(*, api_id: str = Header(None), api_hash: str = Header(None), phone: str = Header(None), code: str = Header(None), uid: str = Header(None)):
    if not phone:
        return {"error": "No valid phone"}
    if not code:
        return {"error": "No valid code"}
    if not uid:
        return {"error": "No valid uid"}

    if not uid in signing.keys():
        return {"error": "Not sent code for this user"}

    client = signing[uid]

    signed_response = await client.sign_in(phone=phone, code=code)

    is_user_authorized = await client.is_user_authorized()

    new_session_string = StringSession.save(client.session)

    return {"is_user_authorized":  is_user_authorized, "session_string": new_session_string, "signed_response": signed_response}


@app.get("/get-dialogs")
async def get_dialogs_request(*, api_id: str = Header(None), api_hash: str = Header(None), session_string: str = Header(None)):

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    is_user_authorized = await client.is_user_authorized()
    new_session_string = StringSession.save(client.session)

    if is_user_authorized:
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
    else:
        return {"authorized": is_user_authorized, "connected": client.is_connected(), "session_string": new_session_string}


@app.get("/get-entity")
async def get_entity(*, api_id: str = Header(None), api_hash: str = Header(None), session_string: str = Header(None), entity_id: str = Header(None)):
    print(api_id, api_hash, session_string, entity_id)

    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    is_user_authorized = await client.is_user_authorized()
    new_session_string = StringSession.save(client.session)

    if is_user_authorized:
        return await client.get_entity(entity_id)
    else:
        return {"authorized": is_user_authorized, "connected": client.is_connected(), "session_string": new_session_string}


@app.get("/get-participants")
async def get_participants(*, api_id: str = Header(None), api_hash: str = Header(None), session_string: str = Header(None), entity_id: str = Header(None)):
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    is_user_authorized = await client.is_user_authorized()
    new_session_string = StringSession.save(client.session)

    if is_user_authorized:
        target = await client.get_entity(id)
        return await client.get_participants(target, aggressive=True)
    else:
        return {"authorized": is_user_authorized, "connected": client.is_connected(), "session_string": new_session_string}


@app.post("/send-message")
async def send_message(*, api_id: str = Header(None), api_hash: str = Header(None), session_string: str = Header(None), to: str = Header(None), message: str = Header(None)):
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()

    is_user_authorized = await client.is_user_authorized()
    new_session_string = StringSession.save(client.session)

    if is_user_authorized:
        res = await client.send_message(to, message)
        return res.out
    else:
        return {"authorized": is_user_authorized, "connected": client.is_connected(), "session_string": new_session_string}
