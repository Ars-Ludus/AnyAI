import asyncio
from typing import List, Dict
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQLAlchemy Setup
DATABASE_URL = os.getenv("MEMORY_SQL")
if not DATABASE_URL:
    raise ValueError("MEMORY_SQL environment variable not set.")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Schema (`topics`)
class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False, unique=True) # Added unique constraint
    datetime = Column(DateTime, nullable=False)
    turn_id = Column(Integer, nullable=False)
    embedding = Column(LargeBinary, nullable=True)
    synonym = Column(ARRAY(String), default=[])
    foreign_key = Column(String, nullable=True)
    last_refactored = Column(DateTime, nullable=True)
    extra_metadata = Column(JSONB, default={})

    def __repr__(self):
        return f"<Topic(topic='{self.topic}', datetime='{self.datetime}', turn_id={self.turn_id}, extra_metadata={self.extra_metadata})>"

from memory.rag_dummy import receive_topics
from memory.base import BaseMemory

class utm_anyai(BaseMemory):
    id = "utm_anyai"
    name = "Universal Topic Mapper (AnyAI)"

    def __init__(self):
        print("UtmAnyAI module initialized.")
        self._turn_counters = {} # To generate turn_id per session
        # Base.metadata.create_all(bind=engine) # This should be handled by Alembic

    def _get_db(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def _extract_topics_from_content(self, content: str) -> List[str]:
        """
        Synchronously extracts high-level topic strings from message content.
        Uses a dummy implementation for now.
        """
        # Dummy topic extraction: simple keyword matching or first few words
        # In a real scenario, this would involve a local LLM (Mistral or similar)
        
        # Example: Extracting up to 3 topics based on keywords
        topics = []
        content_lower = content.lower()
        
        if "memory" in content_lower:
            topics.append("Memory Architecture")
        if "topic" in content_lower:
            topics.append("Topic Extraction")
        if "database" in content_lower or "sql" in content_lower:
            topics.append("Database Management")
        if "module" in content_lower:
            topics.append("Module Integration")
        if "alembic" in content_lower:
            topics.append("Alembic Migrations")
        if "llm" in content_lower or "model" in content_lower:
            topics.append("Language Models")
        if "async" in content_lower:
            topics.append("Asynchronous Operations")

        # Limit to top 3 topics
        return topics[:3]

    def _generate_synonyms(self, topic: str) -> List[str]:
        """
        Generates synonyms for a given topic.
        Uses a dummy implementation for now.
        """
        # Dummy synonym generation: simple transformations
        synonyms = [topic]
        if "memory" in topic.lower():
            synonyms.extend(["recall", "storage"])
        if "topic" in topic.lower():
            synonyms.extend(["subject", "theme"])
        if "database" in topic.lower():
            synonyms.extend(["db", "data store"])
        return list(set(synonyms)) # Remove duplicates

    def extract_and_store_topics(self, message: Dict):
        """
        Accepts a message dict, extracts topics, stores them, and forwards to RAG.
        """
        role = message.get("role")
        content = message.get("content")
        timestamp = message.get("timestamp", datetime.now())
        session_id = message.get("session_id", "default")
        turn_id = message.get("turn_id")

        if not content:
            print("Warning: Message content missing for topic extraction.")
            return

        # If turn_id is not provided, generate one based on session
        if turn_id is None:
            self._turn_counters[session_id] = self._turn_counters.get(session_id, 0) + 1
            turn_id = self._turn_counters[session_id]
            print(f"Generated turn_id {turn_id} for session {session_id}")

        extracted_topics = self._extract_topics_from_content(content)
        all_topics_for_rag = []

        for topic_str in extracted_topics:
            synonyms = self._generate_synonyms(topic_str)
            all_topics_for_rag.append(topic_str)
            all_topics_for_rag.extend(synonyms) # Include synonyms for RAG

            db_session = next(self._get_db())
            try:
                # Check if topic or any synonym already exists
                existing_topic = db_session.query(Topic).filter(
                    (Topic.topic == topic_str) | (Topic.synonym.any(synonyms))
                ).first()

                if existing_topic:
                    # If topic exists, append new datetime and turn_id (or track history)
                    # For simplicity, we'll just update last_refactored for now
                    # A more complex history tracking would involve a separate table or JSONB list
                    existing_topic.last_refactored = datetime.now()
                    # Ensure synonyms are unique and updated
                    for syn in synonyms:
                        if syn not in existing_topic.synonym:
                            existing_topic.synonym.append(syn)
                    print(f"Updated existing topic: {existing_topic.topic}")
                else:
                    # Insert a new row
                    new_topic = Topic(
                        topic=topic_str,
                        datetime=timestamp,
                        turn_id=turn_id,
                        synonym=synonyms,
                        foreign_key=session_id, # Store session_id as foreign_key
                        last_refactored=datetime.now()
                    )
                    db_session.add(new_topic)
                    print(f"Inserted new topic: {new_topic.topic}")
                db_session.commit()
            except SQLAlchemyError as e:
                db_session.rollback()
                print(f"Database error during topic storage: {e}")
            finally:
                db_session.close()
        
        # Forward extracted topics (including synonyms) to RAG dummy
        receive_topics(list(set(all_topics_for_rag))) # Ensure unique topics for RAG

    # MemoryManager Interface Methods
    def add_message(self, role: str, content: str, session_id: str = "default"):
        """
        Adds a new message and triggers topic extraction and storage.
        turn_id is generated internally if not provided by the caller.
        """
        message_dict = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "session_id": session_id,
            "turn_id": None # Explicitly set to None, will be generated in extract_and_store_topics
        }
        self.extract_and_store_topics(message_dict)

    def get_messages(self, session_id: str = "default") -> List[Dict]:
        """
        As an active memory module, this should return messages.
        For UTM, it will return topics as "messages" for now, or an empty list.
        A more complete implementation might retrieve messages from another source.
        """
        db_session = next(self._get_db())
        try:
            topics = db_session.query(Topic).filter(Topic.foreign_key == session_id).order_by(Topic.datetime).all()
            # Transform topics into a message-like format for compatibility
            messages = []
            for topic_obj in topics:
                messages.append({
                    "role": "system", # Or "topic_extractor"
                    "content": f"Topic: {topic_obj.topic} (Synonyms: {', '.join(topic_obj.synonym)})",
                    "timestamp": topic_obj.datetime,
                    "session_id": session_id,
                    "turn_id": topic_obj.turn_id
                })
            return messages
        except SQLAlchemyError as e:
            print(f"Database error during get_messages: {e}")
            return []
        finally:
            db_session.close()

    def clear(self, session_id: str = "default"):
        """
        Clears topics associated with a session.
        """
        db_session = next(self._get_db())
        try:
            db_session.query(Topic).filter(Topic.foreign_key == session_id).delete()
            db_session.commit()
            print(f"Cleared topics for session: {session_id}")
            # Reset turn counter for the session
            if session_id in self._turn_counters:
                del self._turn_counters[session_id]
        except SQLAlchemyError as e:
            db_session.rollback()
            print(f"Database error during clear: {e}")
        finally:
            db_session.close()

    def get_context_string(self, session_id: str = "default") -> str:
        """
        Retrieves topics as a context string.
        """
        messages = self.get_messages(session_id=session_id)
        return "\n".join([msg["content"] for msg in messages])

    async def _populate_missing_embeddings(self):
        """
        Asynchronously checks for known topics and populates missing ones with vector embeddings.
        This is a stub for future implementation.
        """
        print("Running asynchronous embedding population routine (stub)...")
        db_session = next(self._get_db())
        try:
            topics_without_embeddings = db_session.query(Topic).filter(Topic.embedding == None).all()
            for topic_obj in topics_without_embeddings:
                # Simulate embedding generation
                dummy_embedding = b"dummy_embedding_for_" + topic_obj.topic.encode('utf-8')
                topic_obj.embedding = dummy_embedding
                print(f"Populated dummy embedding for topic: {topic_obj.topic}")
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            print(f"Database error during embedding population: {e}")
        finally:
            db_session.close()
        print("Asynchronous embedding population routine finished.")

