from h5py import File
import plotly.graph_objects as go, trace_updater
from plotly_resampler import FigureResampler
import numpy as np
from dash import Dash, html, dcc, Input, Output
import pandas as pd

app = Dash(__name__)


def lightcurve(filename=f'./2022_23/2022_23/2022-10-05-18_32-19_32.mat'):
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
    dcc.Graph(id="graph-id", figure=fig),
    dcc.Graph(id="1234567", figure=fig2),
    trace_updater.TraceUpdater(id="trace-updater", gdID="graph-id"),
    trace_updater.TraceUpdater(id="b", gdID="1234567")
])

fig.register_update_graph_callback(app, "graph-id", "trace-updater")
fig2.register_update_graph_callback(app, "1234567", "b")

first = False
second = False

@app.callback(Output("1234567", "relayoutData"),
              Output("1234567", "figure"),
              Input('graph-id', 'relayoutData'))
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


@app.callback(Output("graph-id", "relayoutData"),
              Output("graph-id", "figure"),
              Input('1234567', 'relayoutData'))
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


app.run('127.0.0.1', port=5000)  # debug=True
