#!/usr/bin/env python

"""
Quick script for checking the alignment of the detector internals
using pattern recognition..
"""

import ROOT
import libMausCpp  # pylint: disable = W0611
import math
import TOFTools
import os


class SciFiAlign:
    """
    Function loops over all events in a TChain of reconstructed MICE
    data and makes verification plots of tracker alignment
    """

    def __init__(self):

        # Generate histogram objects to store residuals in each
        # station:
        self.tknames = ["us", "ds"]
        self.residuals = ["x_yres", "y_xres"]
        self.axestitle = {"x_yres": "x(mm); y-residual(mm)",
                          "y_xres": "y(mm); x-residual(mm)"}

        for tk in self.tknames:
            for res in self.residuals:
                for station in range(1, 6):
                    histname = "res_%s_%i_%s" % (tk, station, res)
                    histtitle = "%s station %i residual;%s" % \
                                (tk, station, self.axestitle[res])
                    hist = ROOT.TH2D(histname, histtitle, 30, -150, +150, 80, -10, +10)
                    setattr(self, histname, hist)

    def fill(self, recon_event):
        """
        Fill the histogram objects with data from the recon event
        after first checking the tracks
        """

        scifi_event = recon_event.GetSciFiEvent()

        # verify only a single spacepoint in each station
        # and only one track:
        for tk_id in range(len(self.tknames)):
            tk_numtracks = 0
            tk_numtracksp = 0
            tk_trackspsum = 0
            trk_hel = None
            tk_straight = None
            for track in scifi_event.helicalprtracks():
                if track.get_tracker() == tk_id:
                    tk_numtracks += 1
                    trk_hel = track
                    for sp in track.get_spacepoints():
                        tk_numtracksp += 1
                        tk_trackspsum += sp.get_station()
            for track in scifi_event.straightprtracks():
                if track.get_tracker() == tk_id:
                    tk_straight = track
                    tk_numtracks += 1
                    for sp in track.get_spacepoints():
                        tk_numtracksp += 1
                        tk_trackspsum += sp.get_station()

            # Process single helical track
            if (tk_numtracks == 1 and tk_numtracksp == 5 and
                    tk_trackspsum == 15 and trk_hel is not None):

                # Find circle parameters:
                #  s=R * true phi, so use this to find a fitted true phi
                phi_mz = trk_hel.get_dsdz()/trk_hel.get_R()
                phi_cz = trk_hel.get_line_sz_c()/trk_hel.get_R()
                R = trk_hel.get_R()
                x0 = trk_hel.get_circle_x0()
                y0 = trk_hel.get_circle_y0()

                # Loop over each spacepoit and fill the residual:
                for sp in trk_hel.get_spacepoints():
                    pos = sp.get_position()
                    this_phi = pos.z()*phi_mz + phi_cz
                    x_fit = R*math.cos(this_phi) + x0
                    y_fit = R*math.sin(this_phi) + y0
                    hn = "res_%s_%i" % (self.tknames[tk_id], sp.get_station())
                    getattr(self, hn+"_x_yres").Fill(pos.x(), pos.y() - y_fit)
                    getattr(self, hn+"_y_xres").Fill(pos.y(), pos.x() - x_fit)

    def process(self):
        """
        Process the collected data to obtain an estimate for alignment
        at each station
        """

        for tk in self.tknames:
            for res in self.residuals:
                for station in range(1, 6):
                    histname = "res_%s_%i_%s" % (tk, station, res)
                    profname = "resp_%s_%i_%s" % (tk, station, res)
                    fitname = "resf_%s_%i_%s" % (tk, station, res)
                    h = getattr(self, histname)

                    # silly profile to get mean - poor handling of tails:
                    #prof = h.ProfileX()

                    # More sophisticated fitter:
                    NBinsX = h.GetNbinsX()
                    Min = h.GetMean() - 1.0*h.GetRMS()
                    Max = h.GetMean() + 1.0*h.GetRMS()
                    prof = ROOT.TH1F(profname, profname, NBinsX,
                                     h.GetXaxis().GetBinLowEdge(1),
                                     h.GetXaxis().GetBinLowEdge(NBinsX+1))

                    for i in range(1, NBinsX+1):
                        proj = h.ProjectionY("_py", i, i)
                        if(proj.Integral(proj.FindBin(Min), proj.FindBin(Max))< 3):
                            continue
                        result = proj.Fit("gaus", "S", "", Min, Max);
                        prof.SetBinContent(i, result.Parameter(1));
                        prof.SetBinError(i, result.Error(1))
                        #if(MeanUncertainty)out->SetBinError(i, result->Error(1));
                        #else out->SetBinError(i, result->Parameter(2));

                    fit = ROOT.TF1("fitname", "pol1", -100, +100)
                    prof.Fit(fit, "R")
                    setattr(self, profname, prof)
                    setattr(self, fitname, fit)



    def print_results(self):
        """
        Display the results
        """

        print "==============================================================="
        print "TK, Station, Residual, Gradient, Intercept"
        for tk in self.tknames:
            for res in self.residuals:
                for station in range(1, 6):
                    fit = getattr(self, "resf_%s_%i_%s" % (tk, station, res))

                    print ("%s, %i, %s, %4.2f +/- %4.2f, %4.3f +/- %4.3f" % 
                           (tk, station, res, fit.GetParameter(1)*1000, fit.GetParError(1)*1000,
                            fit.GetParameter(0), fit.GetParError(0)))

    def draw_result(self, tkname, station, resname):
        """
        Draw a single residual
        """
        hist = getattr(self, "res_%s_%i_%s" % (tkname, station, resname))
        prof = getattr(self, "resp_%s_%i_%s" % (tkname, station, resname))
        fit = getattr(self, "resf_%s_%i_%s" % (tkname, station, resname))

        hist.Draw("COL")
        prof.SetLineColor(ROOT.kBlack)
        prof.Draw("SAME")
        fit.SetLineColor(ROOT.kBlack)
        fit.SetLineStyle(2)
        #fit.Draw("SAME")




