import sys

import holoviews as hv
import numpy as np
import pandas as pd
from dash import Dash, html
from h5py import File
from holoviews.plotting.plotly.dash import to_dash

app = Dash(__name__)
hv.extension('matplotlib')


def lightcurve(filename=f'./2022_23/2022-10-05-18_32-19_32.mat'):
    file = File(filename)

    time = np.ravel(file.get("unixtime_dbl_global"))
    time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
    light = np.ravel(file.get("lightcurvesum_global"))
    # time = np.array([_ for _ in range(40)])
    # light = np.array([random.uniform(1.5, 100) for _ in range(40)])
    curve = hv.Curve(zip(time, light))
    curve.opts(xaxis=None, color='blue')
    spikes = hv.Spikes(time)
    spikes.opts(yaxis=None, color='grey')
    return curve, spikes


def keogram(filename=f'./2022_23/2022-10-05-18_32_19_32.mat'):
    file = File(filename)


plot, spikes_global = lightcurve()

components = to_dash(app, [plot, spikes_global])
app.layout = html.Div(components.children)

# trace_updater.TraceUpdater(id="trace-updater", gdID="first_graph"),])
# fig.register_update_graph_callback(app, "first_graph", "trace-updater")

# @app.callback(Input('first_graph', 'relayoutData'))
# def display_relayout_data(relayoutData):
#     print("It happened!!!", relayoutData)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.run(host=sys.argv[1], port=int(sys.argv[2]))
        pass
    else:
        print(sys.argv)
        app.run(host="localhost", port=5000)
