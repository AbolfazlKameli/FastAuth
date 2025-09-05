from sqlalchemy import Select, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import db_dependency


class Paginator:
    def __init__(self, session: AsyncSession, query: Select, page: int, per_page: int):
        self.session = session
        self.query = query
        self.page = page
        self.per_page = per_page
        self.limit = per_page * page
        self.offset = (page - 1) * per_page
        # computed later
        self.number_of_pages = 0
        self.next_page = ''
        self.previous_page = ''

    def _get_next_page(self) -> int | None:
        if self.page >= self.number_of_pages:
            return
        return self.page + 1

    def _get_previous_page(self) -> int | None:
        if self.page == 1 or self.page > self.number_of_pages + 1:
            return
        return self.page - 1

    async def get_response(self) -> dict:
        return {
            'count': await self._get_total_count(),
            'next_page': self._get_next_page(),
            'previous_page': self._get_previous_page(),
            'items': [todo for todo in await self.session.scalars(self.query.limit(self.limit).offset(self.offset))]
        }

    def _get_number_of_pages(self, count: int) -> int:
        rest = count % self.per_page
        quotient = count // self.per_page
        return quotient if not rest else quotient + 1

    async def _get_total_count(self) -> int:
        count = await self.session.scalar(select(func.count()).select_from(self.query.subquery()))
        self.number_of_pages = self._get_number_of_pages(count)
        return count


async def paginate(query: Select, db: db_dependency, page: int, per_page: int) -> dict:
    async with db as session:
        paginator = Paginator(session, query, page, per_page)
        return await paginator.get_response()
