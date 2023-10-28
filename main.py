from h5py import File
import plotly.graph_objects as go, trace_updater
from plotly_resampler import FigureResampler
import numpy as np
from dash import Dash, html, dcc, Input, Output
from dash.html import Div, Em, Span, A, Img, Br
import pandas as pd

app = Dash(__name__)

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

app.layout = head

if __name__ == "__main__":
    app.run('127.0.0.1', port=5001)
