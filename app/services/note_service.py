from sqlmodel import Session

from app.models.share import ShereRole
from app.repositories.label_repository import LabelRepository
from app.repositories.note_repository import NoteRepository,Note
from app.repositories.shere_repository import Shererepository


class NoteService :
    def __init__(self, db :Session):
        self.db = db
        self.notes = NoteRepository(db)
        self.labels = LabelRepository(db)
        self.shares = Shererepository(db)

    #permisos
    def user_can_read(self, user_id : int , note : Note) -> bool :
        if note.owner_id == user_id:
            return True

        if self.shares.has_note_shere(note_id= note.id, user_id= user_id):
            return True

        label_ids = self.labels.list_label_ids_for_note(note.id)

        return self.shares.has_any_label_shere(label_ids= label_ids, user_id= user_id)

    def user_can_edit( self, user_id : int, note : Note)-> bool:
        if note.owner_id == user_id:
            return True

        if self.shares.has_note_shere(note_id= note.id, user_id= user_id,role = ShereRole.EDIT):
            return True
        label_ids = self.labels.list_label_ids_for_note(note.id)

        return self.shares.has_any_label_shere(label_ids= label_ids, user_id= user_id, role = ShereRole.EDIT)


    def list_visible(self , user_id : int)-> list[Note]:
        owned = self.notes.list_owned(user_id)

        direc_ids = self.shares.list_note_ids_shered_directly(user_id)

        shared_label_ids = self.shares.list_label_ids_shared_with_user(user_id)

        ids_by_label = self.labels.list_note_ids_by_label_ids(shared_label_ids)

        ids = list({*direc_ids, *ids_by_label})

        shered = self.notes.list_by_ids(ids)

        return list({note.id: note for note in [*owned, *shered]}.values())
