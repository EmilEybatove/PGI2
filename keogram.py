import sys
from math import floor, ceil

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
from h5py import File
from plotly_resampler.aggregation import MedDiffGapHandler
from plotly_resampler.aggregation.aggregators import MinMaxAggregator
from plotly_resampler.aggregation.plotly_aggregator_parser import PlotlyAggregatorParser

app = Dash(__name__)


class Keogram:
    def __init__(self, filename="./mat/matlab.mat", max_n_samples=1000):
        self.filename = filename
        self.max_n_samples = max_n_samples
        file = File(filename)
        time = np.ravel(file.get("unixtime_dbl_global"))
        self.time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
        diag_global = file.get("diag_global")
        diag_global = np.rot90(diag_global)
        file.close()
        self.min = diag_global.min(initial=0)
        self.max = diag_global.max(initial=0)
        self.size = time.size
        self.yrange = [0, 15]
        self.data = diag_global
        data = self.update()
        self.figure = go.Figure(data=go.Heatmap(x=data[0], z=data[1]))
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
            html.Div(self.slider, style={'float': 'right'}),
        ])

        @app.callback(
            Output('keogram', 'figure', allow_duplicate=True),
            Input('keogram_slider', 'value'), prevent_initial_call=True)
        def update_minmax(value):
            self.min = value[0]
            self.max = value[1]
            return self.figure.update_traces({"zmin": self.min, "zmax": self.max})

        @app.callback(Output('keogram', 'figure'),
                      Input('keogram', 'relayoutData'))
        def update_keogram(relayoutData):
            data = self.update(relayoutData)
            self.yrange = data[2]
            self.figure = go.Figure(data=go.Heatmap(x=data[0], z=data[1], zmin=self.min, zmax=self.max),
                                    layout_yaxis_range=data[2])
            return self.figure

    def update(self, relayoutData=None):
        res = []
        start, end = 0, self.size
        min_y, max_y = self.yrange[0], self.yrange[1]
        first = {
            "x": self.time,
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
                "x": self.time,
                "y": self.data[i],
                "max_n_samples": self.max_n_samples,
                "downsampler": MinMaxAggregator(),
                "gap_handler": MedDiffGapHandler()
            }
            x, y, indexes = PlotlyAggregatorParser.aggregate(diag, start, end)
            res.append(y)

        return x, res, [min_y, max_y]


keogram = Keogram()

app.layout = html.Div([
    keogram.dcc
])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.run(host=sys.argv[1], port=int(sys.argv[2]), debug=True)
    else:
        print(sys.argv)
        app.run(host="localhost", port=5005, debug=True)
