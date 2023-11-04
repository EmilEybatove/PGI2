import plotly.graph_objects as go
from dash.html import Div, Em, Span, A, Img, Br
import pandas as pd
from plotly_resampler.aggregation.plotly_aggregator_parser import PlotlyAggregatorParser
import numpy as np
from plotly_resampler.aggregation.aggregators import MinMaxAggregator
from plotly_resampler.aggregation import MedDiffGapHandler
from h5py import File
from dash import Dash, html, dcc, Input, Output
import sys
from math import floor, ceil

app = Dash(__name__)

filename = "./mat/matlab.mat"
file = File(filename)
time = np.ravel(file.get("unixtime_dbl_global"))
time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
size = time.size


class Lightcurve:
    def __init__(self, max_n_samples=1000):
        self.max_n_samples = max_n_samples
        self.indexes = None
        self.light = {
            "x": time,
            "y": np.ravel(file.get("lightcurvesum_global")),
            "max_n_samples": max_n_samples,
            "downsampler": MinMaxAggregator(),
            "gap_handler": MedDiffGapHandler()
        }
        self.size = time.size
        data = self.update()
        self.figure = go.Figure(data=go.Scattergl(x=data[0], y=data[1]),
                                layout=go.Layout(margin={'t': 30, 'l': 20, 'b': 20, 'r': 50}))

        self.dcc = html.Div([
            dcc.Graph(id="lightcurve", figure=self.figure, style={'float': 'left', "width": "90%"}),
            html.Div(style={'float': 'right'})
        ])

        @app.callback(Output('lightcurve', 'figure'),
                      Output('keogram', 'relayoutData'),
                      Input('lightcurve', 'relayoutData'))
        def update_lightcurve(relayoutData):
            data = self.update(relayoutData)
            self.figure = go.Figure(data=go.Scattergl(x=data[0], y=data[1]),
                                    layout=go.Layout(margin={'t': 30, 'l': 20, 'b': 20, 'r': 70}))
            res = None
            if relayoutData:
                # TODO Возникают проблемы, если масштабировать тоьлко по ондой оси. Функция plotly_relayout считает это перезагрузкой графика по отсутствующей оси. Нужно понять, каким образом он берёт данные для построения этого, если это происходит после аггрегирования
                self.figure.plotly_relayout(relayoutData)
                if "xaxis.range[0]" in relayoutData:
                    res = {
                        "xaxis.range[0]": relayoutData["xaxis.range[0]"],
                        "xaxis.range[1]": relayoutData["xaxis.range[1]"]
                    }
                if "autosize" in relayoutData or "yaxis.autorange" in relayoutData:
                    res = relayoutData
            return self.figure, res

    def update(self, relayoutData=None):

        start, end = 0, self.size

        if relayoutData:
            if "xaxis.range[0]" in relayoutData:
                start, end = PlotlyAggregatorParser.get_start_end_indices(self.light,
                                                                          start=relayoutData["xaxis.range[0]"],
                                                                          end=relayoutData["xaxis.range[1]"],
                                                                          axis_type="date")

        x, y, self.indexes = PlotlyAggregatorParser.aggregate(self.light, start, end)
        self.indexes += start
        return x, y


