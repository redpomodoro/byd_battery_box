import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from bydboxclient import BydBoxClient
import asyncio



async def main():
    boxclient = BydBoxClient('192.168.30.254',8080,1, 30)

    #task = asyncio.create_task(boxclient.init_data())
    await boxclient.init_data()

    for k, v in boxclient.data.items():
        print(f'{k} {v}')

if __name__ == "__main__":
    asyncio.run(main())