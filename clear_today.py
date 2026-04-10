import asyncio
from datetime import date
from sqlalchemy import delete
from app.db.session import async_session_maker
from app.db.models import Lesson

async def main():
    async with async_session_maker() as session:
        today = date.today()
        stmt = delete(Lesson).where(
            Lesson.published_on == today,
            Lesson.id.like("lesson-ai-%")
        )
        await session.execute(stmt)
        await session.commit()
        print("Cleared today's AI lessons.")

if __name__ == "__main__":
    asyncio.run(main())
