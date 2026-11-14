from datetime import datetime, timedelta, timezone
from  pwdlib import PasswordHash
import jwt

from app.core.congif import setting
pwd_context = PasswordHash.recommended()


def has_password(password : str)->str:
    return pwd_context.hash(password)

def verify_password(plaint : str, hased : str)-> bool:
    return pwd_context.verify(plaint, hased)

def create_acces_token ( data:dict, minutes : int | None = None)-> str :
    to_encode = data.copy()
    expre = datetime.now(timezone.utc) + timedelta(minutes=setting.JWT_EXPIRES_MIN if minutes is None else minutes)
    to_encode.update({"exp": expre})
    return jwt.encode(to_encode,setting.JWT_SECRET, algorithm=setting.JWT_ALG)

def decode_token ( token :str)->dict:
    return jwt.decode(token,setting.JWT_SECRET, algorithms = [setting.JWT_ALG])
