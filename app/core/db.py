

from typing import Iterator

from sqlmodel import SQLModel, Session, create_engine

from app.core.congif import setting


engine = create_engine(setting.DATABASE_URL, echo = True , commect_arg ={"check_same_thread":False }if "sqlite" in setting.DATABASE_URL else {})

def init_db() -> None:
    SQLModel.metadata.create_all(engine) #dev 
    
    
def get_session()->Iterator[Session]:
    with Session(engine) as session:
        yield session 
