# memory/stm_prp.py

import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
from memory.base import BaseMemory

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class stm_prp(BaseMemory):
    id = "stm_prp"
    name = "Perpetual Memory"

    def __init__(self):
        db_url = os.getenv("MEMORY_SQL")
        if not db_url:
            logging.error("MEMORY_SQL environment variable not set")
            raise ValueError("MEMORY_SQL environment variable not set")
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)  # Create tables if they don't exist
        logging.info(f"stm_prp initialized with DB URL: {db_url}, tables created")

    def add_message(self, role: str, content: str, session_id: str = "default"):
        session = self.Session()
        try:
            new_message = Message(session_id=session_id, role=role, content=content)
            session.add(new_message)
            session.commit()
            logging.info(f"Added message to session '{session_id}': Role='{role}', Content='{content[:50]}...'")
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding message to session '{session_id}': {e}")
        finally:
            session.close()

    def get_messages(self, session_id: str = "default"):
        session = self.Session()
        try:
            messages = session.query(Message).filter_by(session_id=session_id).order_by(Message.timestamp).all()
            logging.info(f"Retrieved {len(messages)} messages for session '{session_id}'.")
            return [{"role": msg.role, "content": msg.content} for msg in messages]
        except Exception as e:
            logging.error(f"Error retrieving messages for session '{session_id}': {e}")
            return []
        finally:
            session.close()

    def clear(self, session_id: str = "default"):
        session = self.Session()
        try:
            session.query(Message).filter_by(session_id=session_id).delete()
            session.commit()
            logging.info(f"Cleared memory for session '{session_id}'.")
        except Exception as e:
            session.rollback()
            logging.error(f"Error clearing memory for session '{session_id}': {e}")
        finally:
            session.close()

    def get_context_string(self, session_id: str = "default") -> str:
        session = self.Session()
        try:
            messages = session.query(Message).filter_by(session_id=session_id).order_by(Message.timestamp).all()
            context_string = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
            logging.info(f"Generated context string for session '{session_id}'. Length: {len(context_string)} characters.")
            return context_string
        except Exception as e:
            logging.error(f"Error generating context string for session '{session_id}': {e}")
            return "[Memory Context Unavailable]"
        finally:
            session.close()

module_config = {
    "name": "Perpetual Memory",
    "description": "Stores conversation history in a PostgreSQL database."
}