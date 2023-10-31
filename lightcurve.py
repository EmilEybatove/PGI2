from plotly_resampler.aggregation.plotly_aggregator_parser import PlotlyAggregatorParser
import numpy as np
from plotly_resampler.aggregation.aggregators import MinMaxAggregator
from plotly_resampler.aggregation import MedDiffGapHandler
from h5py import File
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import pandas as pd
from math import floor, ceil
import sys

app = Dash(__name__)


class Lightcurve:
    def __init__(self, filename="./mat/matlab.mat", max_n_samples=1000):
        self.filename = filename
        self.max_n_samples = max_n_samples
        file = File(filename)
        time = np.ravel(file.get("unixtime_dbl_global"))
        time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
        self.light = {
            "x": time,
            "y": np.ravel(file.get("lightcurvesum_global")),
            "max_n_samples": max_n_samples,
            "downsampler": MinMaxAggregator(),
            "gap_handler": MedDiffGapHandler()
        }
        file.close()
        self.size = time.size
        data = self.update()
        self.figure = go.Figure(data=go.Scattergl(x=data[0], y=data[1]))

        self.dcc = html.Div([
            dcc.Graph(id="lightcurve", figure=self.figure, style={'float': 'left', "width": "90%"}),
            html.Div(style={'float': 'right'})
        ])

        @app.callback(Output('lightcurve', 'figure'),
                      Input('lightcurve', 'relayoutData'))
        def update_lightcurve(relayoutData):
            data = self.update(relayoutData)
            self.figure = go.Figure(data=go.Scattergl(x=data[0], y=data[1]))
            if relayoutData:
                self.figure.plotly_relayout(relayoutData)
            return self.figure

    def update(self, relayoutData=None):

        start, end = 0, self.size

        if relayoutData:
            if "xaxis.range[0]" in relayoutData:
                start, end = PlotlyAggregatorParser.get_start_end_indices(self.light,
                                                                          start=relayoutData["xaxis.range[0]"],
                                                                          end=relayoutData["xaxis.range[1]"],
                                                                          axis_type="date")

        x, y, indexes = PlotlyAggregatorParser.aggregate(self.light, start, end)
        return x, y


lightcurve = Lightcurve()

app.layout = html.Div([
    lightcurve.dcc
])

app.run(host='127.0.0.1', port=5000, debug=True)

# app.run(host=sys.argv[1], port=int(sys.argv[2]))
