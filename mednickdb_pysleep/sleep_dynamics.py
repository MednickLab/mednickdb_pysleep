import numpy as np
import itertools
from typing import Dict, Union, List
from mednickdb_pysleep import pysleep_defaults
import warnings


def num_awakenings(epoch_stages, waso_stage=pysleep_defaults.waso_stage):
    """
    Count the number of transitions to wake
    :param epoch_stages: The pattern of sleep stages, ignoring duration (e.g. [ 0 1 2 1]
    :param waso_stage: stage that represents wake, default 0
    :return: number of awakenings
    """
    wake_only = np.where(np.array(epoch_stages) == waso_stage, 1, 0)
    return np.sum(np.diff(wake_only) == 1)


def transition_counts(epoch_stages: list,
                      count_self_trans: bool=False,
                      normalize: bool=False,
                      stages_to_consider=pysleep_defaults.stages_to_consider): #first_order=False, second_order=False):
    """
    Get the number of transition from one stage to another
    :param epoch_stages: The pattern of sleep stages, will handle with and without duration e.g. [0 1 2 1]
    or [0 0 1 1 1 2 2 2 1] will produce the same ans (if count_self_trans=False)
    :param count_self_trans: If transitions from and too the same stages should be counted (i.e. [0 0]). If false, diagnals will be 0
    :param normalize: Whether to normalize to transition probabilities or leave as counts
    :param stages_to_consider: which stages to calc transition counts for
    :return: a tuple of (zeroth order transitions, first order transitions, second order transitions):
        last dimension is stage transitioned to, other dimensions are the last stages.
        e.g. for first order, dims = [current stage, next stage]
        e.g. for 2nd order, dims=[previous stage, current stage, next stage]
    """

    num_stages = len(stages_to_consider)
    stage_rev_map = {v:k for k, v in enumerate(stages_to_consider)}
    epoch_stages_ = [stage_rev_map[epoch] for epoch in epoch_stages if epoch in stages_to_consider]
    first = np.zeros((num_stages, num_stages))
    second = np.zeros((num_stages, num_stages, num_stages))

    if len(epoch_stages_) <= 3:
        return None, None, None

    for a, b, c in zip(epoch_stages_[:-2], epoch_stages_[1:-1], epoch_stages_[2:]):
        first[a, b] += 1
        second[a, b, c] += 1
    first[b, c] += 1  # make sure to add the last one too :)

    if not count_self_trans:
        for stage in stages_to_consider:
            first[stage_rev_map[stage], stage_rev_map[stage]] = 0
    zeroth = np.sum(first, axis=0)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        if not normalize:
            return zeroth.astype(int), first.astype(int), second.astype(int)
        else:
            return zeroth.astype(int)/np.sum(zeroth), \
                   first.astype(int)/np.expand_dims(np.sum(first, axis=1), 1), \
                   second.astype(int)/np.expand_dims(np.sum(second, axis=2), 2)


def bout_durations(epoch_stages: list,
                   epoch_len: int=pysleep_defaults.epoch_len,
                   stages_to_consider=pysleep_defaults.stages_to_consider) -> Dict[Union[str, int], List[float]]:
    """
    Convert an epoch stages array (which includes self transitions) to a set of durations
    :param epoch_stages: epoch_stages: The pattern of sleep stages, with self-transitions e.g. [0 0 1 1 1 2 2 2 1]
    :param epoch_len: the length in seconds of each epoch
    :param stages_to_consider: which stages to calculate bout durations for
    :return: a dict, with one key per stage, and a list of durations for each bout of a stage
    """
    dur_dists = {s: [] for s in stages_to_consider}

    for stage, run in itertools.groupby(epoch_stages):
        if stage in stages_to_consider:
            run_len = len([_ for _ in run])
            dur_dists[stage].append(float(run_len)*epoch_len/60)
    return dur_dists

