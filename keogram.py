from plotly_resampler.aggregation.plotly_aggregator_parser import PlotlyAggregatorParser
import numpy as np
from plotly_resampler.aggregation.aggregators import MinMaxAggregator
from plotly_resampler.aggregation import MedDiffGapHandler
from h5py import File
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import time
from datetime import datetime

app = Dash(__name__)


# ./mat/2022-10-05-18_32-19_32.mat


class Keogram:
    def __init__(self, filename="./mat/matlab.mat", max_n_samples=1000):
        self.filename = filename
        file = File(filename)
        time = np.ravel(file.get("unixtime_dbl_global"))
        self.time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
        diag_global = file.get("diag_global")
        diag_global = np.rot90(diag_global)
        file.close()
        self.size = self.time.size
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
        self.dcc = dcc.Graph(id="id", figure=self.figure)

    def update(self, relayoutData=None):
        res = []
        start, end = 0, self.size
        if relayoutData and "xaxis.range[0]" in relayoutData:
            start = time.mktime(
                datetime.strptime(relayoutData["xaxis.range[0]"], "%Y-%m-%d %H:%M:%S.%f").timetuple()) - time.timezone
            end = time.mktime(
                datetime.strptime(relayoutData["xaxis.range[1]"], "%Y-%m-%d %H:%M:%S.%f").timetuple()) - time.timezone

            start, end = PlotlyAggregatorParser.get_start_end_indices(self.first_diag, start=start,
                                                                      end=end,
                                                                      axis_type=None)

        x, y, indexes = PlotlyAggregatorParser.aggregate(self.first_diag, start, end)
        res.append(y)

        for i in range(15):
            res.append(self.data[i][indexes])
        return self.time[indexes], res


keogram = Keogram()

app.layout = html.Div([
    keogram.dcc
])


@app.callback(Output('id', 'figure'),
              Input('id', 'relayoutData'))
def display_relayout_data(relayoutData):
    data = keogram.update(relayoutData)
    return go.Figure(data=go.Heatmap(x=data[0], z=data[1]))


app.run(host='127.0.0.1', port=5050, debug=True)
# print(keogram.figure)
