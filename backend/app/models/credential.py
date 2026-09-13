from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import utcnow


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # e.g. "llm_api_key", "http_header"
    data_encrypted = Column(JSON, nullable=False)  # dict of field -> encrypted value
    created_at = Column(DateTime(timezone=True), default=utcnow)

    owner = relationship("User", back_populates="credentials")
