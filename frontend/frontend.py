import os
import datapane as dp
import libsql_client
import pandas as pd
import asyncio

async def get_data(url):
    async with libsql_client.Client(url) as client:
        data = await client.execute("SELECT * FROM messages")
        df = pd.DataFrame.from_records(data=data.rows, columns=data.columns)

    app = dp.App(dp.DataTable(df))
    app.upload(name="YAIG summary", description="latest hot messages in YAIG", open=True)


if __name__ == "__main__":
    url = os.getenv("LIBSQL_URL")
    asyncio.run(get_data(url))
