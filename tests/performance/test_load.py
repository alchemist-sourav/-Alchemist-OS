import asyncio
import time
import pytest
from httpx import AsyncClient
import websockets
import json

@pytest.mark.asyncio
async def test_concurrent_websockets():
    start = time.time()
    
    async def connect_ws():
        try:
            async with websockets.connect("ws://localhost:8000/ws?api_key=alchemist_default_secret") as ws:
                await ws.send(json.dumps({"text": "Hello"}))
                await asyncio.sleep(0.5)
                return True
        except Exception as e:
            return False

    tasks = [connect_ws() for _ in range(50)]
    results = await asyncio.gather(*tasks)
    
    successes = sum(1 for r in results if r)
    duration = time.time() - start
    print(f"\nWebsocket Load Test: {successes}/50 successful in {duration:.2f}s")
    assert successes > 40 # Allow some failures in CI/CD environment

@pytest.mark.asyncio
async def test_api_load():
    start = time.time()
    
    async def fetch():
        async with AsyncClient() as client:
            try:
                response = await client.get("http://localhost:8000/admin/health")
                return response.status_code == 200
            except:
                return False

    tasks = [fetch() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    
    successes = sum(1 for r in results if r)
    duration = time.time() - start
    print(f"\nAPI Load Test: {successes}/100 successful in {duration:.2f}s")
    assert successes > 90
