from argparse import ArgumentParser
import aiohttp
from aiohttp import ClientSession
import asyncio
from typing import Dict, List
from datetime import date
import datetime
from dateutil.rrule import rrule, DAILY


def get_parser(parser: ArgumentParser = ArgumentParser) -> ArgumentParser:
    parser = parser(description="Console utility for request")

    subparsers = parser.add_subparsers(
        title="subcommands for request", dest="command", description="it have 3 command"
    )

    subparsers.add_parser("symbols", help="call this commmand for list currency")

    convert_parser = subparsers.add_parser(
        "convert", help="this command for convert currency to another currency"
    )
    convert_parser.add_argument("--from", help="argument for currency")
    convert_parser.add_argument("--to", help="argument for currency")
    convert_parser.add_argument(
        "money", default="1", help="how many money you need for convert"
    )

    history_parser = subparsers.add_parser(
        "history", help="this command for see history"
    )
    history_parser.add_argument("--from", help="currency")
    history_parser.add_argument("--to", help="this is currency too")
    history_parser.add_argument("--date_from", help="date")
    history_parser.add_argument("--date_to", help="this is date too")
    history_parser.add_argument("money", default="1", help="how many money you need")

    return parser


def get_urls(data: Dict, urls=[]) -> List[str]:
    data_from = data["from"].upper()
    data_to = data["to"].upper()
    money = data["money"]
    date_from = data["date_from"]
    date_to = data["date_to"]

    date_from = datetime.datetime.strptime(date_from, "%Y%m%d").date()
    date_from = date_from.strftime("%Y%m%d")

    date_to = datetime.datetime.strptime(date_to, "%Y%m%d").date()
    date_to = date_to.strftime("%Y%m%d")

    a = date(int(date_from[:4]), int(date_from[5]), int(date_from[6:]))
    b = date(int(date_to[:4]), int(date_to[5]), int(date_to[6:]))

    [
        urls.append(
            f'https://api.exchangerate.host/{dt.strftime("%Y-%m-%d")}?symbols={data_from},{data_to}&amount={money}'
        )
        for dt in rrule(DAILY, dtstart=a, until=b)
    ]

    return urls


async def history(session: ClientSession, url: str) -> List[Dict]:
    ten_millis = aiohttp.ClientTimeout(total=60)
    async with session.get(url, timeout=ten_millis) as response:
        data = await response.json()
        if data["success"]:
            return [data["date"], data["rates"]]


async def convert(session: ClientSession, data: Dict) -> None:
    data_from = data["from"].upper()
    data_to = data["to"].upper()
    money = data["money"]

    async with session.get(
        f"https://api.exchangerate.host/latest?symbols={data_from},{data_to}&amount={money}"
    ) as response:
        response = await response.json()
        if response["success"]:
            print(
                f'по текущему курсу {money} {data_from} составляет: {response["rates"][data_to]} {data_to}'
            )


async def get_symbols(session: ClientSession) -> None:
    async with session.get("https://api.exchangerate.host/symbols") as response:
        response = await response.json()
        if response["success"]:
            print("Список валют:")
            for value in response["symbols"].values():
                print(value["description"] + " - " + value["code"])


async def main():
    parser = get_parser()
    # parser.print_help()
    # parser.parse_known_args()
    args = parser.parse_args()

    session_timeout = aiohttp.ClientTimeout(total=20, connect=15)
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=10), timeout=session_timeout
    ) as session:
        if args.command == "symbols":
            await get_symbols(session=session)
        if args.command == "convert":
            await convert(session=session, data=vars(args))
        if args.command == "history":
            requests = [
                history(session=session, url=url) for url in get_urls(data=vars(args))
            ]
            print("История котировок за период:")
            [print(str(task) + "\n") for task in await asyncio.gather(*requests)]

            # [print(await finished_task) for finished_task in asyncio.as_completed(requests)]

            # requests = [asyncio.create_task(history(session=session, url=url)) for url in urls]
            # result = [await task for task in requests]
            # print(result)


if __name__ == "__main__":
    asyncio.run(main())
