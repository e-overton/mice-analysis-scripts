"""
Channel Analysis

does some light yield analysis from the 
"""

# Imports:
from SpacepointTools import missingFromDuplet
import FrontEndLookup
import ROOT

# Parameters:
# these should be tuned somehow to help find noise.
npe_digit_threshold = 0.
npe_spacepoint_threshold = 0.


class ChannelAnalysis:
    """
    An analysis object to collect and then process
    infomation from a single channel inside the detector.

    """

    unique_counter = 0

    def __init__(self, loaddict=None, name=None, felookup=None):
        """
        Constructor.
        """
        if not (loaddict is None):
            self.loaddict(loaddict)
        elif not (name is None):
            self.init(name, felookup)

    def loadDict(self, loaddict):
        """
        Pre load class from a python dictionary
        """

        # Load all keys:
        for key in loaddict:
            setattr(self, key, loaddict[key])

    def getDict(self):
        """
        Get a dictionary from the object
        """
        # Perform object serialisation tasks:
        # none
        # Return the dictionary:
        return self.__dict__

    def init(self, name, felookup):
        """
        Perform construction functions
        """

        self.name = name
        self.uid = self.unique_counter
        self.unique_counter += 1

        self.frontEndLookup = felookup
        self.npe_digit_threshold = npe_digit_threshold
        self.npe_spacepoint_threshold = npe_spacepoint_threshold

        # Some internal counters:
        self.decision_triplet = 0
        self.decision_duplet = 0
        self.decision_missing = 0
        self.decision_npehit = 0
        self.decision_npenoise = 0

        # A Light Yield Histogram:
        self.npe_triplet = []
        self.npe_dumiss = []
        self.npe_duhit = []
        self.npe_dunoise = []
        self.npe_singlehit = []
        self.npe_singlenoise = []

    def process(self, digit, cluster, spacepoint=None, track=None):
        """
        Fill function for filling the cluster with infomation.
        """
        noise = self.isNoise(digit, cluster, spacepoint, track)

    def isNoise(self, digit, cluster, spacepoint=None,
                track=None):
        """
        Function for identifying if the channel is probably
        noise.
        """

        # Find an out if the track is assosiated with a triplet
        # spacepoint:
        if not (spacepoint is None) and \
                (len(spacepoint.get_channels()) == 3):
            # Triplets are considered to be noise free by this analysis
            self.npe_triplet.append(self.getNPE_nonsaturated(digit))
            return False

        elif not (spacepoint is None) and \
                (len(spacepoint.get_channels()) == 2):

            # Determine if a missing channel could be blamed for
            # the forming of this duplet:
            missing = False
            missing_plane, missing_channel = missingFromDuplet(spacepoint)

            if self.frontEndLookup is not None:

                # Perform the looup for dead channels
                dead_channels = self.frontEndLookup.\
                    GetBadChannelsPlane(spacepoint.get_tracker(),
                                        spacepoint.get_station(),
                                        missing_plane)

                # See if a dead channel is in proximity to the missing channel
                for dead in dead_channels:
                    if abs(dead - missing_channel) < 2.0:
                        missing = True

            # Conditional check:
            if (missing):
                self.npe_dumiss.append(self.getNPE_nonsaturated(digit))
                return False
            elif (spacepoint.get_npe() > self.npe_spacepoint_threshold):
                self.npe_duhit.append(self.getNPE_nonsaturated(digit))
                return False
            else:
                self.npe_dunoise.append(self.getNPE_nonsaturated(digit))
                return True

        # Perform a final light yield check:
        if digit.get_npe() > self.npe_digit_threshold:
            self.npe_singlehit.append(self.getNPE_nonsaturated(digit))
            return False
        else:
            self.npe_singlenoise.append(self.getNPE_nonsaturated(digit))
            return True

    def getNPE_nonsaturated(self, digit):
        """
        Function to call to get the npe of a digit,
        where saturated channels are set to zero.
        """
        if abs(digit.get_adc() - 255) < 0.5:
            return 0
        else:
            return digit.get_npe()


