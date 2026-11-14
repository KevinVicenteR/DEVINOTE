from sqlmodel import select,Session ,delete

from app.models.share import NoteShere ,LabelShere


class Shererepository:
    def __init__(self,db:Session):
        self.db = db

    def upsert_note_share(self,note_id:int, user_id: int, role: str)->NoteShere:
        share = self.db.exec(select(NoteShere).where(NoteShere.note_id ==note_id, NoteShere.user_id == user_id)).first()

        if share:
            share.role = role
            self.db.add(share)
            self.db.commit()
            self.db.refresh(share)
            return share

        share = NoteShere(note_id = note_id, user_id = user_id , role = role)
        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)
        return share

    def remove_note_shere( self, note_id: int, user_id: int )-> None:
        self.db.exec(delete(NoteShere).where(NoteShere.note_id == note_id,NoteShere.user_id == user_id))

        self.db.commit()


    def upsert_label_share(self,label_id:int, user_id: int, role: str)->LabelShere:
            share = self.db.exec(select(LabelShere).where(LabelShere.label_id ==label_id, LabelShere.user_id == user_id)).first()

            if share:
                share.role = role
                self.db.add(share)
                self.db.commit()
                self.db.refresh(share)
                return share

            share = LabelShere(label_id = label_id, user_id = user_id , role = role)
            self.db.add(share)
            self.db.commit()
            self.db.refresh(share)
            return share

    def remove_label_shere( self, label_id: int, user_id: int )-> None:
            self.db.exec(delete(LabelShere).where(LabelShere.label_id == label_id,LabelShere.user_id == user_id))

            self.db.commit()

    def has_note_shere(self,note_id: int , user_id : int, role:str | None= None)-> bool:
        query = select(NoteShere).where(
            NoteShere.note_id == note_id,
            NoteShere.user_id == user_id
        )

        if role is not None :
            query = query.where( NoteShere.role == role)

        return self.db.exec(query).first() is not None

    def has_any_label_shere(self,label_ids : list[int], user_id : int, role:str | None=None)->bool:
        if not label_ids :
            return False

        query = select(LabelShere).where(LabelShere.label_id.in_(label_ids), LabelShere.user_id ==user_id)

        if role is not None:
            query = query.where(LabelShere.role == role)

        return self.db.exec(query).first() is not None


    def list_note_ids_shered_directly( self, user_id:int )-> list[int]:
        rows = self.db.exec(
            select(NoteShere.note_id).where( NoteShere.user_id == user_id)
        ).all()

        return rows

    def list_label_ids_shared_with_user(self, user_id : int)->list [int]:
        return self.db.exec(select(LabelShere.label_id).where(LabelShere.user_id == user_id)).all()
