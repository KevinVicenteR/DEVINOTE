

from sqlmodel import SQLModel,Field
from enum import Enum 
from sqlalchemy import UniqueConstraint

class ShereRole(str,Enum):
    READ="reas"
    EDIT = "edit"
    
class NoteShere(SQLModel,table = True):
    __tablename__="note_shere"
    __table_args__ = (UniqueConstraint("note_id", "user_id", name = "uq_note_role"))
    
    id : int =Field(default= None, primary_key= True)
    note_id = int = Field( foreign_key="note.id",index= True)
    user_id = int = Field( foreign_key="user.id",index= True)
    role : ShereRole = Field(default= ShereRole.READ)
    
class LabelShere(SQLModel, table = True):
    __tablename__="label_shere"
    __table_args__ = (UniqueConstraint("label_id", "user_id", name = "uq_label_user"))
        
    id : int =Field(default= None, primary_key= True)
    label_id : int = Field( foreign_key="label.id",index= True)
    user_id : int = Field( foreign_key="user.id",index= True)
    role : ShereRole = Field(default= ShereRole.READ)
    
    
    