class Keogram:
    def __init__(self, max_n_samples=1000):
        self.max_n_samples = max_n_samples
        diag_global = file.get("diag_global")
        diag_global = np.rot90(diag_global)
        self.min = diag_global.min(initial=0)
        self.max = diag_global.max(initial=0)
        self.size = time.size
        self.yrange = [0, 15]
        self.data = diag_global
        data = self.update()
        self.figure = go.Figure(data=go.Heatmap(x=data[0], z=data[1]),
                                layout=go.Layout(margin={'t': 30, 'l': 20, 'b': 20, 'r': 20}))
        self.slider = dcc.RangeSlider(self.min,
                                      self.max,
                                      value=[self.min, self.max],
                                      step=100,
                                      vertical=True,
                                      marks=None,
                                      tooltip={"placement": "left", "always_visible": True},
                                      id="keogram_slider")
        self.dcc = html.Div([
            dcc.Graph(id="keogram", figure=self.figure, style={'float': 'left', "width": "90%"}),
            html.Div(self.slider, style={'float': 'right'})
        ])

        @app.callback(
            Output('keogram', 'figure', allow_duplicate=True),
            Input('keogram_slider', 'value'), prevent_initial_call=True)
        def update_minmax(value):
            self.min = value[0]
            self.max = value[1]
            return self.figure.update_traces({"zmin": self.min, "zmax": self.max})

        @app.callback(Output('keogram', 'figure'),
                      Output('lightcurve', 'relayoutData'),
                      Input('keogram', 'relayoutData'))
        def update_keogram(relayoutData):
            data = keogram.update(relayoutData)
            self.yrange = data[2]
            self.figure = go.Figure(data=go.Heatmap(x=data[0], z=data[1], zmin=self.min, zmax=self.max),
                                    layout_yaxis_range=data[2],
                                    layout=go.Layout(margin={'t': 30, 'l': 20, 'b': 20, 'r': 20}))
            res = None
            if relayoutData:
                if "xaxis.range[0]" in relayoutData:
                    res = {
                        "xaxis.range[0]": relayoutData["xaxis.range[0]"],
                        "xaxis.range[1]": relayoutData["xaxis.range[1]"]
                    }
                if "autosize" in relayoutData or "yaxis.autorange" in relayoutData:
                    res = relayoutData
            return self.figure, res

    def update(self, relayoutData=None):

        res = []
        start, end = 0, self.size
        min_y, max_y = self.yrange[0], self.yrange[1]
        first = {
            "x": time,
            "y": self.data[0],
            "max_n_samples": self.max_n_samples,
            "downsampler": MinMaxAggregator(),
            "gap_handler": MedDiffGapHandler()
        }

        if relayoutData:
            if "xaxis.range[0]" in relayoutData:
                start, end = PlotlyAggregatorParser.get_start_end_indices(first,
                                                                          start=relayoutData["xaxis.range[0]"],
                                                                          end=relayoutData["xaxis.range[1]"],
                                                                          axis_type="date")
            if 'yaxis.range[0]' in relayoutData:
                min_y = max(0, floor(relayoutData["yaxis.range[0]"]))
                max_y = min(15, ceil(relayoutData["yaxis.range[1]"]))

            if "autosize" in relayoutData or "yaxis.autorange" in relayoutData:
                min_y, max_y = 0, 15
        x = None

        for i in range(16):
            diag = {
                "x": time,
                "y": self.data[i],
                "max_n_samples": self.max_n_samples,
                "downsampler": MinMaxAggregator(),
                "gap_handler": MedDiffGapHandler()
            }
            x, y, indexes = PlotlyAggregatorParser.aggregate(diag, start, end)
            res.append(y)

        return x, res, [min_y, max_y]


class Frame:
    def __init__(self, lightcurve):
        self.lightcurve = lightcurve
        self.pdm_2d_rot_global = file.get("pdm_2d_rot_global")
        self.figure = go.Figure()
        self.index = 0
        self.dcc = html.Div([
            dcc.Graph(id="frame", figure=self.figure, style={'float': 'left', "width": "90%"}),
            html.Div(style={'float': 'right'})
        ])

        @app.callback(
            Output('frame', 'figure'),
            Input('lightcurve', 'clickData'),
            Input('lightcurve', 'relayoutData'))
        def lightcurbe_click_event(value, relayoutData):
            if value:
                self.index = lightcurve.indexes[value["points"][0]["pointIndex"]]
            elif relayoutData:
                self.index = lightcurve.indexes[0]
            self.figure = go.Figure(data=go.Heatmap(z=self.pdm_2d_rot_global[self.index]),
                                    layout=go.Layout(margin={'t': 30, 'l': 20, 'b': 20, 'r': 20}))
            self.figure.update_layout(title={"text": str(time[self.index]).split("T")[1], 'x': 0.5})
            return self.figure


head_bar = Div(
    className="head-bar",
    children=[
        Div(
            className="center",
            children=[
                Div(
                    className="loc",
                    children=[
                        Em("ЛЕНИНСКИЕ ГОРЫ Д.1, СТР. 6"),
                        Span("|"),
                        A(
                            href="https://uhecr.sinp.msu.ru/ru/kontakty.html",
                            children="Посмотреть на карте"
                        )
                    ]
                ),
            ]
        )
    ]
)

head_center = Div(
    className="center",
    children=A(
        href="https://uhecr.sinp.msu.ru/",
        className="logo",
        children=[
            Img(src="/assets/images/logo.png"),
            "Лаборатория космических лучей",
            Br(),
            " предельно высоких энергий НИИЯФ МГУ"
        ]
    )
)

head = Div(
    className="head",
    children=[head_bar, head_center]
)

lightcurve = Lightcurve()
keogram = Keogram()
frame = Frame(lightcurve)

app.layout = Div([
    head,
    lightcurve.dcc,
    keogram.dcc,
    frame.dcc
])

if __name__ == "__main__":
    app.run('127.0.0.1', port=5001)  # debug=True
