# Create a DatamationGroupBy
#
# Create a subclass from a pandas DataFrameGroupBy.
#
import json
import pandas as pd
from . import utils
from . import datamation_frame

# The subclass of DataFrameGroupBy
class DatamationGroupBy(pd.core.groupby.generic.DataFrameGroupBy):
    @property
    def _constructor(self):
        return DatamationGroupBy._internal_ctor

    _by = []
    _output = {}
    _error = {}
    _states = []
    _operations = []

    @classmethod
    def _internal_ctor(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __init__(self, obj, by, keys=None, axis=0, level=None):
        self._by = [by] if type(by) == str else by
        super(DatamationGroupBy, self).__init__(obj=obj, keys=self._by)
        self._states = list(obj.states)
        self._operations = list(obj.operations)

    @property
    def states(self):
        return self._states

    @property
    def operations(self):
        return self._operations

    # Override the 'mean' function
    def mean(self):
        self._states.append(self)
        self._operations.append('mean')
        df = super(DatamationGroupBy, self).mean()
        df = datamation_frame.DatamationFrame(df)
        df._by = self.states[1]._by
        df._states = self._states
        df._operations = self._operations
        self._output = df
        self._error = super(DatamationGroupBy, self).sem()
        return df
        
    # The specs to show summarized points on the chart
    def prep_specs_summarize(self, width=300, height=300):
        x_axis = self.states[1].dtypes.axes[0].name if len(self._by) == 1 else self.states[1].dtypes.axes[0].names[0]
        y_axis = self.states[1].dtypes.axes[1].values[1] if len(self._by) == 1 else self.states[1].dtypes.axes[1].values[0]


        if len(self.states[1].groups.keys()) == 2:
            groups = list(self.states[1].groups.keys())
        else:
            groups = [list(self.states[1].groups.keys())[0][0], list(self.states[1].groups.keys())[2][0]]
            subgroups = [list(self.states[1].groups.keys())[0][1], list(self.states[1].groups.keys())[1][1]]

        specs_list = []

        labels = [subgroups[0] if len(self._by) > 1 else groups[0], subgroups[1] if len(self._by) > 1 else groups[1]]

        x_encoding = {
            "field": "datamations_x",
            "type": "quantitative",
            "axis": {
            "values": [1, 2],
            "labelExpr": "round(datum.label) == 1 ? '" + labels[0] + "' : '"  +  labels[1] + "'",
            "labelAngle": -90
            },
            "title": self._by[1] if len(self._by) > 1 else x_axis,
            "scale": {
            "domain": [0.5, 2.5]
            }
        }

        y_encoding = {
            "field": "datamations_y",
            "type": "quantitative",
            "title": y_axis,
            "scale": {
            "domain": [round(self.states[0][y_axis].min(),13), self.states[0][y_axis].max()]
            }
        }

        if len(self._by) > 1:
            color = {
            "field": self._by[1],
            "type": "nominal",
                "legend": {
                    "values": [
                        subgroups[0],
                        subgroups[1]
                    ]
                }
            }

        tooltip = [
            {
                "field": "datamations_y_tooltip",
                "type": "quantitative",
                "title": y_axis
            }
        ]

        for field in self._by:
            tooltip.append({
                "field": field,
                "type": "nominal"
            })
        
        facet_encoding = {}

        if len(self._by) > 1:
            sort = [list(self.states[1].groups.keys())[0][0], list(self.states[1].groups.keys())[2][0]]
            facet_encoding["column"] = { "field": self._by[0], "sort": sort, "type": "ordinal", "title": self._by[0] }

        if len(self._by) > 2:
            facet_encoding["row"] = { "field": self._by[1], "type": "ordinal", "title": self._by[1] }

        facet_dims = {
                "ncol": 1,
                "nrow": 1
        }

        if len(self._by) > 1:
            cols = []
            count = {}
            for key in self.states[1].groups.keys():
                col, row = key
                if col not in cols:
                    cols.append(col)
                if col not in count:
                    count[col] = 0
                count[col] = count[col] + len(self.states[1].groups[key])
                
            facet_dims = {
                "ncol": len(cols),
                "nrow": 1
            }

        data = []
        
        # Prepare the data by assigning different x-axis values to the groups
        # and showing the original values on the y-axis for each point.
        if len(self._by) > 1:
            i = 1
            data = []
            for group in self.groups:
                col, row = group
                for index in self.groups[group]:
                    value = {
                        "gemini_id": i,
                        self._by[0]: self.states[0][self._by[0]][index],
                        self._by[1]: self.states[0][self._by[1]][index],
                        "datamations_x": 1 if self.states[0][self._by[1]][index] == subgroups[0]  else 2,
                        "datamations_y": self.states[0][y_axis][index],
                        "datamations_y_tooltip": self.states[0][y_axis][index]   
                    }
                    data.append(value)
                    i = i+1
                        
            facet_dims = {
                "ncol": len(cols),
                "nrow": 1
            }
        else:
            id = 1
            for i in range(len(self.states[0])):
                if self.states[0][x_axis][i] == groups[1]:
                    continue
                value = {
                    "gemini_id": id,
                    x_axis: self.states[0][x_axis][i],
                    "datamations_x": 1 if self.states[0][x_axis][i] == groups[0]  else 2,
                    "datamations_y": self.states[0][y_axis][i],
                    "datamations_y_tooltip": self.states[0][y_axis][i],
                }
                data.append(value)
                id = id + 1

            for i in range(len(self.states[0])):
                if self.states[0][x_axis][i] == groups[0]:
                    continue
                value = {
                    "gemini_id": id,
                    x_axis: self.states[0][x_axis][i],
                    "datamations_x": 1 if self.states[0][x_axis][i] == groups[0]  else 2,
                    "datamations_y": self.states[0][y_axis][i],
                    "datamations_y_tooltip": self.states[0][y_axis][i]
                }
                data.append(value)
                id = id + 1

        # Jitter plot
        meta = { 
            "parse": "jitter",
            "axes": len(self._by) > 1,
            "description": "Plot " + y_axis + " within each group",
            "splitField": self._by[-1]
        }
        if len(self._by) == 1:
            meta["xAxisLabels"] = groups
        
        # Spec encoding for Vega along with the data and metadata.
        # Generate vega specs for the summarizing steps of the animaiton
        spec_encoding = { 'x': x_encoding, 'y': y_encoding, 'tooltip': tooltip }
        if len(self._by) > 1:
            spec_encoding = { 'x': x_encoding, 'y': y_encoding, "color": color, 'tooltip': tooltip }
        spec = utils.generate_vega_specs(data, meta, spec_encoding, facet_encoding, facet_dims)
        specs_list.append(spec)

        meta = { 
            "axes": len(self._by) > 1,
            "description": "Plot mean " + y_axis + " of each group"
        }

        y_encoding = {
            "field": "datamations_y",
            "type": "quantitative",
            "title": "mean(" + y_axis + ")",
            "scale": {
            "domain": [round(self.states[0][y_axis].min(),13), self.states[0][y_axis].max()]
            }
        }

        tooltip = [
            {
                "field": "datamations_y_tooltip",
                "type": "quantitative",
                "title": "mean(" + y_axis + ")"
            }
        ]
        
        for field in self._by:
            tooltip.append({
                "field": field,
                "type": "nominal"
            })
        
        data = []
        
        # Plot the final summarized value
        # The y-axis value is the same for all 
        if len(self._by) > 1:
            i = 1
            data = []
            for group in self.groups:
                col, row = group
                for index in self.groups[group]:
                    value = {
                        "gemini_id": i,
                        x_axis: self.states[0][x_axis][index],
                        self._by[1]: self.states[0][self._by[1]][index],
                        "datamations_x": 1 if self.states[0][self._by[1]][index] == subgroups[0]  else 2,
                        "datamations_y": self._output[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]],
                        "datamations_y_tooltip": self._output[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]]  
                    }
                    data.append(value)
                    i = i+1
                        
            facet_dims = {
                "ncol": len(cols),
                "nrow": 1
            }
        else:
            id = 1
            for i in range(len(self.states[0])):
                if self.states[0][x_axis][i] == groups[1]:
                    continue
                value = {
                    "gemini_id": id,
                    x_axis: self.states[0][x_axis][i],
                    "datamations_x": 1 if self.states[0][x_axis][i] == groups[0]  else 2,
                    "datamations_y": self._output[y_axis][groups[0]],
                    "datamations_y_tooltip": self._output[y_axis][groups[0]]
                }
                data.append(value)
                id = id + 1

            for i in range(len(self.states[0])):
                if self.states[0][x_axis][i] == groups[0]:
                    continue
                value = {
                    "gemini_id": id,
                    x_axis: self.states[0][x_axis][i],
                    "datamations_x": 1 if self.states[0][x_axis][i] == groups[0]  else 2,
                    "datamations_y": self._output[y_axis][groups[1]],
                    "datamations_y_tooltip": self._output[y_axis][groups[1]]
                }
                data.append(value)
                id = id + 1
        meta['custom_animation'] = 'mean'
        spec_encoding = { 'x': x_encoding, 'y': y_encoding, 'tooltip': tooltip }
        if len(self._by) > 1:
            spec_encoding = { 'x': x_encoding, 'y': y_encoding, "color": color, 'tooltip': tooltip }
        spec = utils.generate_vega_specs(data, meta, spec_encoding, facet_encoding, facet_dims)
        specs_list.append(spec)

        tooltip = [
            {
            "field": "datamations_y_tooltip",
            "type": "quantitative",
            "title": "mean(" + y_axis + ")"
            },
            {
            "field": "Upper",
            "type": "nominal",
            "title": "mean(" + y_axis + ") + standard error"
            },
            {
            "field": "Lower",
            "type": "nominal",
            "title": "mean(" + y_axis + ") - standard error"
            }
        ]

        for field in self._by:
            tooltip.append({
                "field": field,
                "type": "nominal"
            })
        
        data = []

        # Show errror bars along with sumarized values
        if len(self._by) > 1:
            i = 1
            data = []
            for group in self.groups:
                col, row = group
                for index in self.groups[group]:
                    value = {
                        "gemini_id": i,
                        x_axis: self.states[0][x_axis][index],
                        self._by[1]: self.states[0][self._by[1]][index],
                        "datamations_x": 1 if self.states[0][self._by[1]][index] == subgroups[0]  else 2,
                        "datamations_y": self._output[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]],
                        "datamations_y_tooltip": self._output[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]], 
                        "datamations_y_raw": self.states[0][y_axis][index],
                        "Lower": self._output[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]] - self._error[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]],
                        "Upper": self._output[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]] + self._error[y_axis][self.states[0][self._by[0]][index]][self.states[0][self._by[1]][index]]
                    }
                    data.append(value)
                    i = i+1
                        
            facet_dims = {
                "ncol": len(cols),
                "nrow": 1
            }
        else:
            id = 1
            for i in range(len(self.states[0])):
                if self.states[0][x_axis][i] == groups[1]:
                    continue
                data.append({
                    "gemini_id": id,
                    x_axis: self.states[0][x_axis][i],
                    "datamations_x": 1 if self.states[0][x_axis][i] == groups[0]  else 2,
                    "datamations_y": self._output[y_axis][groups[0]],
                    "datamations_y_tooltip": self._output[y_axis][groups[0]],
                    "datamations_y_raw": self.states[0][y_axis][i],
                    "Lower": self._output[y_axis][groups[0]] - self._error[y_axis][groups[0]],
                    "Upper": self._output[y_axis][groups[0]] + self._error[y_axis][groups[0]]
                })
                id = id + 1

            for i in range(len(self.states[0])):
                if self.states[0][x_axis][i] == groups[0]:
                    continue
                data.append({
                    "gemini_id": id,
                    x_axis: self.states[0][x_axis][i],
                    "datamations_x": 1 if self.states[0][x_axis][i] == groups[0]  else 2,
                    "datamations_y": self._output[y_axis][groups[1]],
                    "datamations_y_tooltip": self._output[y_axis][groups[1]],
                    "datamations_y_raw": self.states[0][y_axis][i],
                    "Lower": self._output[y_axis][groups[1]] - self._error[y_axis][groups[1]],
                    "Upper": self._output[y_axis][groups[1]] + self._error[y_axis][groups[1]]
                })
                id = id + 1

        meta = { 
            "axes": len(self._by) > 1,
            "description": "Plot mean " + y_axis + " of each group, with errorbar"
        }

        spec_encoding = { 'x': x_encoding, 'y': y_encoding, 'tooltip': tooltip }
        if len(self._by) > 1:
            spec_encoding = { 'x': x_encoding, 'y': y_encoding, "color": color, 'tooltip': tooltip }
        spec = utils.generate_vega_specs(data, meta, spec_encoding, facet_encoding, facet_dims, True)
        specs_list.append(spec)

        # Show the summarized values along with error bars, zoomed in
        if len(self._by) > 1:
            domain = [
                round(min(self._output[y_axis][groups[0]][subgroups[0]] - self._error[y_axis][groups[0]][subgroups[0]], self._output[y_axis][groups[1]][subgroups[1]] - self._error[y_axis][groups[0]][subgroups[0]]),13),
                round(max(self._output[y_axis][groups[1]][subgroups[0]] + self._error[y_axis][groups[1]][subgroups[0]], self._output[y_axis][groups[1]][subgroups[1]] + self._error[y_axis][groups[1]][subgroups[1]]),13),
              ]
        else:
            domain = [
                round(min(self._output[y_axis][groups[0]]-self._error[y_axis][groups[0]], self._output[y_axis][groups[1]]-self._error[y_axis][groups[1]]),13),
                round(max(self._output[y_axis][groups[0]]+self._error[y_axis][groups[0]], self._output[y_axis][groups[1]]+self._error[y_axis][groups[1]]),13)
            ]

        y_encoding = {
            "field": "datamations_y",
            "type": "quantitative",
            "title": "mean(" + y_axis + ")",
            "scale": {
            "domain": domain
            }
        }

        meta = { 
            "axes": len(self._by) > 1,
            "description": "Plot mean " + y_axis + " of each group, with errorbar, zoomed in"
        }
        spec_encoding = { 'x': x_encoding, 'y': y_encoding, 'tooltip': tooltip }
        if len(self._by) > 1:
            spec_encoding = { 'x': x_encoding, 'y': y_encoding, "color": color, 'tooltip': tooltip }
        spec = utils.generate_vega_specs(data, meta, spec_encoding, facet_encoding, facet_dims, True)
        specs_list.append(spec)
                
        return specs_list
