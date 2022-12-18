#!/bin/sh
"exec" "`dirname $0`/.venv/bin/python" "-u" "$0" "$@"

import argparse
import asyncio
import datetime
import json
from dataclasses import dataclass
from collections import defaultdict
from typing import List, Tuple, Optional

import aiohttp

@dataclass
class Info:
    open_price: float
    low_price: float
    high_price: float
    last_price: float
    change_percent: float

async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


class Moex:
    def __init__(self, engine, market, board):
        self.url_prefix = f'http://iss.moex.com/iss/engines/{engine}/markets/{market}/boards/{board}/securities.json'
        self.url_prefix += '?iss.meta=off&iss.only=securities,marketdata&marketdata.columns=OPEN,LOW,HIGH,LAST&securities.columns=PREVPRICE&securities='

    async def fetch(self, tickers: List[str]) -> List[Tuple[str, Optional[Info]]]:
        r = await fetch_json(f'{self.url_prefix}{",".join(tickers)}')
        resp = []
        for ticker, (prev_price,), data in zip(tickers, r['securities']['data'], r['marketdata']['data']):
            if prev_price is not None:
                change_pcnt = (data[-1] - prev_price) * 100 / prev_price
                resp.append((ticker, Info(*[*data, change_pcnt])))
            else:
                resp.append((ticker, None))
        return resp

class Binance:
    async def fetch(self, tickers: List[str]) -> List[Tuple[str, Optional[Info]]]:
        resp = []
        for ticker, r in zip(tickers, await asyncio.gather(*[fetch_json(f'https://api.binance.com/api/v3/ticker/24hr?symbol={ticker}') for ticker in tickers], return_exceptions=True)):
            if isinstance(r, Exception):
                # print(f'exception: {el}')
                resp.append((ticker, None))
                continue
            resp.append((ticker, Info(*[float(r[x]) for x in ('openPrice', 'lowPrice', 'highPrice', 'lastPrice', 'priceChangePercent')])))
        return resp


PROVIDERS = {
    'moex_currency': Moex('currency', 'selt', 'CETS'),
    'moex_futures': Moex('futures', 'forts', 'RFUD'),
    'binance': Binance(),
}


def format_line(symbol: str, res: Optional[Info]):
    if res is None:
        return f'{symbol} ?'
    if res.change_percent > 0:
        color = '33aa33'
        prefix = '+'
    else:
        color = 'ee4444'
        prefix = ''
    return f'{symbol} {res.last_price:.2f} <span font="sans 6" color="#{color}">{prefix}{res.change_percent:.1f}%</span>'


async def process(tickers):
    by_type = defaultdict(list)
    sorted_results = []
    ticker2pos = {}
    for pos, (xtype, ticker, symbol) in enumerate(tickers):
        by_type[xtype].append((ticker, symbol))
        sorted_results.append([ticker, symbol, None])
        ticker2pos[ticker] = pos

    while True:
        for el in await asyncio.gather(*[PROVIDERS[xtype].fetch([v[0] for v in tlist]) for xtype, tlist in by_type.items()], return_exceptions=True):
            if isinstance(el, Exception):
                # print(f'exception: {el}')
                continue
            for ticker, data in el:
                sorted_results[ticker2pos[ticker]][-1] = data

        line = '<span color="#888888"> | </span>'.join(format_line(symbol, res) for _, symbol, res in sorted_results)

        tooltip = f'{".":<10s}' + ''.join(f'{symbol:<10s}' for _, symbol, _ in sorted_results)
        for title, field in (('open', 'open_price'), ('low', 'low_price'), ('high', 'high_price'), ('last', 'last_price'), ('change%', 'change_percent')):
            tooltip += f'\n{title:<10s}'
            for _, _, res in sorted_results:
                if res:
                    tooltip += f'<span color="#{"33aa33" if res.change_percent > 0 else "ee4444"}">{getattr(res, field):<10.2f}</span>'
                else:
                    tooltip += f'{"?":<10s}'

        yield line, tooltip


async def main(tickers, out_format, update_timeout):
    async for line, tooltip in process(tickers):
        if out_format == 'waybar':
            print(json.dumps({'text': line, 'tooltip': tooltip, 'alt': 'shiftdel'}))

        elif out_format == 'awesome':
            print(f'text\t{line}')
            print(f'tooltipstart')
            print(f'tooltip\t<span color="#555555">{datetime.datetime.now()}</span>')
            for t in tooltip.split('\n'):
                print(f'tooltip\t{t}')

        await asyncio.sleep(update_timeout)


def parse_arg_ticker(s: str):
    x = s.split(':')
    assert len(x) == 3
    assert x[0] in PROVIDERS
    return x

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', type=parse_arg_ticker, action='append', help='tickers, format: {provider}:{ticker}:{symbol}', required=True)
    parser.add_argument('--format', choices=['awesome', 'waybar'], required=True, help='output format')
    parser.add_argument('--update-interval', type=int, required=False, default=60, help='update interval, seconds')
    args = parser.parse_args()

    asyncio.run(main(args.ticker, args.format, args.update_interval))
