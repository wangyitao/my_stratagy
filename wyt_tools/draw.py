import pandas as pd
import numpy as np
from datetime import datetime
from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts import options as opts

df = pd.read_csv('../csv_files/data_fu888.SHFE.csv')
dates = df.iloc[1:][['Date']].values.tolist()
dates = [str(i[0]) for i in dates]
values = df.iloc[1:][['Open', 'Close', 'Low', 'High']].values.tolist()
volume = df.iloc[1:][['Volume']].values.tolist()
linregress = np.round(df.iloc[1:][['Linregress']].values, 2).tolist()
# print(linregress)
linregress_datas = []
for index, lin in enumerate(linregress):
    linregress_datas.append([index, lin[0], -1 if lin[0] < 0 else 1])
ema_fast = np.round(df.iloc[1:][['EmaFast']].values, 2).tolist()
ema_slow = np.round(df.iloc[1:][['EmaSlow']].values, 2).tolist()
print(len(values))
print(len(ema_fast))


def get_date(date):
    len_dates = len(dates)
    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    for i in range(len_dates - 1):
        start = datetime.strptime(dates[i], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(dates[i + 1], '%Y-%m-%d %H:%M:%S')
        if start < date < end:
            return str(format(end))


def draw_charts():
    # print(kline_data)
    kline = (
        Kline()
        .add_xaxis(dates)
        .add_yaxis(
            series_name="Dow-Jones index",
            y_axis=values,  # open close low high
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ec0000", color0="#00da3c"),
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                is_show=False, pos_bottom=10, pos_left="center"
            ),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False,
                    type_="inside",
                    xaxis_index=[0, 1],
                    range_start=98,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0, 1],
                    type_="slider",
                    pos_top="85%",
                    range_start=98,
                    range_end=100,
                ),
            ],
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(245, 245, 245, 0.8)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
            visualmap_opts=opts.VisualMapOpts(
                is_show=False,
                dimension=2,
                series_index=3,
                is_piecewise=True,
                pieces=[
                    {"value": 1, "color": "#00da3c"},
                    {"value": -1, "color": "#ec0000"},
                ],
            ),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
            brush_opts=opts.BrushOpts(
                x_axis_index="all",
                brush_link="all",
                out_of_brush={"colorAlpha": 0.1},
                brush_type="lineX",
            ),
        )
    )

    line = (
        Line()
        .add_xaxis(xaxis_data=dates)
        .add_yaxis(
            series_name="emafast",
            y_axis=ema_fast,
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="emaslow",
            y_axis=ema_slow,
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
    )
    # line.render('bbb.html')
    # print(chart_data["volumes"])
    bar = (
        Bar()
        .add_xaxis(dates)
        .add_yaxis(
            series_name="lin",
            y_axis=linregress_datas,
            xaxis_index=1,
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                grid_index=1,
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=False),
                split_number=20,
                min_="dataMin",
                max_="dataMax",
            ),
            yaxis_opts=opts.AxisOpts(
                grid_index=1,
                is_scale=True,
                split_number=2,
                axislabel_opts=opts.LabelOpts(is_show=False),
                axisline_opts=opts.AxisLineOpts(is_show=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )

    # Kline And Line
    overlap_kline_line = kline.overlap(line)

    # Grid Overlap + Bar
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1000px",
            height="800px",
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )
    grid_chart.add(
        overlap_kline_line,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="50%"),
    )
    grid_chart.add(
        bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="63%", height="16%"
        ),
    )

    grid_chart.render("base22.html")


if __name__ == "__main__":
    draw_charts()