# Example usage for testing (will be commented out or moved to unit tests)
if __name__ == "__main__":
    utm_anyai_instance = utm_anyai()
    # Simulate a message
    sample_message = {
        "role": "user",
        "content": "I need to understand the memory architecture and how topics are extracted and stored in the database using Alembic.",
        "timestamp": datetime.now(),
        "session_id": "test_session_123",
        "turn_id": 1
    }

    print("\n--- Simulating first message ---")
    utm_anyai_instance.add_message(
        role=sample_message["role"],
        content=sample_message["content"],
        session_id=sample_message["session_id"],
        turn_id=sample_message["turn_id"]
    )

    print("\n--- Simulating second message with overlapping topics ---")
    sample_message_2 = {
        "role": "assistant",
        "content": "The topic extraction process involves language models and asynchronous operations for embeddings.",
        "timestamp": datetime.now(),
        "session_id": "test_session_123",
        "turn_id": 2
    }
    utm_anyai_instance.add_message(
        role=sample_message_2["role"],
        content=sample_message_2["content"],
        session_id=sample_message_2["session_id"],
        turn_id=sample_message_2["turn_id"]
    )

    print("\n--- Retrieving messages (topics) ---")
    retrieved_topics = utm_anyai_instance.get_messages(session_id="test_session_123")
    for msg in retrieved_topics:
        print(f"Retrieved: {msg['content']}")

    print("\n--- Simulating embedding population ---")
    asyncio.run(utm_anyai_instance._populate_missing_embeddings())

    print("\n--- Clearing session topics ---")
    utm_anyai_instance.clear(session_id="test_session_123")

module_config = {
    "name": "UTM AnyAI Memory",
    "description": "Universal Transactional Memory for AnyAI",
    "version": "1.0",
    "capabilities": ["add_message", "get_messages", "clear", "get_context_string"]
}