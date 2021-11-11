# Copyright (C) 2019-2020, Therapixel SA.
# All rights reserved.
# This file is subject to the terms and conditions described in the
# LICENSE file distributed in this package.
"""The main application dashboard."""
import os

from datetime import date, datetime
from typing import Any

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import dcc, html
from dash.dependencies import Input, Output
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker

from pacsanini.config import PacsaniniConfig
from pacsanini.dashboard.env import app_env
from pacsanini.db import ManufacturerView, StudyMetaView


base_path = os.path.dirname(os.path.abspath(__file__))
app = dash.Dash(
    name="pacsanini",
    title="pacsanini",
    assets_folder=os.path.join(base_path, "assets"),
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server


def description_card() -> html.Div:
    """Return a div containing the dashboard title and descriptions."""
    return html.Div(
        id="description-card",
        children=[
            html.H5("Pacsanini Dashboard 🎻"),
            html.Div(
                id="intro",
                children=(
                    "Welcome to the pacsanini dashboard."
                    " Explore the available DICOM data according to the filters you come up with."
                ),
            ),
        ],
    )


def control_card() -> html.Div:
    """Return the div that contains all the control buttons/inputs to filter data."""
    return html.Div(
        id="control-card",
        children=[
            html.P("Select Manufacturer"),
            dcc.Dropdown(
                id="manufacturer-select",
                options=[{"label": i, "value": i} for i in app_env.manufacturers],
                value=0,
                multi=True,
            ),
            html.Br(),
            html.P("Select Date Range"),
            dcc.DatePickerRange(
                id="date-range-picker",
                start_date=date(2010, 1, 1),
                end_date=datetime.utcnow().date(),
                display_format="YYYY MMM DD",
                clearable=True,
            ),
            html.Br(),
            html.Br(),
            html.P("Select Study Image Count"),
            dcc.RangeSlider(
                id="image-range-picker",
                min=0,
                max=20,
                step=1,
                value=[0, 5],
                marks={i: f"{i} images" for i in range(0, 21, 10)},
                tooltip={"placement": "top", "always_visible": True},
            ),
            html.P("Select Patient Age"),
            dcc.RangeSlider(
                id="patient-age-range-picker",
                min=0,
                max=100,
                step=5,
                value=[0, 80],
                marks={i: str(i) for i in range(0, 100, 20)},
                tooltip={"placement": "top", "always_visible": True},
            ),
            html.Br(),
        ],
    )


def counts_card() -> html.Div:
    """Return the div that contains the overall count of patients/studies/images."""
    return html.Div(
        className="row",
        children=[
            html.Div(
                className="four columns",
                children=[
                    html.Div(
                        className="card gold-left-border",
                        children=html.Div(
                            className="container",
                            children=[
                                html.H4(id="patient-count", children=""),
                                html.P(children="patients"),
                            ],
                        ),
                    )
                ],
            ),
            html.Div(
                className="four columns",
                children=[
                    html.Div(
                        className="card green-left-border",
                        children=html.Div(
                            className="container",
                            children=[
                                html.H4(id="study-count", children=""),
                                html.P(children="studies"),
                            ],
                        ),
                    )
                ],
            ),
            html.Div(
                className="four columns",
                children=[
                    html.Div(
                        className="card purple-left-border",
                        children=html.Div(
                            className="container",
                            children=[
                                html.H4(id="image-count", children=""),
                                html.P(children="images"),
                            ],
                        ),
                    )
                ],
            ),
        ],
    )


def generate_study_metadata_plot(data: pd.DataFrame) -> Any:
    """Recompute and return the bar plot."""
    data["study_year"] = data["study_date"].apply(lambda x: x.year)

    year_grp = data.groupby(["study_year", "manufacturer"])
    yearly_patients = year_grp["patient_id"].nunique().reset_index()
    yearly_studies = year_grp["study_uid"].nunique().reset_index()
    yearly_images = year_grp["image_count"].sum().reset_index()
    years = yearly_images["study_year"]

    fig = go.Figure(
        data=[
            go.Bar(
                name="patients",
                x=years,
                y=yearly_patients["patient_id"],
                textposition="none",
                text=yearly_studies["manufacturer"],
                hovertemplate="%{x} %{text} patients: %{y}",
                marker_color="#DA9422",
            ),
            go.Bar(
                name="studies",
                x=years,
                y=yearly_studies["study_uid"],
                textposition="none",
                text=yearly_studies["manufacturer"],
                hovertemplate="%{x} %{text} studies: %{y}",
                marker_color="#22D892",
            ),
            go.Bar(
                name="images",
                x=years,
                y=yearly_images["image_count"],
                textposition="none",
                text=yearly_images["manufacturer"],
                hovertemplate="%{x} %{text} images: %{y}",
                marker_color="#9222D8",
            ),
        ]
    )

    fig.update_layout(
        title="Patient, Study and Image counts per year",
        legend_title_text="Count type",
        barmode="group",
        xaxis_title="year",
        yaxis_title="counts",
        xaxis=dict(tick0=data["study_year"].min(), dtick=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def graph_card() -> html.Div:
    """Return an empty bar plot that will be initialized on startup."""
    fig = px.bar()
    return html.Div(children=[dcc.Graph(id="data-overview", figure=fig)])


@app.callback(
    Output("manufacturer-select", "options"), Input("control-card", "children")
)
def load_manufacturer_options(_):
    """Load the different available manufacturers on application startup."""
    if not app_env.manufacturers:
        DBSession = sessionmaker(bind=app_env.engine)
        session = DBSession()
        available_manufacturers = [
            res[0] for res in session.query(ManufacturerView.manufacturer).all()
        ]
        app_env.manufacturers = available_manufacturers
    else:
        available_manufacturers = app_env.manufacturers
    return [{"label": manu, "value": manu} for manu in available_manufacturers]


@app.callback(
    [
        Output("patient-count", "children"),
        Output("study-count", "children"),
        Output("image-count", "children"),
        Output("data-overview", "figure"),
    ],
    [
        Input("manufacturer-select", "value"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("image-range-picker", "value"),
        Input("patient-age-range-picker", "value"),
    ],
)
def update_query_results(manufacturer, start_date, end_date, image_range, patient_age):
    """Update the patient, study, and image counts based on the provided
    control card input values. Regenerate the graph as well.
    """
    DBSession = sessionmaker(bind=app_env.engine)
    session = DBSession()
    query = session.query(StudyMetaView)

    if manufacturer:
        if isinstance(manufacturer, str):
            query = query.filter(StudyMetaView.manufacturer == manufacturer)
        else:
            query = query.filter(StudyMetaView.manufacturer.in_(manufacturer))

    if start_date and end_date:
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)
        query = query.filter(
            and_(
                StudyMetaView.study_date >= start_date_obj,
                StudyMetaView.study_date <= end_date_obj,
            )
        )
    elif start_date:
        start_date_obj = date.fromisoformat(start_date)
        query = query.filter(StudyMetaView.study_date >= start_date_obj)
    elif end_date:
        end_date_obj = date.fromisoformat(end_date)
        query = query.filter(StudyMetaView.study_date <= end_date_obj)

    patient_age_lower = patient_age[0]
    patient_age_upper = patient_age[1]
    if patient_age_lower == patient_age_upper:
        query = query.filter(StudyMetaView.patient_age == patient_age_upper)
    elif patient_age_lower == 0:
        query = query.filter(StudyMetaView.patient_age <= patient_age_upper)
    else:
        query = query.filter(
            and_(
                StudyMetaView.patient_age >= patient_age_lower,
                StudyMetaView.patient_age <= patient_age_upper,
            )
        )

    image_count_lower = image_range[0]
    image_count_upper = image_range[1]
    if image_count_lower == image_count_upper:
        query = query.filter(StudyMetaView.image_count == image_count_upper)
    elif image_count_lower == 0:
        query = query.filter(StudyMetaView.image_count <= image_count_upper)
    else:
        query = query.filter(
            and_(
                StudyMetaView.image_count >= image_count_lower,
                StudyMetaView.image_count <= image_count_upper,
            )
        )

    results = pd.read_sql_query(query.statement, app_env.engine.connect())

    return (
        f'{results["patient_id"].nunique():,}',
        f'{results["study_uid"].nunique():,}',
        f'{results["image_count"].sum():,}',
        generate_study_metadata_plot(results),
    )


app.layout = html.Div(
    children=[
        html.Div(
            id="left-column",
            className="four columns",
            children=[description_card(), control_card()],
        ),
        html.Div(
            id="right-column",
            className="eight columns",
            children=[counts_card(), graph_card()],
        ),
    ]
)


def run_server(config: PacsaniniConfig, port: int = 8050, debug: bool = False):
    """Run the dashboard server using the provided configuration to access
    the database backend.

    Running the server will block the current thread until it is terminated.

    Parameters
    ----------
    config : PacsaniniConfig
        The pacsanini configuration to use for spawning the dashboard server.
    port : int
        The port to use for the server. Defaults to 8050.
    debug : bool
        Whether the launch the dashboard in debug mode or not. The default
        is False.
    """
    engine = None
    session = None
    try:
        engine = create_engine(config.storage.resources)
        app_env.engine = engine

        DBSession = sessionmaker(bind=app_env.engine)
        session = DBSession()
        available_manufacturers = [
            res[0] for res in session.query(ManufacturerView.manufacturer).all()
        ]
        app_env.manufacturers = available_manufacturers

        app.run_server(port=port, debug=debug)
    finally:
        if session:
            session.close()
        if engine:
            engine.dispose()
