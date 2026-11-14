from fastapi import HTTPException

from app.core.security import create_acces_token, has_password, verify_password
from app.repositories.user_repository import UserRepository,User
from app.models.Users import UserCreate



class AuthService :
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def register(self,payload : UserCreate)->User:
        if self.repo.get_by_email(payload.email):
            raise HTTPException( status_code= 400 , detail="Email ya registado")

        user = User(
            email = payload.email,
            full_name = payload.full_name,
            hashed_password= has_password( payload.password)
        )

        return self.repo.create(user)

    def login(self, email: str, password : str)-> str :
        user = self.repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code= 401, detail= "credenciales invalidas")

        token = create_acces_token({"sub": str(user.id)})

        return token
