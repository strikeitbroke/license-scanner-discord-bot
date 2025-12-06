from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Channel(Base):
    __tablename__ = "channel"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    messages = relationship("Message", back_populates="channel")  # <-- add this
    message_loaded = relationship("ChannelLoadStatus", back_populates="channel", uselist=False)


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, index=True, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=False)
    author = Column(String, nullable=False)

    # Foreign key column
    channel_id = Column(Integer, ForeignKey("channel.id"), nullable=False)
    channel = relationship("Channel", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, plate={self.plate}, author={self.author})>"


class ChannelLoadStatus(Base):
    __tablename__ = "channel_load_status"
    id = Column(Integer, primary_key=True, index=True)
    is_loaded = Column(Boolean, nullable=False, default=False)

    # Foreign key to Guild with unique constraint
    channel_id = Column(Integer, ForeignKey("channel.id"), unique=True, nullable=False)
    channel = relationship("Channel", back_populates="message_loaded")
