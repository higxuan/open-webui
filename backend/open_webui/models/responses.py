import time
from typing import Any, Optional

from open_webui.internal.db import Base, JSONField, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, Index, Text, delete, select
from sqlalchemy.ext.asyncio import AsyncSession


class ResponseState(Base):
    __tablename__ = 'response_state'

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False, index=True)
    chat_id = Column(Text, nullable=False, index=True)
    message_id = Column(Text, nullable=False)
    model = Column(Text, nullable=False, index=True)
    status = Column(Text, nullable=False, default='completed')

    input = Column(JSONField, nullable=True)
    instructions = Column(Text, nullable=True)
    output = Column(JSONField, nullable=True)
    response = Column(JSONField, nullable=True)
    usage = Column(JSONField, nullable=True)
    meta = Column(JSONField, nullable=True)

    store = Column(Boolean, default=True, nullable=False)
    created_at = Column(BigInteger, nullable=False, index=True)
    updated_at = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index('response_state_user_created_idx', 'user_id', 'created_at'),
        Index('response_state_chat_message_idx', 'chat_id', 'message_id'),
    )


class ResponseStateModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    chat_id: str
    message_id: str
    model: str
    status: str
    input: Optional[Any] = None
    instructions: Optional[str] = None
    output: Optional[list] = None
    response: Optional[dict] = None
    usage: Optional[dict] = None
    meta: Optional[dict] = None
    store: bool = True
    created_at: int
    updated_at: int


class ResponseStateTable:
    async def insert_state(
        self,
        *,
        id: str,
        user_id: str,
        chat_id: str,
        message_id: str,
        model: str,
        status: str = 'completed',
        input: Any = None,
        instructions: str | None = None,
        output: list | None = None,
        response: dict | None = None,
        usage: dict | None = None,
        meta: dict | None = None,
        store: bool = True,
        db: Optional[AsyncSession] = None,
    ) -> ResponseStateModel:
        now = int(time.time())

        async with get_async_db_context(db) as session:
            state = ResponseState(
                id=id,
                user_id=user_id,
                chat_id=chat_id,
                message_id=message_id,
                model=model,
                status=status,
                input=input,
                instructions=instructions,
                output=output,
                response=response,
                usage=usage,
                meta=meta or {},
                store=store,
                created_at=now,
                updated_at=now,
            )
            session.add(state)
            await session.commit()
            await session.refresh(state)
            return ResponseStateModel.model_validate(state)

    async def get_state_by_id(
        self,
        id: str,
        user_id: str | None = None,
        db: Optional[AsyncSession] = None,
    ) -> ResponseStateModel | None:
        async with get_async_db_context(db) as session:
            stmt = select(ResponseState).filter_by(id=id)
            if user_id is not None:
                stmt = stmt.filter_by(user_id=user_id)

            result = await session.execute(stmt)
            state = result.scalar_one_or_none()
            return ResponseStateModel.model_validate(state) if state else None

    async def delete_state_by_id(
        self,
        id: str,
        user_id: str | None = None,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        async with get_async_db_context(db) as session:
            stmt = delete(ResponseState).filter_by(id=id)
            if user_id is not None:
                stmt = stmt.filter_by(user_id=user_id)

            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0


ResponseStates = ResponseStateTable()
