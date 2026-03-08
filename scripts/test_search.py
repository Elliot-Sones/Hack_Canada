import asyncio
from app.database import async_session_maker
from app.schemas.geospatial import ParcelSearchParams
from app.routers.parcels import search_parcels

async def main():
    async with async_session_maker() as db:
        params = ParcelSearchParams()
        params.address = "123 King St W"
        try:
            res = await search_parcels(params=params, db=db)
            print("Success:", len(res))
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
