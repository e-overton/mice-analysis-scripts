import pickle
import ROOT

from ChannelAnalysis import ChannelAnalysisResultsProcessor, ChannelAnalysisDigtProcessor
import FrontEndLookup


class TemplateFitter:

    def __init__(self, template, function):
        """
        Constructor, saves histogram and template objects.
        """
        self.template = template
        self.function = function

    def __call__(self, x, par):
        """
        Performs the fit using the parameters...
        [0] Multiple of template
        [1] Multiple of function
        [2:] Function parameters.
        """
        x=x[0]

        # Evaluate Histogram
        template_bin = self.template.FindBin(x)
        template_value = self.template.GetBinContent(template_bin)

        # Evaluate Fit Function
        for i in range(self.function.GetNpar()):
            self.function.SetParameter(i, par[2+i])
        function_value = self.function(x)

        return template_value*par[0] + function_value*par[1]

d = pickle.load(file("dpro2.pickle"))
# assert isinstance(d, ChannelAnalysisDigtProcessor)

chsplit = FrontEndLookup.N_Channel * FrontEndLookup.N_Plane *\
             FrontEndLookup.N_Station
c_us = ChannelAnalysisResultsProcessor(d.channels[0:chsplit])
c_ds = ChannelAnalysisResultsProcessor(d.channels[chsplit:])

c_ds = ChannelAnalysisResultsProcessor(d.channels[4300:4340])
cn = ROOT.TCanvas("c","c", 800, 600)
#cn.Divide(2,1)
#cn.cd(1)
c_ds.h_ly_triplet.Draw()
#cn.cd(2)
#c_ds.h_ly_triplet.Draw()

#cn.cd(1)
#c_us.draw()
#cn.cd(2)
#c_ds.draw()

#c.h_ly_triplet.Draw()

bkg = ROOT.TF1("bkg", "expo", 3, 25)
tempfunc = TemplateFitter(c_ds.h_ly_triplet, bkg)
fit = ROOT.TF1("f", tempfunc, 2, 25, 4)
fit.SetParameter(0, 0.02)
fit.SetParameter(1, 500000)
fit.SetParameter(2, 0.4)
fit.SetParameter(2, -1.3)


c_ds.h_ly_duplet.Fit(fit, "R", "SAME", 3, 20)

# Use the triplet light yield as a base model:

raw_input("End")
