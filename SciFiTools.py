"""
Some tools for processing spacepoints.. (and now clusters)

"""

import ROOT
from array import array
from math import sqrt, pow
from ROOTTools import TemplateFitter, IntegrateExpErr
import math
import numbers


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
    npe_sum = 0.0
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
        fitresults = hist.Fit(fitfunc, "SNQ", "", fit_low, fit_high)
        est_val = fitfunc.Eval(ch)
        if est_val < 0:
                est_val = 0.0
        # get error:
        conf_int = array('d',[0])
        fitresults.GetConfidenceIntervals(1, 1, 1, array('d',[ch]),
                                          conf_int, 0.683, False)
        est_val_err = conf_int[0]

        meas_val = hist.GetBinContent(hist.FindBin(ch))

        # Tweaked to resuce false positives:
        if meas_val < 0.2*(est_val-3*est_val_err) and est_val > 10:
            deadchs.append({"channel": ch,
                            "probability": est_val/hist.GetEntries(),
                            "prob_error": est_val_err/hist.GetEntries()})

    return deadchs


def StationDeadProbability(deadchs):
    """
    Function to estimate the probability of a hit intersecting
    dead station channels
    """

    probsum = 0.0
    probsum_err = 0.0

    # Find probability of all possible hit combinations:
    for d in deadchs:
        for dd in deadchs:
            if d["plane"] != dd["plane"]:
                val = d["probability"]*dd["probability"]
                val_error = val*sqrt(pow(d["prob_error"]/d["probability"], 2) +
                                     pow(dd["prob_error"]/dd["probability"], 2) )
                probsum += val
                probsum_err += val_error

    return probsum, probsum_err


def LightYieldFinder(histo):
    """
    Process a 1D histogram to find the estimated
    light yield.
    """
    low_npe = 2
    high_npe = low_npe
    for i in range(histo.GetNbinsX()):
        if histo.GetBinContent(i):
            high_npe = histo.GetBinLowEdge(i)

    # poisson
    f_poisson = ROOT.TF1("f1", "[0]*TMath::Power(([1]/[2]),(x/[2]))"\
                         "*(TMath::Exp( ([1]/[2])))/TMath::Gamma((x/[2])+1)", 0, 5)
    f_poisson.SetParameters(1E-4, 12, 2)

    histo.Fit(f_poisson, "", "", low_npe, high_npe)
    return {"npe": f_poisson.GetParameter(1),
            "npe_e": f_poisson.GetParError(1)}


