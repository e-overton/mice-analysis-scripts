"""
Some tools for processing spacepoints.. (and now clusters)

"""

import ROOT


def MissingFromDuplet(sp):
    """
    Determine the missing plane and channel from a duplet
    spacepoint. Using the kuno sum
    """

    if sp.get_channels() == 3:
        raise Exception("Not possible to locate a missing"
                        " channel in a triplet spacepoint")

    if (sp.get_tracker() == 1) and (sp.get_station() == 5):
        kuno_total = 319.5
    else:
        kuno_total = 318.0
    plane_total = 3

    plane_sum, kuno_sum = 0, 0

    for cluster in sp.get_channels():
        plane_sum += cluster.get_plane()
        kuno_sum += cluster.get_channel()

    return plane_total - plane_sum, kuno_total - kuno_sum


def UnsaturatedCluster(cluster):
    """
    Determine the light yield from a cluster, but also
    check for saturation effects.
    """
    isSaturated = False
    npe_sum = 0
    for digit in cluster.get_digits():
        if abs(digit.get_adc() - 255) < 0.5:
            isSaturated = True
        npe_sum += digit.get_npe()

    if isSaturated:
        return 0.0
    else:
        return npe_sum


def FindDeadChansHist(hist):
    """
    Find dead channels from a histogram of a planes channel
    hits which combined to make tripets.
    """
    deadchs = []

    ch_START = 0
    ch_MAX = 215
    fit_W = 50

    fitfunc = ROOT.TF1("tf1", "pol4", ch_START, ch_MAX)

    for ch in range(ch_START, ch_MAX):

        # Set up fit range with bounds checking:
        fit_low = ch - fit_W/2
        fit_high = ch + fit_W/2
        if fit_low < 0:
            fit_high -= fit_low
            fit_low = 0
        if fit_high > ch_MAX:
            fit_low -= fit_high - ch_MAX
            fit_high = ch_MAX

        # Now perform a fit:
        hist.Fit(fitfunc, "", "", fit_low, fit_high)

        est_val = fitfunc.Eval(ch)
        if est_val < 0:
            est_val = 0.0
        meas_val = hist.GetBinContent(hist.FindBin(ch))

        if meas_val < 0.2*est_val:
            deadchs.append({"channel": ch,
                            "probability": est_val/hist.GetEntries()})

    return deadchs


def StationDeadProbability(deadchs):
    """
    Function to estimate the probability of a hit intersecting
    dead station channels
    """

    probsum = 0.0

    # Find probability of all possible hit combinations:
    for d in deadchs:
        for dd in deadchs:
            if d["plane"] != dd["plane"]:
                probsum += d["probability"]*dd["probability"]

    return probsum