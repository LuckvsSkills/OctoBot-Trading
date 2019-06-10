#  Drakkar-Software OctoBot-Trading
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.

import time

import numpy as np
from octobot_commons.enums import PriceIndexes, TimeFramesMinutes

from octobot_commons.logging.logging_util import get_logger
from octobot_websockets.constants import MINUTE_TO_SECONDS

from octobot_trading.data_manager.candles_manager import CandlesManager
from octobot_trading.data_manager.order_book_manager import OrderBookManager
from octobot_trading.data_manager.recent_trades_manager import RecentTradesManager
from octobot_trading.data_manager.ticker_manager import TickerManager


class ExchangeSymbolData:
    MAX_ORDER_BOOK_ORDER_COUNT = 100
    MAX_RECENT_TRADES_COUNT = 100

    def __init__(self, symbol):
        self.symbol = symbol

        self.candles_manager = CandlesManager()
        self.order_book_manager = OrderBookManager()
        self.recent_trades_manager = RecentTradesManager()
        self.ticker_manager = TickerManager()

        self.symbol_candles = {}

        self.are_recent_trades_initialized = False
        self.is_order_book_initialized = False
        self.is_price_ticker_initialized = False

        self.logger = get_logger(f"{self.__class__.__name__} - {self.symbol}")

    # candle functions
    async def handle_candles_update(self, time_frame, new_symbol_candles_data, replace_all=False):
        try:
            symbol_candles = self.symbol_candles[time_frame]
        except KeyError:
            symbol_candles = CandlesManager()
            await symbol_candles.initialize()
            symbol_candles.replace_all_candles(new_symbol_candles_data)
            self.symbol_candles[time_frame] = symbol_candles
            return

        if replace_all:
            symbol_candles.replace_all_candles(new_symbol_candles_data)
        else:
            symbol_candles.add_new_candle(new_symbol_candles_data)

    def handle_recent_trades(self, recent_trades):
        self.recent_trades_manager.recent_trades_update(recent_trades)

    def handle_recent_trade_update(self, recent_trades):
        self.recent_trades_manager.recent_trade_update(recent_trades)

    def handle_order_book_update(self, asks, bids):
        self.order_book_manager.order_book_update(asks, bids)

    def handle_order_book_delta_update(self, asks, bids):
        self.order_book_manager.order_book_delta_update(asks, bids)

    def handle_ticker_update(self, ticker):
        self.ticker_manager.ticker_update(ticker)

    # def ensure_data_validity(self, time_frame): TODO
    #     previous_candle_timestamp = self._get_previous_candle_timestamp(time_frame)
    #     error_allowance = 1.2
    #     current_time = time.time()
    #     if previous_candle_timestamp is not None:
    #         # if update time from the previous time frame is greater than this given time frame:
    #         # data did not get updated => data are invalid
    #         if current_time - previous_candle_timestamp > \
    #                 TimeFramesMinutes[time_frame] * MINUTE_TO_SECONDS * error_allowance:
    #             return False
    #     return True

    '''
    Called by non-trade classes
    '''

    # candle functions
    def get_candle_data(self, time_frame):
        if time_frame in self.symbol_candles:
            return self.symbol_candles[time_frame]
        elif time_frame is None:
            return self.symbol_candles[next(iter(self.symbol_candles))]
        return None

    def get_available_time_frames(self):
        return self.symbol_candles.keys()

    # ticker functions
    def get_symbol_ticker(self):
        return self.ticker_manager  # TODO

    # order book functions
    def get_symbol_order_book(self):
        return self.order_book_manager  # TODO

    # recent trade functions
    def get_symbol_recent_trades(self, limit=None):
        if limit:
            return self.recent_trades_manager[-limit:]  # TODO
        else:
            return self.recent_trades_manager  # TODO

    # private functions
    # @staticmethod
    # def _has_candle_changed(candle_data, start_candle_time):
    #     return candle_data.time_candles_list[-1] < start_candle_time
    #
    # def _get_previous_candle_timestamp(self, time_frame):
    #     if time_frame in self.previous_candle_time:
    #         return self.previous_candle_time[time_frame]
    #     else:
    #         return None

    def candles_are_initialized(self, time_frame):
        if time_frame in self.symbol_candles and self.symbol_candles[time_frame].is_initialized:
            return True
        elif time_frame is None:
            return True
        return False

    def ticker_is_initialized(self) -> bool:
        return True if self.symbol_ticker is not None else False

    def get_symbol_prices(self, time_frame, limit=None, return_list=False):
        try:
            return self.get_candle_data(time_frame).get_symbol_prices(limit, return_list)
        except AttributeError:
            # if get_candle_data returned None: no candles on this timeframe
            self.logger.error(f"Trying retrieve candle data on {time_frame}: no candle for this time frame.")
            return None
