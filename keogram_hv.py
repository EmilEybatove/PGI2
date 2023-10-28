import sys
import time

import holoviews as hv
import numpy as np
from dash import Dash, html
from h5py import File
from holoviews.plotting.plotly.dash import to_dash

app = Dash(__name__)
hv.extension('matplotlib')


def keogram(filename=f'./2022_23/2022-10-05-18_32-19_32.mat'):
    t0 = time.time()
    file = File(filename)
    print(dict(file))
    # time = np.ravel(file.get("unixtime_dbl_global"))
    # time = pd.to_datetime(pd.Series(time), unit="s").to_numpy()
    data = np.array(file.get("pdm_2d_rot_global"))

    t1 = time.time()
    print(f"Time spent on export: {t1 - t0}", flush=True)
    heatmap = hv.HeatMap(data)
    return heatmap


plot = keogram()

components = to_dash(app, [plot])
app.layout = html.Div(components.children)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        app.run(host=sys.argv[1], port=int(sys.argv[2]))
        pass
    else:
        print(sys.argv)
        app.run(host="localhost", port=5000)
