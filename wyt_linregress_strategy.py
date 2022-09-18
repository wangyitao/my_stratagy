from scipy.stats import linregress
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
)

from vnpy.trader.constant import Interval

from .wyt_strategy_tools import WytBarGenerator, WytArrayManager


class WytLinregressStrategy(CtaTemplate):
    """
    均值回归策略
    """

    author = "王以涛"

    # 定义参数
    # 均值回归周期
    linregress_window = 20
    window = 20
    fixed_size = 1

    # 定义变量
    # 均值
    linregress_value = 0

    parameters = [
        "linregress_window",
        "window",
        "fixed_size"
    ]
    variables = [
        "linregress_value"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.last_value = None

        self.bg_xm = WytBarGenerator(
            self.on_bar,
            window=self.window,
            on_window_bar=self.on_xmin_bar,
            interval=Interval.MINUTE
        )
        self.am = WytArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg_xm.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_xm.update_bar(bar)

    def on_xmin_bar(self, bar: BarData):
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return
        # 均值回归的计算
        high_am = max(am.high[-self.linregress_window:])
        low_am = min(am.low[-self.linregress_window:])
        avg_value = sum([sum([high_am, low_am]) / 2,
                        am.sma(self.linregress_window)]) / 2

        x = [range(self.linregress_window)]
        y = am.close[-self.linregress_window:] - avg_value
        val = linregress(x, y)
        self.linregress_value = val.intercept + val.slope * self.linregress_window

        # 如果不存在上一次的值
        if not self.last_value:
            self.last_value = self.linregress_value
            return

        # 穿过0轴开
        if self.pos == 0:
            if self.linregress_value > 0 and self.last_value < 0:
                self.buy(bar.close_price, self.fixed_size)
            elif self.linregress_value < 0 and self.last_value > 0:
                self.short(bar.close_price, self.fixed_size)
        elif self.pos > 0:
            if self.linregress_value < self.last_value:
                self.sell(bar.close_price, abs(self.pos))
        elif self.pos < 0:
            if self.linregress_value > self.last_value:
                self.cover(bar.close_price, abs(self.pos))

        self.last_value = self.linregress_value

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