############################################################################
class TrackEfficiency:
    """
    Do a simple track efficiency calculation

    TODO; fix for helical running. At present "feducials"
    do not work with field.
    """

    def __init__(self, tracker, name=None):
        """
        Initilise elements:
        """
        self.tracker = tracker
        if name is None:
            self.name = "tke_%i_%i" % tracker
        else:
            self.name = name

        self.all_tracks = [0]*6 # Number of track points:
        self.feducial_tracks = [0]*6

    def fill(self, recon_event):
        """
        Fill with track statistics
        """
        all_tracker_tracks = []
        feducial_tracker_tracks = []
        helical_found = False
        feducial_found = False
        z_stn_5 = 1100

        # Add helical tracks to the efficiency logging
        for track in recon_event.GetSciFiEvent().helicalprtracks():
            if track.get_tracker() == self.tracker:
                helical_found = True
                all_tracker_tracks.append(len(track.get_spacepoints()))

        # Add straight tracks to the efficiency logging
        for track in recon_event.GetSciFiEvent().straightprtracks():
            if track.get_tracker() == self.tracker:
                all_tracker_tracks.append(len(track.get_spacepoints()))

                # Apply a feducial cut on the track to ensure it remains inside
                # the tracker at both ends:
                r_st1 = math.sqrt(track.get_x0()**2 + track.get_y0()**2)
                r_st5 = math.sqrt((track.get_x0()+z_stn_5*track.get_mx())**2 + 
                                  (track.get_y0()+z_stn_5*track.get_my())**2)

                # select all those within a 13cm radius:
                if (r_st1 < 100) and (r_st5 < 100):
                    feducial_tracker_tracks.append(len(track.get_spacepoints()))
                    feducial_found = True

        # Get longest track
        if len (all_tracker_tracks) == 0:
            self.all_tracks[0] += 1
        else:
            self.all_tracks[max(all_tracker_tracks)] += 1

        # Only add longest track data if no helical track was found.
        if not helical_found:
            if len (feducial_tracker_tracks) == 0:
                self.feducial_tracks[0] += 1
            else:
                self.feducial_tracks[max(feducial_tracker_tracks)] += 1


    def compute(self):
        """
        Calculate the efficiency of 5-spacepoint tracks,
        and of various things..
        """

        self.eff_all_5p, self.eff_all_5p_err = self.efficiency(self.all_tracks[5], sum(self.all_tracks))
        self.eff_all_all, self.eff_all_all_err = self.efficiency(sum(self.all_tracks[1:6]), sum(self.all_tracks))

        self.eff_fed_5p, self.eff_fed_5p_err = self.efficiency(self.feducial_tracks[5], sum(self.feducial_tracks))
        self.eff_fed_all, self.eff_fed_all_err = self.efficiency(sum(self.feducial_tracks[1:6]), sum(self.feducial_tracks))



    def efficiency(self, hit, total):
        """
        Return efficiency and errors:
        """

        if total > 0:
            return float(hit)/total, math.sqrt(hit)/total
        return 0, 1

    def getTObjects(self):
        """
        Return any internal TObjects
        """
        rval = {}
        #rval["%s_st_trackeff"%self.name] = self.st_trackeff
        #rval["%s_st_speff"%self.name] = self.st_speff
        #for s in self.spes:
        #    rval.update(s.getTObjects())
        return rval