class ChannelAnalysisDigtProcessor:
    """
    A class to wrap the channel analysis objects, so
    that it can be handled by the "MasterProcessor"
    """

    def __init__(self, felookup):
        """
        Some basic stuff to build all the channels!
        """
        self.felookup = felookup

        # Construct array of channels:
        self.channels = [None] * self._get1dref(FrontEndLookup.N_Tracker, 1, 0, 0)

        for tracker in range(FrontEndLookup.N_Tracker):
            for station in range(1, FrontEndLookup.N_Station+1):
                for plane in range(FrontEndLookup.N_Plane):
                    for channel in range(FrontEndLookup.N_Channel):

                        cid = self._get1dref(tracker, station, plane, channel)
                        n = "%s_%i_%i_%i" % (("US" if tracker == 0 else "DS"),
                                             station, plane, channel)

                        # Construct the actual channel objects
                        self.channels[cid] = ChannelAnalysis\
                            (loaddict=None, name=n, felookup=self.felookup)
                        # Store infomation for tracker, station, plane, channel:
                        self.channels[cid].tracker = tracker
                        self.channels[cid].station = station
                        self.channels[cid].plane = plane
                        self.channels[cid].channel = channel

    def process(self, digit, cluster, spacepoint, track):
        """
        This function decides what to call to do the processing of the
        digit

        :argument digit
        :type digit: ROOT.MAUS.SciFiDigit
        :argument cluster
        :type cluster: ROOT.MAUS.SciFiCluster
        :argument spacepoint
        :type spacepoint: ROOT.MAUS.SciFiSpacePoint
        :argument track [0-220]
        :type track: ROOT.MAUS.

        :returns nothing
        """

        cid = self._get1dref(digit.get_tracker(), digit.get_station(),
                             digit.get_plane(), digit.get_channel())

        self.channels[cid].process(digit, cluster, spacepoint, track)

    def _get1dref(self, tracker, station, plane, channel):
        """
        Get a 1 dimenstional referference which can be used to find the
        channel in tracker space.

        :argument tracker [0,1]
        :type tracker: int
        :argument station [1,2,3,4,5]
        :type station: int
        :argument plane [0,1,2]
        :type plane: int
        :argument channel [0-220]
        :type channel: int
        :rtype int
        :returns unique reference to channel
        """
        ref = channel + (plane + (station - 1 +
                                  tracker * FrontEndLookup.N_Station) *
                         FrontEndLookup.N_Plane) * FrontEndLookup.N_Channel
        return ref

    def _de1dref(self, ref):
        """
        Get a 1 dimenstional referference which can be used to find the
        channel in tracker space.
        :argument ref - the reference to dereferecne.
        :type ref: int
        :returns tracker, station, plane, channel
        """
        channel = ref % FrontEndLookup.N_Channel
        planeid = ref / FrontEndLookup.N_Channel
        plane = planeid % FrontEndLookup.N_Plane
        stationid = plane / FrontEndLookup.N_Plane
        station = stationid % FrontEndLookup.N_Station + 1
        tracker = stationid / FrontEndLookup.N_Station

        return tracker, station, plane, channel


class ChannelAnalysisResultsProcessor:
    """
    A class to process the results from a "channel Analysis" object.
    in order to generate some results.
    """

    def __init__(self, channels):
        """
        initilised using the "Channel Analusis" object.
        :param ChannelAnalysis, a Channel Analysis object to process. or 
        a list of objects.
        """

        if not isinstance(channels, list):
            channels = [channels]

        for c in channels:
            assert isinstance(c, ChannelAnalysis)

        self.basename = "hly_"

        # Generate the histogram objects:
        self.h_ly_triplet = self.generateLYHistogram(self.basename+"triplet")
        self.h_ly_dumiss = self.generateLYHistogram(self.basename+"dumiss")
        self.h_ly_duhit = self.generateLYHistogram(self.basename+"duhit")
        self.h_ly_dunoise = self.generateLYHistogram(self.basename+"dunoise")
        self.h_ly_sihit = self.generateLYHistogram(self.basename+"sihit")
        self.h_ly_simiss = self.generateLYHistogram(self.basename+"simiss")

        # Fill
        for c in channels:
            self.fillChannel(c)

    def generateLYHistogram(self, name, channels, key):
        """
        generate and return a histogram from the data presented

        :param name: Name of histogram
        :type name: string

        :rtype ROOT.TH1D
        :returns histogram object
        """

        axistitle = ";Light Yield (npe); Events"
        h = ROOT.TH1D(name, name + axistitle, 30, -0.5, 29.5)
        # for channel in channels:
        #    for npe in getattr(channel, key):
        #        h.Fill(npe)

        return h

    def fillLYHistogram(self, hist, npes):
        """
        Function to fill a histogram from a list of data

        :param hist: Histogram object to fill
        :type hist: ROOT.TH1D

        :param npes: Array of floats to fill histogram from
        :type npes: [number]
        """

        for npe in npes:
            hist.Fill(npe)

    def fillChannel(self, channel):
        """
        Fill the internal histogram objects from the channel

        :param channel: Input channel to fill from
        :type channel: ChannelAnalysis
        """

        self.fillLYHistogram(self.h_ly_triplet, channel.npe_triplet)
        self.fillLYHistogram(self.h_ly_dumiss, channel.npe_dumiss)
        self.fillLYHistogram(self.h_ly_duhit, channel.npe_duhit)
        self.fillLYHistogram(self.h_ly_dunoise, channel.npe_dunoise)
        self.fillLYHistogram(self.h_ly_sihit, channel.npe_singlehit)
        self.fillLYHistogram(self.h_ly_simiss, channel.npe_singlenoise)

    def draw(self):
        """
        Draw my histogram objects
        """

        self.c = ROOT.TCanvas("c", "c", 800, 600)
        self.c.cd()

        self.h_ly_triplet.SetLineColor(ROOT.kBlack)
        self.h_ly_triplet.Draw()

        self.h_ly_dumiss.SetLineColor(ROOT.kGreen)
        self.h_ly_dumiss.Draw("Same")

        self.h_ly_duhit.SetLineColor(ROOT.kBlue)
        self.h_ly_duhit.Draw("Same")

        # self.h_ly_dunoise.SetLineColor(ROOT.kRed)
        # self.h_ly_dunoise.Draw("Same")

        self.h_ly_sihit.SetLineColor(ROOT.kViolet)
        self.h_ly_sihit.Draw("Same")

        # self.h_ly_simiss.SetLineColor(ROOT.kOrange)
        # self.h_ly_simiss.Draw("Same")
