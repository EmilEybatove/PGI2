import plotly.graph_objects as go
from dash.html import Div, Em, Span, A, Img, Br, P, Button, H4
import pandas as pd
from plotly_resampler.aggregation.plotly_aggregator_parser import PlotlyAggregatorParser
import numpy as np
from plotly_resampler.aggregation.aggregators import MinMaxAggregator
from plotly_resampler.aggregation import MedDiffGapHandler
from h5py import File
from dash import Dash, html, dcc, Input, Output
import os
from math import floor, ceil
import dash_bootstrap_components as dbc
from nested_dropdown_menu import nested_dropdown_menu
import sys

JQUERY_CDN_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js'

dirname = "a"
if len(sys.argv) > 1:
    dirname = sys.argv[3]


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

        start, end = 0, size

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
        self.yrange = [0, 15]
        self.data = diag_global
        data = self.update()
        self.figure = go.Figure(data=go.Heatmap(x=data[0], z=data[1]),
                                layout=go.Layout(margin={'t': 30, 'l': 20, 'b': 20, 'r': 20}))
        print(f"min, max: ", self.min, self.max)
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
            html.Div(self.slider, style={'float': 'right'}, id="slider_id")
        ])

        @app.callback(
            Output('keogram', 'figure', allow_duplicate=True),
            Input('keogram_slider', 'value'), prevent_initial_call=True)
        def update_minmax(value):
            self.min = value[0]
            self.max = value[1]
            return self.figure.update_traces({"zmin": self.min, "zmax": self.max})

        @app.callback(Output('keogram', 'figure'),
                      Output('lightcurve', 'relayoutData', allow_duplicate=True),
                      Input('keogram', 'relayoutData'), prevent_initial_call=True)
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
        start, end = 0, size
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
            dcc.Graph(id="frame", figure=self.figure, style={"display": "table", "margin": "0 auto"})
        ])

        @app.callback(
            Output('frame', 'figure', allow_duplicate=True),
            Input('lightcurve', 'clickData'), prevent_initial_call=True)
        def lightcurbe_click_event(value):
            if value:
                self.index = lightcurve.indexes[value["points"][0]["pointIndex"]]
                self.update()

            return self.figure

        @app.callback(
            Output('frame', 'figure', allow_duplicate=True),
            Input('lightcurve', 'relayoutData'), prevent_initial_call=True)
        def lightcurbe_relayout_event(relayoutData):
            if relayoutData:
                self.index = lightcurve.indexes[0]
                self.update()
            return self.figure

    def update(self):
        self.figure = go.Figure(data=go.Heatmap(z=self.pdm_2d_rot_global[self.index]),
                                layout=go.Layout(margin={'t': 30, 'l': 20, 'b': 20, 'r': 20}))
        self.figure.update_layout(title={"text": str(time[self.index]).split("T")[1],
                                         "x": 0.5},
                                  width=700,
                                  height=700)


filename = None


def parse_dir(dir, start_dir):
    global filename
    res = []
    for name in os.listdir(dir):
        if os.path.isfile(f"{dir}/{name}"):
            if not filename:
                filename = f"{dir}/{name}"
            res.append({'label': name, "href": f"{dir}/{name}".lstrip(start_dir)})
        else:
            res.append({'label': name, "children": parse_dir(f"{dir}/{name}", start_dir)})
    return res


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

app = Dash(__name__,
           external_scripts=[JQUERY_CDN_URL],
           external_stylesheets=[dbc.themes.BOOTSTRAP]
           )

# filename = "./mat/matlab.mat"


dropdown = html.Div([dcc.Location(id='url', refresh=False),
                     nested_dropdown_menu(
                         label='files',
                         menu_structure=parse_dir(dirname, dirname)
                     ),
                     Div(id='file')
                     ],
                    style={"float": "left", "width": "20%"},
                    )

file = File(filename)
time = np.ravel(file.get("unixtime_dbl_global"))
time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
size = time.size

lightcurve = Lightcurve()
keogram = Keogram()
frame = Frame(lightcurve)

main = html.Div([
    lightcurve.dcc,
    keogram.dcc,
    frame.dcc
], style={'float': 'right', "width": "80%"})

app.layout = Div([
    head,
    dropdown,
    main
])


@app.callback(
    Output('file', 'children'),
    Output('lightcurve', 'relayoutData', allow_duplicate=True),
    Output("slider_id", "children"),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def update_output(pathname):
    global filename, file, time, size

    if pathname not in ("/", "\\"):

        filename = dirname + pathname
        file = File(filename)
        time = np.ravel(file.get("unixtime_dbl_global"))
        time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
        size = time.size
        lightcurve.indexes = None
        lightcurve.light = {
            "x": time,
            "y": np.ravel(file.get("lightcurvesum_global")),
            "max_n_samples": lightcurve.max_n_samples,
            "downsampler": MinMaxAggregator(),
            "gap_handler": MedDiffGapHandler()
        }

        diag_global = file.get("diag_global")
        diag_global = np.rot90(diag_global)
        keogram.min = diag_global.min(initial=0)
        keogram.max = diag_global.max(initial=0)
        keogram.yrange = [0, 15]
        keogram.data = diag_global

        frame.pdm_2d_rot_global = file.get("pdm_2d_rot_global")
        frame.index = 0

        keogram.slider = dcc.RangeSlider(keogram.min,
                                         keogram.max,
                                         value=[keogram.min, keogram.max],
                                         step=100,
                                         vertical=True,
                                         marks=None,
                                         tooltip={"placement": "left", "always_visible": True},
                                         id="keogram_slider")
        print(f"min, max: ", keogram.min, keogram.max)

    return Div([
        Br(),
        H4(f'Скачать файл'),
        Button(pathname, id="download-button", className="btn btn-primary"),
        dcc.Download(id="download-current-file")
    ]), {'autosize': True}, keogram.slider


@app.callback(
    Output("download-current-file", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def get_data(n_click):
    return dcc.send_file(filename)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.run(host=sys.argv[1], port=int(sys.argv[2]))
    else:
        print(sys.argv)
        app.run(host="localhost", port=5002, debug=True)
