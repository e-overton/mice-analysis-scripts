"""
Some tools for processing spacepoints.. (and now clusters)

"""


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