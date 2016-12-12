"""
Some generic ROOT Tools. 

"""
import math

class TemplateFitter:
    """
    Class to allow a TH1D (template) + TF1 to be fitted to a TH1.

    tempfunc = TemplateFitter(th1d_template, tf1_name)
    fit = ROOT.TF1("f", tempfunc, 2, 25, 4) #Fir params = 2+th1 params

    note fit params are p[0]*template + p[1]*function + function params
    """

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

def IntegrateExpErr(a, a_error, start, stop):
    """
    Calculat the inegral of e(ax) integrated between
    start and stop.
    """

    integral = 1/a*(math.exp(a*stop) - math.exp(a*start))
    dida = -1/a/a*(math.exp(a*stop) - math.exp(a*start))\
        + 1/a*(stop*math.exp(a*stop) - start*math.exp(a*start))
    error = a_error*dida

    return integral, error

def CombinedNorm(hists):
    """
    Normalise an array of histograms to 1 over all
    """
    
    entries = 0
    for h in hists:
        entries += h.GetEntries()
    
    try:
        rescale = 1/entries
    except:
        rescale = 1
    
    for h in hists:
        h.Scale(rescale)
    