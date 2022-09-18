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


class WytCuatroStrategy(CtaTemplate):
    """
    信号:5min boll突破
    过滤:1、5min RSI进入极值区 2、15min 均线的相对位置
    离场:5min 基于boll宽度移动止损
    """

    author = "王以涛"

    # boll参数
    boll_window = 20
    boll_dev = 1.8
    # rsi参数
    rsi_window = 14
    rsi_signal = 20
    # 均线参数
    fast_window = 4
    slow_window = 26
    # 移动止损参数
    trailing_long = 0.4
    trailing_short = 0.6
    # 交易手数
    fixed_size = 1
    # 定义变量
    boll_up = 0
    boll_down = 0
    rsi_value = 0
    rsi_long = 0
    rsi_short = 0
    fast_ma = 0
    slow_ma = 0
    ma_trend = 0  # 长周期方向
    # 移动止损最高和最低价格
    intra_trade_high = 0
    intra_trade_low = 0
    # 空头和多头的止损价格
    long_stop = 0
    short_stop = 0

    parameters = [
        "boll_window",
        "boll_dev",
        "rsi_window",
        "rsi_signal",
        "fast_window",
        "slow_window",
        "trailing_short",
        "trailing_long",
        "fixed_size"
    ]
    variables = [
        "boll_up",
        "boll_down",
        "rsi_value",
        "rsi_long",
        "rsi_short",
        "fast_ma",
        "slow_ma",
        "ma_trend",
        "intra_trade_high",
        "intra_trade_low",
        "long_stop",
        "short_stop"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # rsi超买超卖区域
        self.rsi_long = 50 + self.rsi_signal
        self.rsi_short = 50 + self.rsi_signal

        self.bg_5m = WytBarGenerator(
            self.on_bar,
            window=5,
            on_window_bar=self.on_5min_bar,
            interval=Interval.MINUTE
        )
        self.bg_15m = WytBarGenerator(
            self.on_bar,
            window=15,
            on_window_bar=self.on_15min_bar,
            interval=Interval.MINUTE
        )
        self.am5 = WytArrayManager()
        self.am15 = WytArrayManager()

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
        # tick只要update一次就行了
        self.bg_5m.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg_5m.update_bar(bar)
        self.bg_15m.update_bar(bar)

        # 更新图形界面
        self.put_event()

    def on_5min_bar(self, bar: BarData):
        self.cancel_all()
        self.am5.update_bar(bar)
        if not self.am5.inited or not self.am15.inited:
            return

        self.boll_up, self.boll_down = self.am5.boll(
            self.boll_window, self.boll_dev)
        self.rsi_value = self.am5.rsi(self.rsi_window)

        boll_width = self.boll_up - self.boll_down

        if self.pos == 0:
            # 初始化移动止损最高点和最低点
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price
            self.long_stop = 0
            self.short_stop = 0

            # 通过长周期和rsi过滤
            if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
                self.buy(self.boll_up, self.fixed_size, stop=True)
            if self.ma_trend < 0 and self.rsi_value <= self.rsi_short:
                self.short(self.boll_down, self.fixed_size, stop=True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.long_stop = self.intra_trade_high - self.trailing_long * boll_width
            self.sell(self.long_stop, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.intra_trade_high = min(self.intra_trade_low, bar.low_price)
            self.short_stop = self.intra_trade_low + self.trailing_short * boll_width
            self.cover(self.short_stop, abs(self.pos), stop=True)

        # 更新图形界面
        self.put_event()

    def on_15min_bar(self, bar: BarData):
        """15min 均线判断买卖方向"""
        self.am15.update_bar(bar)
        if not self.am15.inited:
            return

        self.fast_ma = self.am15.sma(self.fast_window)
        self.slow_ma = self.am15.sma(self.slow_window)

        if self.fast_ma > self.slow_ma:
            self.ma_trend = 1
        elif self.fast_ma < self.slow_ma:
            self.ma_trend = -1
        else:
            self.ma_trend = 0

        # 更新图形界面
        self.put_event()

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
