"""
Channel Analysis

does some light yield analysis from the tracker
"""

# Imports:
from SpacepointTools import missingFromDuplet
import FrontEndLookup
import ROOT
import math

# Parameters:


class ChannelAnalysis:
    """
    An analysis object to collect and then process
    infomation from a single channel inside the detector.
    """
    unique_counter = 0

    def __init__(self, loaddict=None, name=None, felookup=None):
        """
        Constructor.

        :argument name: Name of class
        :type name: string
        :argument felookup: Front end lookup object
        :type felookup: FrontEndLookup
        :argument channel: Channel data stored in {}
        :type channel: {}
        :
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

        :argument name: Name of class
        :type name: string
        :argument felookup: Front end lookup object
        :type felookup: FrontEndLookup
        """

        self.name = name
        self.uid = self.unique_counter
        self.unique_counter += 1

        self.frontEndLookup = felookup
        self.channel = -1
        self.station = -1
        self.plane = -1
        self.tracker = -1
        self.saturation_pe = -1

        # A log of the light yeilds, not stored as
        # a histogram to preserve unbinned data:
        self.npe_triplet = []
        self.npe_dumiss = []
        self.npe_duplet = []
        self.npe_single = []

    def process_end(self, recon):
        pass

    def process(self, digit, cluster, spacepoint=None, track=None):
        """
        Function for identifying if the channel is probably
        noise.

        :argument digit
        :type digit: ROOT.MAUS.SciFiDigit
        :argument cluster
        :type cluster: ROOT.MAUS.SciFiCluster
        :argument spacepoint
        :type spacepoint: ROOT.MAUS.SciFiSpacePoint

        :returns nothing
        """

        # Find an out if the hit is a triplet spacepoint, duplet
        # spacepoint, or a single hit.
        if (spacepoint is not None) and \
                (len(spacepoint.get_channels()) == 3):
            # Store the triplet light yield data:
            self.npe_triplet.append(self.getNPE_nonsaturated(digit))

        # Now inspect duplets:
        elif (spacepoint is not None) and \
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
            else:
                self.npe_duplet.append(self.getNPE_nonsaturated(digit))

        # Finally, if this is a single hit then update the single hits.
        else:
            self.npe_single.append(self.getNPE_nonsaturated(digit))
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
        :type felookup: FrontEndLookup
        """
        self.felookup = felookup

        # Construct array of channels:
        self.channels = [None] * self._get1dref(FrontEndLookup.N_Tracker,
                                                1, 0, 0)

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
                        # Store infomation for tracker, station, plane, channel
                        self.channels[cid].tracker = tracker
                        self.channels[cid].station = station
                        self.channels[cid].plane = plane
                        self.channels[cid].channel = channel

                        # Compute local saturation PE:
                        try:
                            fe = felookup.GetChannel(tracker, station,
                                                     plane, channel)
                            self.channels[cid].saturation_pe = \
                                (255-fe["adc_pedestal"])/fe["adc_gain"]

                        except:
                            print "Failed to find saturation for %s" % n

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

        :returns nothing
        """

        cid = self._get1dref(digit.get_tracker(), digit.get_station(),
                             digit.get_plane(), digit.get_channel())

        self.channels[cid].process(digit, cluster, spacepoint, track)

    def process_end(self, recon):
        pass

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
        :param channels, list of channel analysis objects
        :type channels: [ChannelAnalysis]
        """

        if not isinstance(channels, list):
            channels = [channels]

        for c in channels:
            assert isinstance(c, ChannelAnalysis)

        self.basename = "hly_"

        # Generate the histogram objects:
        self.h_ly_triplet = self.generateLYHistogram(self.basename+"triplet")
        self.h_ly_dumiss = self.generateLYHistogram(self.basename+"dumiss")
        self.h_ly_duplet = self.generateLYHistogram(self.basename+"duplet")
        self.h_ly_single = self.generateLYHistogram(self.basename+"single")

        # Fill
        for c in channels:
            self.fillChannel(c)

        # Store channel data persistently:
        self.channels = channels

    def generateLYHistogram(self, name):
        """
        generate and return a histogram from the data presented

        :param name: Name of histogram
        :type name: string

        :rtype ROOT.TH1D
        :returns histogram object
        """

        axistitle = ";Light Yield (npe); Events"
        h = ROOT.TH1D(name, name + axistitle, 30, -0.5, 29.5)

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

    def findLightYield(self):
        """
        Function to evaluate the light yield of this tracker
        fibre. Using RooFit unbinned likelihood fitter.
        """
        max_npe = 0
        for c in self.channels:
            for n in c.npe_triplet:
                if n > max_npe:
                    max_npe = n

        # Check that we actulalry found a hit 
        if max_npe == 0:
            return 0.0, 0.0

        # Observable: n photo electrons
        npe = ROOT.RooRealVar("npe", "npe", 2, 30)
        npe.setRange("R1", 5, math.floor(max_npe))

        # Generate Roo dataset
        argset = ROOT.RooArgSet()
        argset.add(npe)
        dataset = ROOT.RooDataSet("data", "data", argset)
        for c in self.channels:
            for n in c.npe_triplet:
                if n > 1:
                    npe.setVal(n)
                    dataset.add(argset)

        # Parameterisation (poission, with mean=npe_mean)
        npe_mean = ROOT.RooRealVar("npe_mean", "npe_mean", 3, 20)
        poisson = ROOT.RooPoisson("lightyield", "ly", npe, npe_mean)

        poisson.fitTo(dataset, ROOT.RooFit.Range("R1"))

        # PLot.
        # frame = npe.frame()
        # dataset.plotOn(frame)
        # poisson.plotOn(frame)
        # frame.Draw()
        # raw_input("test")

        return npe_mean.getValV(), npe_mean.getError()

    def parameteriseLightYield(self, dataname):
        """
        Function to parameterise the light yield from the
        detector hits, using two poissons, with independent
        integrals..
        """

        datanames = ["triplet", "dumiss", "duplet", "single"]

        max_npe = 0
        for c in self.channels:
            for dataname in datanames:
                for n in getattr(c, "npe_%s" % dataname):
                    if n > max_npe:
                        max_npe = n

        # Check that we actulalry found a hit 
        if max_npe == 0:
            return "FAIL"

        # Generate some datasets. One for triplet, duplet and singlet
        npe = ROOT.RooRealVar("npe", "npe", 0, 30)
        npe_arg = ROOT.RooArgSet()
        npe_arg.add(npe)

        npe.setRange("R1", 2, math.floor(max_npe))
        datasets = {}
        sample = ROOT.RooCategory("sample", "sample")
        for dataname in datanames:
            datasets[dataname] = ROOT.RooDataSet("data_%s" % dataname,
                                                 "data_%s" % dataname,
                                                 npe_arg)
            sample.defineType(dataname)
            for c in self.channels:
                for n in getattr(c, "npe_%s" % dataname):
                    if n > 1:
                        npe.setVal(n)
                        datasets[dataname].add(npe_arg)

        # Generate the combined dataset:
        data_all = ROOT.RooDataSet\
            ("combData", "combined data", npe_arg, ROOT.RooFit.Index(sample),
             ROOT.RooFit.Import("triplet", datasets["triplet"]),
             ROOT.RooFit.Import("dumiss", datasets["dumiss"]),
             ROOT.RooFit.Import("duplet", datasets["duplet"]),
             ROOT.RooFit.Import("single", datasets["single"]))

        # Generate Data Model:
        hit_mean = ROOT.RooRealVar("hit_mean", "hit_mean", 5, 20)
        hit_pdf = ROOT.RooPoisson("hit_ly", "hit_ly", npe, hit_mean)
        noise_decay = ROOT.RooRealVar("noise_decay", "noise_decay", -2, 2)
        noise_pdf = ROOT.RooExponential("noise_ly", "noise_ly", npe, noise_decay)
        simultaneous_pdf = ROOT.RooSimultaneous("simpdf","simultaneous pdf",sample)

        # Include all the fits we want to do:
        n = {}
        pdf = {}
        for dataname in datanames:
            n["hit_%s" % dataname] = ROOT.RooRealVar("hit_%s_n" % dataname,
                                                     "hit_%s_n" % dataname, 0, 10000)

            n["noise_%s" % dataname] = ROOT.RooRealVar("noise_%s_n" % dataname,
                                                       "noise_%s_n" % dataname, 0, 10000)

            pdf["hit_%s" % dataname] = ROOT.RooExtendPdf("hit_%s_ep" % dataname,
                                                         "hit_%s_ep" % dataname,
                                                         hit_pdf, n["hit_%s" % dataname])

            pdf["noise_%s" % dataname] = ROOT.RooExtendPdf("noise_%s_ep" % dataname,
                                                           "noise_%s_ep" % dataname,
                                                           noise_pdf, n["noise_%s" % dataname])

            pdf["comb_%s" % dataname] = ROOT.RooAddPdf("comb_%s" % dataname,
                                                       "hit+noise comb %s" % dataname,
                                                       ROOT.RooArgList(pdf["hit_%s" % dataname],
                                                                       pdf["noise_%s" % dataname]))
            simultaneous_pdf.addPdf(pdf["comb_%s" % dataname], dataname)

        simultaneous_pdf.fitTo(data_all)

        #Drawing functionality...
        triplet_frame = npe.frame(ROOT.RooFit.Bins(30),
                                  ROOT.RooFit.Title("TripletFit"))
        
        datasets["triplet"].plotOn(triplet_frame)
        simultaneous_pdf.plotOn(triplet_frame,datasets["triplet"])
        
        triplet_frame.Draw()
        
        raw_input("hang on")
        


    def fillChannel(self, channel):
        """
        Fill the internal histogram objects from the channel

        :param channel: Input channel to fill from
        :type channel: ChannelAnalysis
        """

        self.fillLYHistogram(self.h_ly_triplet, channel.npe_triplet)
        self.fillLYHistogram(self.h_ly_dumiss, channel.npe_dumiss)
        self.fillLYHistogram(self.h_ly_duplet, channel.npe_duplet)
        self.fillLYHistogram(self.h_ly_single, channel.npe_single)

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

        self.h_ly_duplet.SetLineColor(ROOT.kBlue)
        self.h_ly_duplet.Draw("Same")

        self.h_ly_single.SetLineColor(ROOT.kViolet)
        self.h_ly_single.Draw("Same")
        

