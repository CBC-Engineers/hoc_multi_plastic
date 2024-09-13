"""Widgets to be used in Jupyter notebook."""
import functools

from IPython.display import display
import ipywidgets as widgets
from aashto_plastic_pipe_check import SH

import hoc_multi_plastic

pipe_type_select = widgets.Dropdown(
    options=[v.value for v in SH.range("AvailablePipeNames")],
    value=SH.range("PipeName").value,
    description="Pipe Names",
    style=dict(description_width='initial'),
)

description_select = widgets.SelectMultiple(
    options=[v.value for v in SH.range("AvailableDescriptions#")],
    description="Descriptions",
    style = dict(description_width='initial'),
)

diameter_select = widgets.SelectMultiple(
    options=sorted({str(v.value) for v in SH.range("AvailableDiameters#")}),
    description="Diameters",
    style = dict(description_width='initial'),
)

flood_condition_select = widgets.SelectMultiple(
    options={"Flooded":True, "No Water": False},
    description="Flood Condition",
    style = dict(description_width='initial'),
)

cover_condition_select = widgets.SelectMultiple(
    options=["Max", "Min"],
    description="Cover Condition",
    style = dict(description_width='initial'),
)

soil_class_select = widgets.SelectMultiple(
    options=["I", "II", "III"],
    description="Soil Class",
    style = dict(description_width='initial'),
)

compaction_classI_select = widgets.SelectMultiple(
    options=["Compacted", "Uncompacted"],
    description="Class I Compaction",
    style = dict(description_width='initial'),
)

compaction_select = widgets.SelectMultiple(
    options=["95%", "90%", "85%"],
    description="Class II-III Compaction",
    style = dict(description_width='initial'),
)

run_button = widgets.Button(
    description="Run Analyses",
    style=dict(description_width='initial'),
)

results_text = widgets.Textarea(
    placeholder='Analysis Results',
    # disabled=True
)


def run(b):
    try:
        results_text.value = "BUTTON CLICKED\n"
        pipes_analyzed = tuple((hoc_multi_plastic.u(d+"inch"), p) for d in diameter_select.value for p in description_select.value)
        results_text.value = results_text.value + "\n".join(f"{d}-{p}" for d, p in pipes_analyzed)
        hoc_multi_plastic.main(
            pipes_analyzed,
            flooded_conditions=flood_condition_select.value,
            cover_conditions=cover_condition_select.value,
            soil_classes=soil_class_select.value,
            compactions=compaction_select.value + compaction_classI_select.value,
            log = results_text,
        )
        results_text.value = results_text.value + "\nANALYSIS COMPLETE\n"
    except:
        raise


run_button.on_click(run)


def update_menus(w):
    SH.range("PipeName").value = pipe_type_select.value
    description_select.options = [v.value for v in SH.range("AvailableDescriptions#")]
    diameter_select.options = sorted({v.value for v in SH.range("AvailableDiameters#")})


pipe_type_select.observe(handler=update_menus, names="value")

layout_70 = widgets.Layout(width="100%", # object_fit="fill"
                           )

display(widgets.VBox([widgets.HBox([pipe_type_select]),
                      widgets.HBox([
                          description_select,
                          diameter_select,
                      ]),
                      widgets.HBox([
                          flood_condition_select,
                          cover_condition_select,
                      ]),
                      widgets.HBox([
                          soil_class_select,
                          compaction_classI_select,
                          compaction_select,
                      ]),
                      widgets.HBox([run_button]),
                      widgets.HBox([results_text])
                      ],layout=layout_70
                     )
        )
