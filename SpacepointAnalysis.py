"""
Spacepoint Analysis...

Multiplicity Processor for evaulating the spacepoint multiplicity...
"""

import ROOT
from PlotSciFiEvent import PlotSciFiEvent


class SpacepointMultiplicityProcessor:
    """
    Class to collect spacepoint multiplicity infomation.
    """

    def __init__(self, tracker):
        """
        Construct internal objects..
        """

        self.spacepoints_used = []
        self.spacepoints_used_this = 0
        self.spacepoints_solo = []
        self.spacepoints_solo_this = 0

        self.tracker = tracker

    def process(self, spacepoint, track):
        """
        Process the spacepoint with an assosiated track
        """

        if spacepoint.get_tracker() == self.tracker:

            if track is None:
                self.spacepoints_solo_this += 1
            else:
                self.spacepoints_used_this += 1

    def process_end(self, recon_event):
        """
        Append the counts and reset the counters.
        """
        self.spacepoints_used.append(self.spacepoints_used_this)
        self.spacepoints_used_this = 0

        self.spacepoints_solo.append(self.spacepoints_solo_this)
        self.spacepoints_solo_this = 0

        """ Not using plot functions:
        if self.spacepoints_used[-1] == 0 and \
           self.spacepoints_solo[-1] > 4:

            # print ("test")
            if self.tracker == 1:
                plot = PlotSciFiEvent()
                plot.fill(recon_event)
                plot.draw()
                raw_input("Waiting...")
        """


class SpacepointMultiplicityResultsProcessor:
    """
    Class to display spacepoint multiplicity results.
    """

    def __init__(self, name):
        """
        Add the spacepoint multiplicity to the thing

        :type name: string
        """
        self.name = name
        self.track_mult = ROOT.TH1D("h_%s_trk" % self.name,
                                    "h_%s_trk" % self.name,
                                    7, -0.5, 6.5)

        self.sp_mult = ROOT.TH1D("h_%s_sp" % self.name,
                                 "h_%s_sp" % self.name,
                                 7, -0.5, 6.5)

        self.sp_all = ROOT.TH1D("h_%s_all" % self.name,
                                "h_%s_all" % self.name,
                                10, -0.5, 9.5)

    def append(self, ms):
        """
        Append Multuplicity infomation from a spacepoint multiplicity processor

        :type ms: SpacepointMultiplicityProcessor
        """

        for m in ms.spacepoints_solo:
            self.sp_mult.Fill(m)

        for m in ms.spacepoints_used:
            self.track_mult.Fill(m)

        for n, m in zip(ms.spacepoints_used, ms.spacepoints_solo):
            self.sp_all.Fill(n+m)
