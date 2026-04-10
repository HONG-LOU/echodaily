import asyncio
import logging
from datetime import date
import traceback

from app.db.session import get_session_factory
from app.api.dependencies import lesson_repository, daily_message_client
from app.api.routers.lessons import _generate_and_store_lessons, MAX_RECENT_LESSONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_daily_lessons_task():
    while True:
        try:
            current_day = date.today()
            session_factory = get_session_factory()
            async with session_factory() as session:
                lessons = await lesson_repository.list_recent(
                    session,
                    current_day=current_day,
                    limit=MAX_RECENT_LESSONS,
                )
                if len(lessons) < MAX_RECENT_LESSONS:
                    logger.info(f"Generating lessons for {current_day}...")
                    generated_lessons = await _generate_and_store_lessons(
                        session=session,
                        current_day=current_day,
                        existing_lessons=lessons,
                        target_count=MAX_RECENT_LESSONS,
                    )
                    if generated_lessons:
                        await lesson_repository.add_many(session, generated_lessons)
                        await session.commit()
                        logger.info(f"Successfully generated {len(generated_lessons)} lessons.")
        except Exception as e:
            logger.error(f"Error in daily lesson generation task: {e}")
            traceback.print_exc()
        
        # Sleep for 1 hour before checking again
        await asyncio.sleep(3600)
