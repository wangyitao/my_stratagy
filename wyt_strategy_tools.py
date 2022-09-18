from datetime import datetime
from typing import Callable, Tuple, Union

import numpy as np
import talib
from vnpy_ctastrategy import (
    BarData,
    BarGenerator,
)

from vnpy.trader.constant import Interval
from vnpy.trader.utility import ArrayManager

"""
趋势跟踪类：
    均线(不推荐): sma ema ama
    震荡指标: rsi超买超卖  MACD柱放大
趋势突破类:
    通道: Donchian  Keltner Boll
    形态: 日内高低点  三角形态
信号过滤:
    趋势强度:ATR波动范围 STD标准差
    趋势方向:DMI过滤  CCI位置  RSI阈值
出场逻辑:
    反向信号 固定止盈  固定止损 移动止损


"""


class WytBarGenerator(BarGenerator):
    """n分钟bar"""

    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ) -> None:
        super().__init__(on_bar, window, on_window_bar, interval)
        self.last_minute_bar: BarData = None

    def update_bar(self, bar: BarData) -> None:
        """
        Update 1 minute bar into generator
        """
        if self.interval == Interval.MINUTE:
            self.update_bar_minute_window(bar)
        else:
            self.update_bar_hour_window(bar)

    def update_bar_minute_window(self, bar: BarData) -> None:
        """"""
        # If not inited, create window bar object
        if not self.window_bar:
            dt: datetime = bar.datetime.replace(second=0, microsecond=0)
            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price,
                bar.high_price
            )
            self.window_bar.low_price = min(
                self.window_bar.low_price,
                bar.low_price
            )

        # Update close price/volume/turnover into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += bar.volume
        self.window_bar.turnover += bar.turnover
        self.window_bar.open_interest = bar.open_interest

        self.interval_count += 1
        if self.last_minute_bar and bar.datetime.minute != self.last_minute_bar.datetime.minute:
            if not self.interval_count % self.window:
                self.interval_count = 0
                self.on_window_bar(self.window_bar)
                self.window_bar = None

        self.last_minute_bar = bar


class WytArrayManager(ArrayManager):
    def __init__(self, size: int = 100) -> None:
        super().__init__(size)

    # 扩展指标
    def donchian(
            self, n: int, array: bool = False) -> Union[
            Tuple[np.ndarray, np.ndarray],
            Tuple[float, float],
    ]:
        """
        Donchian Channel.
        """
        up: np.ndarray = talib.MAX(self.high, n)
        down: np.ndarray = talib.MIN(self.low, n)

        if array:
            return up, down
        return up[-1], down[-1]
