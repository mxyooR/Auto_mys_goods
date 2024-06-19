import httpx
import asyncio
import json
from datetime import datetime, timedelta
import ntplib
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

async def get_ntp_time():
    client = ntplib.NTPClient()
    
    def fetch_ntp_time():
        try:
            response = client.request('ntp.aliyun.com')
            return datetime.utcfromtimestamp(response.tx_time) + timedelta(hours=8)
        except Exception as e:
            print(f"Failed to fetch NTP time: {e}")
            return None
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, fetch_ntp_time)

async def exchange_goods(payload, headers):
    url = "https://api-takumi.miyoushe.com/mall/v1/web/goods/exchange"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=json.dumps(payload), headers=headers)
            print(response.text)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

async def schedule_task():
    # 在程序开始时读取JSON文件
    with open('data.json', 'r') as f:
        config = json.load(f)
        payload = {
            "app_id": config["app_id"],
            "point_sn": config["point_sn"],
            "goods_id": config["goods_id"],
            "exchange_num": config["exchange_num"],
            "uid": config["uid"],
            "region": config["region"],
            "game_biz": config["game_biz"],
            "address_id": config["address_id"]
        }
        headers = config["headers"]
        target_time = datetime.fromisoformat(config["target_time"])
    
    while True:
        ntp_time = await get_ntp_time()
        
        if ntp_time:
            delay = (target_time - ntp_time).total_seconds()
            if delay <= 15:
                await asyncio.sleep(delay)
                await asyncio.gather(
                    exchange_goods(payload, headers),
                    exchange_goods(payload, headers),
                    exchange_goods(payload, headers),
                    exchange_goods(payload, headers),
                    exchange_goods(payload, headers)
                )
                break
            else:
                print(f"Current NTP time is {ntp_time}")
                print(f"Current delay is {delay} seconds. Checking again in 10 seconds.")
                await asyncio.sleep(10)
        else:
            print("Failed to get NTP time, retrying in 1 second.")
            await asyncio.sleep(1)

# 运行异步任务
asyncio.run(schedule_task())