############################################################################
class StationSpacePointEfficiency:
    """
    Class! to calculate the efficiency of a single station
    using, trying to account for doublet noise quantities.
    """

    def __init__(self, tracker, station, name=None):
        """
        Initlise an empty class:
        """
        self.tracker = tracker
        self.station = station

        if name is None:
            self.name = "spe_%i_%i" % (tracker, station)
        else:
            self.name = name

        # Keep track of number of efficiency
        # entries
        self.events = 0
        self.c_triplet = 0
        self.c_doublet = 0
        self.c_nothing = 0

        # Make ROOT Objects:
        self.triplet_ly = ROOT.TH1D(self.name+"_triplet_ly",
                                    self.name+"_triplet_ly",
                                    30, -0.5, 29.5)
        self.doublet_ly = ROOT.TH1D(self.name+"_doublet_ly",
                                    self.name+"_doublet_ly",
                                    30, -0.5, 29.5)

    def fill(self, recon_event):
        """
        Add the reconstucted event to this station's
        efficiency calculation.
        """

        self.events += 1

        # First loop over hits to identify any triplets in the
        # selected station
        tripletfound = False
        for sp in recon_event.GetSciFiEvent().spacepoints():
            if (sp.get_tracker() == self.tracker) and\
               (sp.get_station() == self.station):

                if len(sp.get_channels()) == 3:
                    tripletfound = True
                    self.c_triplet += 1
                    for cluster in sp.get_channels():
                        self.triplet_ly.Fill\
                            (UnsaturatedCluster(cluster))
                    # Found a triplet spacepoint, so no point
                    # to looking further.
                    break

        # Identify stations without triplets and store duplet
        # infomation (all, will do noise suppression at the
        # final step).
        doubletfound = False
        if not tripletfound:
            for sp in recon_event.GetSciFiEvent().spacepoints():
                if (sp.get_tracker() == self.tracker) and\
                   (sp.get_station() == self.station):
                    if len(sp.get_channels()) == 2:
                        doubletfound = True
                        self.c_doublet += 1
                        for cluster in sp.get_channels():
                            self.doublet_ly.Fill\
                                (UnsaturatedCluster(cluster))

        if not doubletfound and not tripletfound:
            self.c_nothing += 1

    def compute(self):
        """
        Final step in the analysis process, use the light yields
        to accurately count the number of hits in this plane
        of the detector.
        """
        print ""
        print " ============================================="
        print " = Now Processing: Tracker %i, Station %i ======"\
            % (self.tracker, self.station)

        if self.events == 0:
            print " No events to process!"
            print " Skipping calculation."
            print ""
            return False

        # To understand the duplet stuff, we need to fit the light yields to
        # estimate the SNR from the duplets.
        bkg = ROOT.TF1("bkg", "expo", 2, 25)
        tempfunc = TemplateFitter(self.triplet_ly, bkg)
        fit = ROOT.TF1("f", tempfunc, 2, 25, 4)
        fit.SetParameter(0, 0.05)
        fit.SetParameter(1, 100000)
        fit.FixParameter(2, 0)
        fit.SetParameter(3, -0.3)
        self.doublet_ly.Fit(fit, "RQN", "", 2, 25)

        # Use template to estimate number of real duplets:
        print "Template fraction:",
        print fit.GetParameter(0), fit.GetParError(0)
        print "Template integral:",
        print self.triplet_ly.GetEntries()

        # Enter raw statistics:
        intg, intg_err = IntegrateExpErr(fit.GetParameter(3),
                                         fit.GetParError(3), 2, 10)
        n_noise = intg*fit.GetParameter(1)
        n_noise_err = n_noise*math.sqrt(math.pow(intg_err/intg, 2) +
                                        math.pow(fit.GetParError(1) /
                                                 fit.GetParameter(1), 2))

        print " ---------------------------------------------"
        print " N Events:            %i" % self.events
        print " N Triplets:          %i" % self.c_triplet
        print " N Doublets:          %i" % self.c_doublet
        print " N Noise Doublets:    %.2f +- %.2f" % (n_noise, n_noise_err)
        
        # Now subtract the estimated noise events:
        # Note that the histogram gets filled twice per duplet.
        #if (n_noise_err > n_noise*2) or (n_noise < 0) or (n_noise/2 > self.c_doublet):
        #    n_duplets = self.c_doublet
        #    n_duplets_err = math.sqrt(n_duplets)
        #else:
        #    n_duplets = self.c_doublet - n_noise/2
        #    n_duplets_err = math.sqrt(n_duplets)/2 + n_noise_err/2

        # Estimate from integral of template.
        n_duplets = self.triplet_ly.GetEntries()*fit.GetParameter(0)/2.
        n_duplets_err = self.triplet_ly.GetEntries()*fit.GetParError(0)/2.
        
        n_real = self.c_triplet + n_duplets
        if n_real < 0: n_real =0
        if n_real > self.events: n_real=self.events
        #n_real_err = math.sqrt(self.c_triplet) + n_duplets_err # old non binomial method
        n_real_err = math.sqrt(n_real*abs(1-n_real/self.events) + n_noise_err*n_noise_err)
        print " N Real Doublets:     %.2f +- %.2f" % (n_duplets, n_duplets_err)
        print " N Real Events:       %.2f +- %.2f" % (n_real, n_real_err)

        self.eff = float(n_real)/self.events
        self.eff_err = float(n_real_err)/self.events

        print " Combined Efficiency: %f, +-: %f" % (self.eff, self.eff_err)
        
        return True

    def getTObjects(self):
        """
        Function to collate and return all root objects:
        Loops over the dictionary - checking types to pull
        out all ROOT objects.
        """

        return {key : self.__dict__[key] for key in self.__dict__
                if isinstance(self.__dict__[key], ROOT.TObject)}

    def getParams(self):
        """
        Get parameters from the class:
        Loops over the class dictionary, checks types to
        pull out numbers.
        """
        return {key : self.__dict__[key] for key in self.__dict__
                if isinstance(self.__dict__[key], numbers.Number)}

