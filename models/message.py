from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=False)
    author = Column(String, nullable=False)

    def __repr__(self):
        return f"<Message(id={self.id}, plate={self.plate}, author={self.author})>"


class MessageLoaded(Base):
    __tablename__ = "message_loaded"
    id = Column(Integer, primary_key=True, index=True)
    is_loaded = Column(Boolean, nullable=False, default=False)
