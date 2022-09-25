from datetime import datetime
import re
from scipy.stats import linregress as scipy_linregress
from typing import Callable

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


def get_vt_step_and_num(vt):
    vts = {"i": [0.5, 100], "cu": [10, 5], "ni": [10, 1], "sn": [10, 1], "bc": [10, 5], "au": [0.02, 1000], "ag": [1, 15], "lh": [5, 16], "sc": [0.1, 1000], "ru": [5, 10], "nr": [5, 10], "jm": [0.5, 60], "j": [0.5, 100], "ss": [5, 5], "al": [5, 5], "zn": [5, 5], "pb": [5, 5], "cf": [5, 5], "cy": [5, 5], "cj": [5, 5], "b": [1, 10], "bu": [1, 10], "ma": [1, 10], "eg": [1, 10], "fu": [1, 10], "rb": [
        1, 10], "hc": [1, 10], "a": [1, 10], "m": [1, 10], "oi": [1, 10], "rm": [1, 10], "c": [1, 10], "cs": [1, 10], "jd": [1, 10], "sr": [1, 10], "ap": [1, 10], "pf": [2, 5], "sf": [2, 5], "sm": [2, 5], "pk": [2, 5], "ta": [2, 5], "l": [1, 5], "pp": [1, 5], "v": [1, 5], "eb": [1, 5], "fg": [1, 20], "ur": [1, 20], "sa": [1, 20], "pg": [1, 20], "sp": [2, 10], "y": [2, 10], "p": [2, 10]}
    need_vt = re.findall('([a-z]+)', str(vt).lower())
    if need_vt:
        return vts.get(need_vt[0], [])


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
    def linregress(self, n: int):
        """
        均值回归
        """
        high_am = max(self.high[-n:])
        low_am = min(self.low[-n:])
        avg_value = sum([sum([high_am, low_am]) / 2, self.sma(n)]) / 2
        x = [range(n)]
        y = self.close[-n:] - avg_value
        val = scipy_linregress(x, y)
        linregress_value = val.intercept + val.slope * n

        return linregress_value
