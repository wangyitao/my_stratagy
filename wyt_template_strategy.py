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


class WytTemplateStrategy(CtaTemplate):
    """
    策略模板系统
    """

    author = "王以涛"

    # 定义参数
    window = 5

    # 定义变量

    parameters = []
    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

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

        # 更新图形界面
        self.put_event()

    def on_xmin_bar(self, bar: BarData):
        pass

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
