from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Note


class Postgres:
    def __init__(self, db_user: str, db_pass: str, database: str, db_host: str = 'localhost', db_port: int = 5432):
        engine = create_engine(f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{database}')
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def clear_notes(self):
        all_notes = self.session.query(Note).all()
        for note in all_notes:
            self.session.delete(note)
            print(f'{note.title} deleted')
        self.session.commit()

    def get_all_notes(self):
        """Get all note titles and content."""
        return self.session.query(Note.title, Note.content).all()

if __name__ == '__main__':
    postgres = Postgres('babysuse', 'haha', 'hedgedoc')
    postgres.get_all_notes()
