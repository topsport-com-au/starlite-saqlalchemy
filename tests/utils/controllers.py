"""Example set of controllers and a router to use for testing."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from starlite import Dependency, delete, get, post, put
from starlite.status_codes import HTTP_200_OK

from starlite_saqlalchemy.repository.types import FilterTypes
from tests.utils.domain import Author, CreateDTO, ReadDTO, Service, UpdateDTO

DETAIL_ROUTE = "/{author_id:uuid}"


def provides_service(db_session: AsyncSession) -> Service:
    """Constructs repository and service objects for the request."""
    return Service(session=db_session)


@get()
async def get_authors(
    service: Service,
    filters: list[FilterTypes] = Dependency(skip_validation=True),
) -> list[ReadDTO]:
    """Get a list of authors."""
    return [ReadDTO.from_orm(item) for item in await service.list(*filters)]


@post()
async def create_author(data: CreateDTO, service: Service) -> ReadDTO:
    """Create an `Author`."""
    return ReadDTO.from_orm(await service.create(Author.from_dto(data)))


@get(DETAIL_ROUTE)
async def get_author(service: Service, author_id: UUID) -> ReadDTO:
    """Get Author by ID."""
    return ReadDTO.from_orm(await service.get(author_id))


@put(DETAIL_ROUTE)
async def update_author(data: UpdateDTO, service: Service, author_id: UUID) -> ReadDTO:
    """Update an author."""
    return ReadDTO.from_orm(await service.update(author_id, Author.from_dto(data)))


@delete(DETAIL_ROUTE, status_code=HTTP_200_OK)
async def delete_author(service: Service, author_id: UUID) -> ReadDTO:
    """Delete Author by ID."""
    return ReadDTO.from_orm(await service.delete(author_id))
