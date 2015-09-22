#!/usr/bin/env python

import ROOT

class ClusterLightYield:
    """
    Class to compute the light yield from the scifi clusters.
    
    Note, this uses the technique in the Tracker NIM paper
    to help compensate for saturated channels.
    """

    # Uniquie identifier of class, its a static which
    # we inrement at construction.
    uid = 0

    
    def __init__(self, lookup, name=None):
        """
        Make the class objects
        """

        if name is None:
            self.name = "ClstrLY_%i"%self.uid
        else:
            self.name = "ClstrLY_%s"%name
        self.uid += 1
        
        # Front end lookup object
        self.lookup = lookup
        
        # Histogram Creation
        self.raw_hist = ROOT.TH1D(self.name+"_raw",\
                                  self.name+"_raw; Light Yield (P.E.); Events",\
                                  50, -0.5, 49.5)
        
        self.cut_hist = ROOT.TH1D(self.name+"_cut",\
                                  self.name+"_cut; Light Yield (P.E.); Events",\
                                  50, -0.5, 49.5)

        self.ly_hist = ROOT.TH1D(self.name+"_ly",\
                                 self.name+"_ly; Light Yield (P.E.); Events",\
                                 50, -0.5, 49.5)

        self.prob_hist = ROOT.TH1D(self.name+"_prob",\
                                   self.name+"_prob; Light Yield (P.E.); Non-Saturated Probability",\
                                   50, -0.5, 49.5)



    def FillCluster(self, cluster, lookup=None):
        """
        Fill the histograms using the 
        """
        
        if lookup is None:
            lookup = self.lookup

        digits = cluster.get_digits()
        n_digits = len (digits)
        if n_digits == 2:
            return

        # Fill light yield histograms:
        npe = 0
        saturated = False
        bad = False
        for d in digits:

            # Extract light yield infomation:
            npe += d.get_npe()
            if (d.get_adc() > 245.5):
                saturated = True

            # Extract saturation infomation:
            saturation_pe = lookup.GetChannelSaturationPE\
                            (d.get_tracker(), d.get_station(),\
                             d.get_plane(), d.get_channel())

            if saturation_pe < 0.2:
                bad = True
            else:
                # Fill probability histogram:
                for b in range(1, self.prob_hist.GetNbinsX() +1 ):
                    bin_npe =  self.prob_hist.GetBinCenter(b)
                    if (bin_npe/n_digits < saturation_pe):
                        self.prob_hist.Fill(bin_npe)

        # Fill the raw and cut histograms
        if not bad:
            self.raw_hist.Fill(npe)
            if not saturated:
                self.cut_hist.Fill(npe)
            

    def ProcessResult(self):
        """
        Function to generate the ly hist from existing data.
        """

        # Chose a sclae factor so the maximum bin entry 1
        # in the prob histogram.
        scale_factor = float(1.0/self.prob_hist.GetMaximum())

        self.prob_hist_scaled = self.prob_hist.Clone(self.name+"_scprob")
        self.prob_hist_scaled.Scale(scale_factor)

        # Copy results into 
        self.ly_hist.Reset()
        self.ly_hist.Add(self.cut_hist)
        self.ly_hist.Divide(self.prob_hist_scaled)


    def FitPoisson(self, hist):
        """
        Function to attempt a poission fit on the specified hist.
        """
        self.PoissonFit = ROOT.TF1('PoissonFit', fitfunction_poisson, 4, 22, 3)
        self.PoissonFit.SetParameter(0, 1)
        self.PoissonFit.SetParameter(1, 1)
        self.PoissonFit.SetParameter(2, 1)

        hist.Fit(self.PoissonFit,"","",3,25)

    def MakeDrawCanvas(self):
        """
        Finally make me a canvas of the results
        """
        
        self.ProcessResult()

        self.legends = []

        self.c = ROOT.TCanvas(self.name+"_cnv", self.name, 900, 500)
        self.c.Divide(2,1)

        # Draw Light Yields
        self.c.cd(1)
        
        self.raw_hist.SetLineColor(ROOT.kGray)
        self.raw_hist.Draw()
        self.raw_hist.GetYaxis().SetTitleOffset(1.4)
        
        self.cut_hist.SetLineColor(ROOT.kRed)
        self.cut_hist.Draw("SAME")

        self.ly_hist.SetLineColor(ROOT.kBlack)
        self.ly_hist.Draw("SAME")

        self.raw_hist.GetYaxis().SetTitleOffset(1.4)

        self.legends.append(ROOT.TLegend(0.55,0.60,0.97,0.76))
        self.legends[-1].AddEntry(self.raw_hist, "Saturated")
        self.legends[-1].AddEntry(self.cut_hist, "Unsaturated")
        self.legends[-1].AddEntry(self.ly_hist, "Unsaturated rescaled")
        self.legends[-1].Draw()

        #self.FitPoisson(self.ly_hist)
        

        # Draw probs:
        self.c.cd(2)
        self.prob_hist_scaled.Draw()
        self.prob_hist_scaled.GetYaxis().SetTitleOffset(1.4)

    
def fitfunction_poisson(x, par):
    """
    poisson fit function shamelessly stolen from:
    https://root.cern.ch/phpBB3/viewtopic.php?t=18740
    """
    if par[2] != 0:
        if ROOT.TMath.Gamma((x[0]/par[2])+1) != 0:
            poisson = par[0] * ROOT.TMath.Power((par[1]/par[2]),(x[0]/par[2]))\
                      * (ROOT.TMath.Exp(-(par[1]/par[2])))/ROOT.TMath.Gamma((x[0]/par[2])+1)
        else:
            poisson = 0
    else:
        poisson = 0
        
    return poisson

        
