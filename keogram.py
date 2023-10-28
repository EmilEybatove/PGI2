from plotly_resampler.aggregation.plotly_aggregator_parser import PlotlyAggregatorParser
import numpy as np
from plotly_resampler.aggregation.aggregators import MinMaxAggregator
from plotly_resampler.aggregation import MedDiffGapHandler
from h5py import File
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import sys

app = Dash(__name__)


class Keogram:
    def __init__(self, filename="./mat/matlab.mat", max_n_samples=1000):
        self.filename = filename
        file = File(filename)
        time = np.ravel(file.get("unixtime_dbl_global"))
        time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
        diag_global = file.get("diag_global")
        diag_global = np.rot90(diag_global)
        file.close()
        self.size = time.size
        self.first_diag = {
            "x": time,
            "y": diag_global[0],
            "max_n_samples": max_n_samples,
            "downsampler": MinMaxAggregator(),
            "gap_handler": MedDiffGapHandler()
        }
        self.data = diag_global[1:]
        data = self.update()
        self.figure = go.Figure(data=go.Heatmap(x=data[0], z=data[1]))
        self.dcc = dcc.Graph(id="keogram", figure=self.figure)

    def update(self, relayoutData=None):
        res = []
        start, end = 0, self.size
        if relayoutData and "xaxis.range[0]" in relayoutData:

            start, end = PlotlyAggregatorParser.get_start_end_indices(self.first_diag,
                                                                      start=relayoutData["xaxis.range[0]"],
                                                                      end=relayoutData["xaxis.range[1]"],
                                                                      axis_type="date")

        x, y, indexes = PlotlyAggregatorParser.aggregate(self.first_diag, start, end)
        res.append(y)

        for i in range(15):
            res.append(self.data[i][indexes])
        return x, res


keogram = Keogram()

app.layout = html.Div([
    keogram.dcc
])


@app.callback(Output('keogram', 'figure'),
              Input('keogram', 'relayoutData'))
def update_keogram(relayoutData):
    data = keogram.update(relayoutData)
    return go.Figure(data=go.Heatmap(x=data[0], z=data[1]))


# app.run(host='127.0.0.1', port=5050, debug=True)

app.run(host=sys.argv[1], port=int(sys.argv[2]))