if __name__ == "__main__":

    #infiles = ["/home/ed/MICE/data/08666_recon.root"]  # 170mev

    # bad 140mev data
    infiles = ["/home/ed/MICE/data/cooling/08681_recon.root"]
    tof01_low = 28
    tof01_high = 32
    
    # 170mev
    #infiles = ["/home/ed/MICE/data/08666_recon.root"]
    #tof01_low = 28
    #tof01_high = 30.5

    # good 240mev data
    #infiles = ["/home/ed/MICE/data/08672_recon.root"]
    #tof01_low = 26.5
    #tof01_high = 28.5
    
    #infiles = ["/home/ed/MICE/data/efficiency_investigation/high_sz_2_6_0.root"]
    
    #for MC
    #inpath = "/home/ed/MICE/data/efficiency_investigation/mc"
    #infiles = []
    #for f in os.listdir(inpath):
    #    if f[5:] == "_sim.root":
    #        infiles.append(os.path.join(inpath, f))
    #tof01_low = 28
    #tof01_high = 32
    
    max_spills = 0
    
    ###########################################################################

    tof_time = ROOT.TH1D("tof01", "tof01", 500, -50, +50)

    kr = [None]*30
    for i in range (30):
        kr[i] = ROOT.TH1D("kp_%i"%i, "kp_%i"%i, 100, -5, +5)

    chain = ROOT.TChain("Spill")
    for f in infiles:
        chain.AddFile(f)

    data = ROOT.MAUS.Data()  # pylint: disable = E1101
    chain.SetBranchAddress("data", data)

    align = SciFiAlign()

    # Begin the processing
    print "Beginning Processing"
    for i in range(chain.GetEntries()):
        print "Spill", i, "/", chain.GetEntries()
        if max_spills > 0 and i > max_spills:
            break
        chain.GetEntry(i)
        spill = data.GetSpill()
        if spill.GetDaqEventType() != "physics_event":
            continue

        for j, recon_event in enumerate(spill.GetReconEvents()):
            print j, ":",
               
            for time in TOFTools.TOF01Times(recon_event.GetTOFEvent().GetTOFEventSpacePoint(), 500):
                tof_time.Fill(time)
                
            # check TOF:
            if TOFTools.TOF01CoincidenceTime\
                    (recon_event.GetTOFEvent(), low_ns=tof01_low, 
                     high_ns=tof01_high):

                # Fill alignment data
                align.fill(recon_event)

                # Fill kalman data:
                for kalman_tracks in recon_event.GetSciFiEvent().scifitracks():
                    for tp in kalman_tracks.scifitrackpoints ():
                        id = tp.tracker()*15 + (tp.station()-1)*3 + tp.plane()
                        kr[id].Fill(tp.pull())
                

    align.process()
    align.print_results()

    c = []
    for tk in align.tknames:
            for res in align.residuals:
                c.append(ROOT.TCanvas("%s_%s"%(tk,res), "%s_%s"%(tk,res), 800, 600))
                c[-1].Divide(3, 2)
                for station in range(1, 6):
                    c[-1].cd(station)
                    align.draw_result(tk, station, res)
                
    #align.res_ds_5_x_yres.Draw()
    #tof_time.Draw()
    
    c1 = ROOT.TCanvas("c1", "c1", 800, 600)
    c1.Divide(5,3)
    for i in range (15):
        c1.cd(i+1)
        kr[i].Draw()
        
    c2 = ROOT.TCanvas("c2", "c2", 800, 600)
    c2.Divide(5,3)
    for i in range (15):
        c2.cd(i+1)
        kr[i+15].Draw()
        
    
    raw_input("Done")
            
            
            