import csv
import os
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
)


from vnpy.trader.constant import Direction, Interval, Offset

from .wyt_strategy_tools import WytBarGenerator, WytArrayManager, get_vt_step_and_num


class WytRbStrategy(CtaTemplate):
    """
    策略模板系统
    """

    author = "王以涛"

    # 定义参数
    bar_to_csv = 0
    window = 23
    linregress_window = 13
    ema_fast_window = 10
    ema_slow_window = 20
    fixed_size = 1
    # 固定点位移动止损
    stop_price = 500

    # 定义变量
    linregress_value = 0
    ema_fast_value = 0
    ema_slow_value = 0
    # 移动止损最高和最低价格
    intra_trade_high = 0
    intra_trade_low = 0
    # 空头和多头的止损价格
    long_stop = 0
    short_stop = 0

    parameters = [
        'bar_to_csv',
        'window',
        "linregress_window",
        "ema_slow_window",
        "ema_fast_window",
        "stop_price",
        "fixed_size"
    ]
    variables = [
        "linregress_value",
        "intra_trade_high",
        "intra_trade_low",
        "long_stop",
        "short_stop"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        # vt_symbol,datetime,open,high,close,low,volume
        self.csv_name = f'data_{vt_symbol}.csv'
        self.csv_save_path = '/home/felix/桌面/vnpy_all/vnpy-3.3.0/strategies/csv_files/'
        if self.bar_to_csv:
            data = ['vt_symbol', 'Date', 'Open',
                    'Close', 'Low', 'High', 'Volume', 'Linregress', 'EmaFast', 'EmaSlow']
            with open(os.path.join(self.csv_save_path, self.csv_name), 'w') as csvfile:
                writer = csv.writer(csvfile, lineterminator='\n')
                writer.writerow(data)
        # 价格跳动，合约乘数
        self.vt_step, self.vt_num = get_vt_step_and_num(vt_symbol)
        self.one_price = self.vt_step * self.vt_num / self.vt_step
        # 开多成交价
        self.long_entry = None
        # 开空成交价
        self.short_entry = None
        # 平多成交价
        self.sell_entry = None
        # 平空成交价
        self.cover_entry = None

        self.last_value = None
        self.last_ema_fast_value = None
        self.last_ema_slow_value = None
        self.ema_flag = 0

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
        self.cancel_all()
        self.bg_xm.update_bar(bar)

        if self.pos > 0:
            if bar.close_price - self.long_entry > self.stop_price:
                self.long_stop = self.long_entry + self.one_price * 3
            self.sell(self.long_stop, abs(self.pos), stop=True)
        elif self.pos < 0:
            if self.short_entry - bar.close_price > self.stop_price:
                self.short_stop = self.short_entry - self.one_price * 3
            self.cover(self.short_stop, abs(self.pos), stop=True)

        # 更新图形界面
        self.put_event()

    def on_xmin_bar(self, bar: BarData):
        self.cancel_all()
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return
        # 均值回归的计算
        self.linregress_value = am.linregress(self.linregress_window)
        self.ema_fast_value = am.ema(self.ema_fast_window)
        self.ema_slow_value = am.ema(self.ema_slow_window)

        # 如果不存在上一次的值
        if not self.last_value and not self.last_ema_fast_value and not self.last_ema_slow_value:
            self.last_value = self.linregress_value
            self.last_ema_fast_value = self.ema_fast_value
            self.last_ema_slow_value = self.ema_slow_value
            return

        if self.ema_fast_value > self.ema_slow_value and self.last_ema_fast_value <= self.last_ema_slow_value:
            if self.ema_fast_value - self.last_ema_fast_value > self.ema_slow_value - self.last_ema_slow_value:
                self.ema_flag = 1
        if self.ema_fast_value < self.ema_slow_value and self.last_ema_fast_value >= self.last_ema_slow_value:
            if self.last_ema_fast_value - self.ema_fast_value > self.last_ema_slow_value - self.ema_slow_value:
                self.ema_flag = -1
        # 穿过0轴开
        if self.pos == 0:
            if (self.linregress_value > 0 and self.last_value < 0) or (self.linregress_value > self.last_value > 0):
                if self.ema_flag == 1:
                    self.buy(bar.close_price, self.fixed_size)
            elif (self.linregress_value < 0 and self.last_value > 0) or (self.linregress_value < self.last_value < 0):
                if self.ema_flag == -1:
                    self.short(bar.close_price, self.fixed_size)
        elif self.pos > 0:
            if self.linregress_value < self.last_value:
                self.sell(bar.close_price, abs(self.pos))
            else:
                self.sell(self.long_stop, abs(self.pos), stop=True)

        elif self.pos < 0:
            if self.linregress_value > self.last_value:
                self.cover(bar.close_price, abs(self.pos))
            else:
                self.cover(self.short_stop, abs(self.pos), stop=True)

        self.last_value = self.linregress_value
        self.last_ema_fast_value = self.ema_fast_value
        self.last_ema_slow_value = self.ema_slow_value
        self.put_event()
        if self.bar_to_csv:
            data_tmp = [bar.vt_symbol, '{:%Y-%m-%d %H:%M:%S}'.format(bar.datetime), bar.open_price, bar.close_price,
                        bar.low_price, bar.high_price, bar.volume, self.linregress_value, self.ema_fast_value, self.ema_slow_value]
            self.save_bar_to_csv(data_tmp)

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """

        if trade.offset == Offset.OPEN:
            # 开仓
            if trade.direction == Direction.LONG:
                # 开多仓成交
                self.long_entry = trade.price
                # 多头移动止损
                self.long_stop = self.long_entry - self.stop_price / self.one_price
                self.sell(self.long_stop, abs(self.pos), stop=True)
            elif trade.direction == Direction.SHORT:
                # 开空仓成交
                self.short_entry = trade.price
                # 空头移动止损
                self.short_stop = self.short_entry + self.stop_price / self.one_price
                self.cover(self.short_stop, abs(self.pos), stop=True)

        elif trade.offset == Offset.CLOSE:
            # 平仓
            if trade.direction == Direction.SHORT:
                # 平多仓成交
                self.sell_entry = trade.price
                self.cancel_all()
            elif trade.direction == Direction.LONG:
                # 平空仓成交
                self.cover_entry = trade.price
                self.cancel_all()
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass

    def save_bar_to_csv(self, data):
        '''保存k线数据'''
        if self.bar_to_csv:
            with open(os.path.join(self.csv_save_path, self.csv_name), 'a') as csvfile:
                writer = csv.writer(csvfile, lineterminator='\n')
                writer.writerow(data)
