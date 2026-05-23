import asyncio
import sys
import logging
sys.path.append('d:/final_h')

logging.basicConfig(level=logging.INFO)

from backend.camera.area_counter import generate_area_tracking_stream

async def run():
    count = 0
    async for f in generate_area_tracking_stream('food_court'):
        print(f'Got frame! {count}')
        count += 1
        if count > 5:
            break

asyncio.run(run())
