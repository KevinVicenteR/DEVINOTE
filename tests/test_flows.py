import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import SQLModel, Session, create_engine, select

from app.core.security import create_acces_token, decode_token
from app.models.Users import User, UserCreate
from app.models.note import Note, NoteRead
from app.models.share import LabelShere, NoteShere, ShereRole
from app.repositories.label_repository import LabelRepository
from app.repositories.note_repository import NoteRepository
from app.repositories.shere_repository import Shererepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.note_service import NoteService
from main import app


class FlowTests(unittest.TestCase):
    def setUp(self):
        secret_patch = patch('app.core.security.setting.JWT_SECRET', 'test-secret-with-at-least-32-characters')
        secret_patch.start()
        self.addCleanup(secret_patch.stop)
        self.engine = create_engine('sqlite://')

        @event.listens_for(self.engine, 'connect')
        def enable_foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')

        SQLModel.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)
        self.users = UserRepository(self.db)
        self.owner = self.users.create(User(email='owner@example.com', hashed_password='unused'))
        self.reader = self.users.create(User(email='reader@example.com', hashed_password='unused'))
        self.outsider = self.users.create(User(email='outsider@example.com', hashed_password='unused'))
        self.notes = NoteRepository(self.db)
        self.labels = LabelRepository(self.db)
        self.shares = Shererepository(self.db)
        self.service = NoteService(self.db)

    def test_register_login_and_token_expiry(self):
        import jwt

        auth = AuthService(self.users)
        password = 'a' * 80
        user = auth.register(UserCreate(email='new@example.com', password=password))
        self.assertNotEqual(user.hashed_password, password)
        self.assertEqual(decode_token(auth.login(user.email, password))['sub'], str(user.id))
        self.assertEqual(self.users.get_by_id(user.id).email, user.email)
        for wrong_password in ['incorrect', 'a' * 72 + 'different']:
            with self.assertRaises(HTTPException) as error:
                auth.login(user.email, wrong_password)
            self.assertEqual(error.exception.status_code, 401)
        with self.assertRaises(HTTPException):
            auth.login('missing@example.com', password)
        with self.assertRaises(HTTPException):
            auth.register(UserCreate(email=user.email, password=password))
        with self.assertRaises(jwt.ExpiredSignatureError):
            decode_token(create_acces_token({'sub': str(user.id)}, minutes=-1))

    def test_note_and_label_operations(self):
        note = self.notes.create(Note(title='First', owner_id=self.owner.id))
        label = self.labels.create(self.owner.id, 'Work')
        self.assertEqual(self.labels.get(label.id), label)
        self.assertEqual(self.labels.get_by_name(self.owner.id, 'Work'), label)
        self.assertEqual(self.labels.list_by_user(self.owner.id), [label])
        self.assertEqual(self.labels.list_ids_for_owner_sebset(self.owner.id, [label.id, label.id]), [label.id])
        self.assertEqual(self.labels.list_ids_for_owner_sebset(self.reader.id, [label.id]), [])
        self.notes.replace_labels(self.owner.id, note.id, [label.id, label.id])
        self.assertEqual(self.labels.list_label_ids_for_note(note.id), [label.id])
        self.assertEqual(self.labels.list_note_ids_by_label_ids([label.id]), [note.id])
        self.assertEqual(self.labels.list_by_ids([note.id]), [note])
        note.title = 'Updated'
        self.notes.update(note)
        self.assertEqual(NoteRead.model_validate(note).title, 'Updated')
        foreign_label = self.labels.create(self.reader.id, 'Other')
        with self.assertRaises(ValueError):
            self.notes.replace_labels(self.owner.id, note.id, [foreign_label.id])
        with self.assertRaises(ValueError):
            self.notes.replace_labels(self.reader.id, note.id, [])
        self.assertEqual(self.labels.list_label_ids_for_note(note.id), [label.id])
        self.shares.upsert_label_share(label.id, self.reader.id, ShereRole.READ)
        self.labels.delete(label)
        self.assertEqual(self.labels.list_label_ids_for_note(note.id), [])
        self.assertEqual(self.shares.list_label_ids_shared_with_user(self.reader.id), [])
        self.shares.upsert_note_share(note.id, self.reader.id, ShereRole.READ)
        self.notes.delete(note)
        self.assertIsNone(self.notes.get(note.id))
        self.assertEqual(self.shares.list_note_ids_shered_directly(self.reader.id), [])

    def test_shared_visibility_and_permissions(self):
        note = self.notes.create(Note(title='Shared', owner_id=self.owner.id))
        label = self.labels.create(self.owner.id, 'Team')
        self.notes.replace_labels(self.owner.id, note.id, [label.id])
        self.assertTrue(self.service.user_can_edit(self.owner.id, note))
        self.assertFalse(self.service.user_can_read(self.reader.id, note))
        self.assertFalse(self.service.user_can_edit(self.reader.id, note))
        self.assertEqual(self.service.list_visible(self.reader.id), [])
        direct = self.shares.upsert_note_share(note.id, self.reader.id, ShereRole.READ)
        self.assertIsNotNone(direct.id)
        self.assertTrue(self.service.user_can_read(self.reader.id, note))
        self.assertFalse(self.service.user_can_edit(self.reader.id, note))
        self.shares.upsert_note_share(note.id, self.reader.id, ShereRole.EDIT)
        self.assertTrue(self.service.user_can_edit(self.reader.id, note))
        shared_label = self.shares.upsert_label_share(label.id, self.reader.id, ShereRole.READ)
        self.assertIsNotNone(shared_label.id)
        self.assertEqual(self.service.list_visible(self.reader.id), [note])
        self.assertEqual(self.service.list_visible(self.owner.id), [note])
        self.shares.remove_note_shere(note.id, self.reader.id)
        self.assertTrue(self.service.user_can_read(self.reader.id, note))
        self.assertFalse(self.service.user_can_edit(self.reader.id, note))
        self.shares.upsert_label_share(label.id, self.reader.id, ShereRole.EDIT)
        self.assertTrue(self.service.user_can_edit(self.reader.id, note))
        self.assertFalse(self.service.user_can_read(self.outsider.id, note))
        self.assertFalse(self.service.user_can_edit(self.outsider.id, note))
        self.shares.remove_label_shere(label.id, self.reader.id)
        self.assertEqual(self.service.list_visible(self.reader.id), [])
        self.assertEqual(list(self.db.exec(select(NoteShere)).all()), [])
        self.assertEqual(list(self.db.exec(select(LabelShere)).all()), [])

    def test_database_initialization_and_http(self):
        from app.core import db
        with patch.object(db, 'engine', self.engine):
            db.init_db()
        self.assertIn('user', SQLModel.metadata.tables)
        with TestClient(app) as client:
            self.assertEqual(client.get('/').status_code, 200)
            self.assertEqual(client.get('/openapi.json').status_code, 200)


if __name__ == '__main__':
    unittest.main()
