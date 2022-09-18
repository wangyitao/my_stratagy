from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class WytDoubleMaStrategy(CtaTemplate):
    """
    双均线系统
    1、均线金叉买入
    2、均线死叉卖出
    """

    author = "王以涛"

    # 定义参数
    fast_window = 10
    slow_window = 20
    fixed_size = 1

    # 定义变量
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0

    parameters = [
        "fast_window",
        "slow_window", "fixed_size"
    ]
    variables = ["fast_ma0",
                 "fast_ma1",
                 "slow_ma0",
                 "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

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
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算技术指标
        fast_ma = am.sma(self.fast_window, array=True)
        self.fast_ma0 = fast_ma[-1]
        self.fast_ma1 = fast_ma[-2]

        slow_ma = am.sma(self.slow_window, array=True)
        self.slow_ma0 = slow_ma[-1]
        self.slow_ma1 = slow_ma[-2]

        # 判断均线交叉
        # 金叉
        cross_over = self.fast_ma0 >= self.slow_ma0 and self.fast_ma1 < self.slow_ma1
        # 死叉
        cross_below = self.fast_ma0 <= self.slow_ma0 and self.fast_ma1 > self.slow_ma1

        if cross_over:
            price = bar.close_price + 5
            if not self.pos:
                self.buy(price, self.fixed_size)
            elif self.pos < 0:
                self.cover(price, self.fixed_size)
                self.buy(price, self.fixed_size)
        elif cross_below:
            price = bar.close_price - 5
            if not self.pos:
                self.short(price, self.fixed_size)
            elif self.pos > 0:
                self.sell(price, self.fixed_size)
                self.short(price, self.fixed_size)

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
