#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
cytoflow.operations.subsample
-----------------------------

Applies random subsampling to an `Experiment`. `subsample` has one class:

`SubsampleOp` -- Applies subsampling, given sampling parameters
"""

from typing import List
import numpy as np
from traits.api import (HasStrictTraits, Float, Str, Instance,
                        Bool, observe, provides, Any, Dict,
                        Constant)

import pandas as pd
import itertools

import cytoflow.utility as util

from .i_operation import IOperation


@provides(IOperation)
class SubsampleOp(HasStrictTraits):
    """
    Apply subsampling a cytometry experiment.

    Attributes
    ----------
    sampling_type : Str
        Defines weather the sampling is done by a fixed number of events or by a fraction of the total number of events. 
        Must be either "absolute" or "relative".

    sampling_size : Float (default = None)
        The number of events to sample if `sampling_type` is "absolute" or the fraction of events to sample if `sampling_type` is "relative".
        Used to simply sample a fixed number of events or a fraction of the total number of events.

    sampling_def : Dict(Str, Any) (default = None)
        A dictionary defining the sampling for given conditions.
        The keys are the names of the conditions and the values are either a string or another dictionary.
        If the value is a string, it must follow the format "amount:retrieval_type" 
        where "amount" is a float and "retrieval_type" is either "FromEach" or "InTotal".
        If "retrieval_type" is "FromEach", "amount" defines the amount of events to sample from each unqiue value of the given condition.
        If "retrieval_type" is "InTotal", "amount" defines the amount of events to sample in total from all unique values of the given condition.
        In the second case the number of events per unqiue value of the given condition will be the same.

    replacement : Bool (default = True)
        Wether to sample with or without replacement. If replacement is False and amount of events to sample is larger than the total number of events,
        amount of events to sample will be set to the total number of events.

    """

    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.subsampling')
    friendly_id = Constant("Subsampling")

    sampling_type = Str
    sampling_size = Float(None)
    sampling_def = Dict(Str, Any, value=None)
    replacement = Bool(True)

    def apply(self, experiment):
        """Applies subsampling to an experiment.

        Parameters
        ----------
        experiment : `Experiment`
            the `Experiment` to which this operation is applied

        Returns
        -------
        Experiment
            a new `Experiment`, the same as the old experiment but with 
            only the rows that passed the sampling process.
        """

        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")

        if self.sampling_type not in ["absolute", "relative"]:
            raise util.CytoflowOpError('sampling_type',
                                       "Sampling type must be 'absolute' or 'relative'")

        if self.sampling_size is None and (self.sampling_def is None and self.sampling_def == {}):
            raise util.CytoflowOpError('sampling_size',
                                       "Either sampling_size or sampling_def must be set")

        if self.sampling_size is not None and (self.sampling_def is not None and self.sampling_def != {}):
            raise util.CytoflowOpError('sampling_size',
                                       "Either sampling_size or sampling_def must be set, not both")

        if self.sampling_def is not None:
            for condition_name in self.sampling_def.keys():
                if condition_name not in experiment.conditions:
                    raise util.CytoflowOpError('sampling_def',
                                               "Condition {} not in experiment".format(condition_name))

        if self.sampling_size is not None and self.sampling_size <= 0:
            raise util.CytoflowOpError('sampling_size',
                                       "Sampling size must be positive")

        new_experiment = experiment.clone(deep=False)

        sampling_indices = []

        if self.sampling_size is not None:
            # basic sampling with sampling_size
            if self.sampling_type == 'relative':
                sampling_indices.append(experiment.data.sample(
                    frac=self.sampling_size, replace=self.replacement).index.tolist())
            else:
                sampling_indices.append(experiment.data.sample(
                    n=int(np.round(self.sampling_size)), replace=self.replacement).index.tolist())

        else:
            # advanced sampling with sampling_def
            for condition_name, config_value in self.sampling_def.items():
                if isinstance(config_value, dict) or isinstance(config_value, Dict):
                    sampling_indices.append(self._advanced_sampling_by_value_dict(
                        experiment.data, condition_name, config_value))
                else:
                    condition_dtype = experiment.metadata[condition_name]["dtype"]
                    if condition_dtype != 'category' and condition_dtype != 'bool':
                        raise util.CytoflowOpError('sampling_def',
                                                   "Condition '{}' is not categorical or boolean".format(condition_name))

                    sampling_indices.append(self._advanced_sampling_by_value_string(
                        experiment.data, condition_name, config_value))

        sampling_indices = list(itertools.chain.from_iterable(sampling_indices))

        if len(sampling_indices) == 0:
            raise util.CytoflowOpError("no events to sample could be found")

        new_experiment.data = new_experiment.data.iloc[sampling_indices, :]

        new_experiment.history.append(self.clone_traits(transient=lambda t: True))
        return new_experiment

    def _advanced_sampling_by_value_dict(self, data_df: pd.DataFrame, condition_name: str, config_value: dict) -> List[int]:
        sampling_indices = []
        value_counts = data_df[condition_name].value_counts()
        for value_name, amount in config_value.items():

            if not isinstance(value_name, str):
                raise util.CytoflowOpError('sampling_def',
                                           f"value '{value_name}' must be a string")

            if not isinstance(amount, (int, float)):
                raise util.CytoflowOpError('sampling_def',
                                           f"amount '{amount}' must be a number")

            if amount <= 0:
                raise util.CytoflowOpError('sampling_def',
                                           f"amount '{amount}' must be positive")

            if value_name not in value_counts.keys():
                raise util.CytoflowOpError('sampling_def',
                                           f"value '{value_name}' not present in condition '{condition_name}'")

            if self.sampling_type == 'absolute' and self.replacement == False and amount > value_counts[value_name]:
                amount = value_counts[value_name]

            events_with_value = data_df[data_df[condition_name] == value_name]
            if self.sampling_type == 'relative':
                sampled_idx = events_with_value.sample(
                    frac=amount, replace=self.replacement).index.tolist()
            elif self.sampling_type == 'absolute':
                sampled_idx = events_with_value.sample(
                    n=int(np.round(amount)), replace=self.replacement).index.tolist()

            sampling_indices.append(sampled_idx)

        return list(itertools.chain.from_iterable(sampling_indices))

    def _advanced_sampling_by_value_string(self, data_df: pd.DataFrame, condition_name: str, config_value: str) -> List[int]:

        if not isinstance(config_value, (str)):
            raise util.CytoflowOpError('config_value',
                                       "Config value must be a dict or a string but given is '{}'".format(type(config_value)))

        if ":" not in config_value:
            raise util.CytoflowOpError('config_value',
                                       "Config value must be in the format 'value:retrieval_type' but given '{}'".format(config_value))
        amount, retrieval_type = config_value.split(":")
        try:
            amount = float(amount)
        except ValueError:
            raise util.CytoflowOpError('config_value',
                                       "Amount must be a number but given '{}'".format(amount))

        if retrieval_type not in ["FromEach", "InTotal"]:
            raise util.CytoflowOpError('sampling_def',
                                       "retrieval_type must be 'FromEach' or 'InTotal'")

        sampling_indices = []
        value_counts = data_df[condition_name].value_counts()

        to_sample_per_value = dict()

        if retrieval_type == "FromEach":

            if self.sampling_type == 'relative':
                for value_name, value_count in value_counts.items():
                    to_sample_per_value[value_name] = int(
                        np.round(amount * value_counts[value_name]))
            elif self.sampling_type == 'absolute':
                for value_name, value_count in value_counts.items():
                    if self.replacement == False and amount > value_counts[value_name]:
                        amount = value_counts[value_name]
                    to_sample_per_value[value_name] = int(np.round(amount))

        elif retrieval_type == "InTotal":

            if self.replacement == False:
                raise util.CytoflowOpError(
                    'sampling_def', "'InTotal' sampling is not possible without replacement")

            if self.sampling_type == 'relative':
                n_events = data_df.shape[0]
                target_total = amount * n_events
            elif self.sampling_type == 'absolute':
                target_total = amount
            amount_per_val_population = int(np.round(target_total / len(value_counts)))
            for value_name in value_counts.keys():
                to_sample_per_value[value_name] = amount_per_val_population

        for value_name, sample_amount in to_sample_per_value.items():
            events_with_value = data_df[data_df[condition_name] == value_name]

            sampled_idx = events_with_value.sample(
                n=sample_amount, replace=self.replacement).index.tolist()
            sampling_indices.append(sampled_idx)

        return list(itertools.chain.from_iterable(sampling_indices))


if __name__ == '__main__':
    import cytoflow as flow

    tube1 = flow.Tube(file = '../../cytoflow/tests/data/vie14/494.fcs')
    org_ex = flow.ImportOp(tubes = [tube1]).apply()
    cond_op = flow.BulkConditionOp(conditions_csv_path = '../../cytoflow/tests/data/vie14/494_labels.csv',
                                        combine_order = ["allevents","syto", "singlets", "intact","cd19", "blast"])
    cond_op.combined_conditions_name = "label"
    ex = cond_op.apply(org_ex)

    subsampling_op = flow.SubsampleOp(sampling_type = "relative", sampling_def = {
            "label" : {"blast" : 0.5, "cd19" : 0.1}
        })
    new_ex = subsampling_op.apply(ex)
