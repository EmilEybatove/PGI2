from h5py import File
import plotly.graph_objects as go
import trace_updater
from plotly_resampler import FigureResampler
import numpy as np
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import sys

app = Dash(__name__)


def lightcurve(filename=f'./2022_23/2022-10-05-18_32-19_32.mat'):
    file = File(filename)

    time = np.ravel(file.get("unixtime_dbl_global"))
    time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
    light = np.ravel(file.get("lightcurvesum_global"))

    fig = FigureResampler(go.Figure())
    fig.add_trace(go.Scattergl(name='lightcurve', showlegend=True), hf_x=time, hf_y=light)
    return fig


fig = lightcurve()
fig2 = lightcurve()

app.layout = html.Div([
    dcc.Graph(id="first_graph", figure=fig),
    dcc.Graph(id="second_graph", figure=fig2),
    trace_updater.TraceUpdater(id="trace-updater", gdID="first_graph"),
    trace_updater.TraceUpdater(id="trace2-updater", gdID="second_graph")
])

fig.register_update_graph_callback(app, "first_graph", "trace-updater")
fig2.register_update_graph_callback(app, "second_graph", "trace2-updater")

first = False
second = False


@app.callback(Output("second_graph", "relayoutData"),
              Output("second_graph", "figure"),
              Input('first_graph', 'relayoutData'))
def display_relayout_data(relayoutData):
    global first, second
    if not second:

        first = True
        if relayoutData and "autosize" in relayoutData and relayoutData["autosize"]:
            fig2.layout = {"autosize": True}
        elif relayoutData and "yaxis.autorange" not in relayoutData:
            relayoutData["yaxis.autorange"] = False

        fig2.plotly_update(relayout_data=relayoutData)
        return relayoutData, fig2
    second = False


@app.callback(Output("first_graph", "relayoutData"),
              Output("first_graph", "figure"),
              Input('second_graph', 'relayoutData'))
def display_relayout_data(relayoutData):
    global first, second

    if not first:

        second = True

        if relayoutData and "autosize" in relayoutData and relayoutData["autosize"]:
            fig.layout = {"autosize": True}
        elif relayoutData and "yaxis.autorange" not in relayoutData:
            relayoutData["yaxis.autorange"] = False

        fig.plotly_update(relayout_data=relayoutData)
        return relayoutData, fig
    first = False


# app.run(host='127.0.0.1', port=5000)  # debug=True
if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.run(host=sys.argv[1], port=int(sys.argv[2]))
    else:
        print(sys.argv)
        app.run(host="localhost", port=5000)
