"""
.. module:: likelihood_class
   :synopsis: Definition of the major likelihoods
.. moduleauthor:: Julien Lesgourgues <lesgourg@cern.ch>
.. moduleauthor:: Benjamin Audren <benjamin.audren@epfl.ch>

Contains the definition of the base likelihood class :class:`Likelihood`, with
basic functions, as well as more specific likelihood classes that may be reused
to implement new ones.

"""
import os
import numpy as np
import math
import warnings
import random as rd
import subprocess as sp
import re
import scipy.constants as const
import scipy.integrate
import scipy.interpolate
import scipy.misc
import sys
sys.path.insert(0, 'montepython/')
import io_mp


class Likelihood(object):
    """
    General class that all likelihoods will inherit from.

    """

    def __init__(self, path, data, command_line):
        """
        It copies the content of self.path from the initialization routine of
        the :class:`Data <data.Data>` class, and defines a handful of useful
        methods, that every likelihood might need.

        If the nuisance parameters required to compute this likelihood are not
        defined (either fixed or varying), the code will stop.

        Parameters
        ----------
        data : class
            Initialized instance of :class:`Data <data.Data>`
        command_line : NameSpace
            NameSpace containing the command line arguments

        """
        print("         (Internal MP): start to init Likelihood")
        self.name = self.__class__.__name__
        self.folder = os.path.abspath(os.path.join(
            data.path['MontePython'], 'likelihoods', self.name))
        #if os.path.isfile(os.path.abspath(os.path.join(self.folder, self.like_name+".data"))):
        #    print("Data file ",self.file," exists.")
        #else:
        #    print("Data file ",self.file," for likelihood", self.like_name, " does not exists. Make sure it is in ",self.folder, " and try again.")
        #    exit()  
        #if not data.log_flag:
        #    path = os.path.join(command_line.folder, 'log.param')

        #print("About to read from data file")
        # Define some default fields
        #self.data_directory = os.path.abspath(data.path['data'])
        self.data_directory = data.path['data']
        #print self.data_directory

        # Store all the default fields stored, for the method read_file.
        self.default_values = ['data_directory']

        # Recover the values potentially read in the input.param file.
        if hasattr(data, self.name):
            exec("attributes = [e for e in dir(data.%s) if e.find('__') == -1]" % self.name)
            for elem in attributes:
                exec("setattr(self, elem, getattr(data.%s, elem))" % self.name)

        # Read values from the data file
        self.read_from_file(path, data, command_line)
        
        # Default state
        self.need_update = True

        # Check if the nuisance parameters are defined
        error_flag = False
        #try:
        #    for nuisance in self.use_nuisance:
        #        if nuisance not in data.get_mcmc_parameters(['nuisance']):
        #            error_flag = True
        #            warnings.warn(
        #                nuisance + " must be defined, either fixed or " +
        #                "varying, for %s likelihood" % self.name)
        #    self.nuisance = self.use_nuisance
        #except AttributeError:
        #    self.use_nuisance = []
        #    self.nuisance = []
        
    def loglkl(self, cosmo, data):
        """
        Placeholder to remind that this function needs to be defined for a
        new likelihood.

        Raises
        ------
        NotImplementedError

        """
        raise NotImplementedError(
            'Must implement method loglkl() in your likelihood')

    def read_from_file(self, path, data, command_line):
        """
        Extract the information from the log.param concerning this likelihood.

        If the log.param is used, check that at least one item for each
        likelihood is recovered. Otherwise, it means the log.param does not
        contain information on the likelihood. This happens when the first run
        fails early, before calling the likelihoods, and the program did not
        log the information. This check might not be completely secure, but it
        is better than nothing.

        .. warning::

            This checks relies on the fact that a likelihood should always have
            at least **one** line of code written in the likelihood.data file.
            This should be always true, but in case a run fails with the error
            message described below, think about it.

        .. warning::

            As of version 2.0.2, you can specify likelihood options in the
            parameter file. They have complete priority over the ones specified
            in the `likelihood.data` file, and it will be reflected in the
            `log.param` file.

        """

        # Counting how many lines are read.
        counter = 0

        self.path = path
        self.dictionary = {}
        if os.path.isfile(path):
            data_file = open(path, 'r')
            for line in data_file:
                if line.find('#') == -1:
                    if line.find(self.name+'.') != -1:
                        # Recover the name and value from the .data file
                        regexp = re.match(
                            "%s.(.*)\s*=\s*(.*)" % self.name, line)
                        name, value = (
                            elem.strip() for elem in regexp.groups())
                        # If this name was already defined in the parameter
                        # file, be sure to take this value instead. Beware,
                        # there are a few parameters which are always
                        # predefined, such as data_directory, which should be
                        # ignored in this check.
                        is_ignored = False
                        if name not in self.default_values:
                            try:
                                value = getattr(self, name)
                                is_ignored = True
                            except AttributeError:
                                pass
                        if not is_ignored:
                            #print("is_ignored is True")
                            #print(name, " ", value)
                            exec('self.'+name+' = '+value)
                        value = getattr(self, name)
                        counter += 1
                        self.dictionary[name] = value
            data_file.seek(0)
            data_file.close()
        else:
            raise io_mp.ConfigurationError("Could not open file %s. Make sure it exists and check for typos!\n \t (Remember to pass the path to the file relative to your GAMBIT directory)" % path)


         #Checking that at least one line was read, exiting otherwise
        if counter == 0:
            raise io_mp.ConfigurationError(
                "No information on %s likelihood " % self.name +
                "was found in the %s file.\n" % path )

    
    def need_cosmo_arguments(self, data, dictionary):
        """
        Ensure that the arguments of dictionary are defined to the correct
        value in the cosmological code

        .. warning::

            So far there is no way to enforce a parameter where `smaller is
            better`. A bigger value will always overried any smaller one
            (`cl_max`, etc...)

        Parameters
        ----------
        data : dict
            Initialized instance of :class:`data`
        dictionary : dict
            Desired precision for some cosmological parameters

        """
        array_flag = False
        for key, value in dictionary.iteritems():
            try:
                data.cosmo_arguments[key]
                try:
                    float(data.cosmo_arguments[key])
                    num_flag = True
                except ValueError:
                    num_flag = False
                except TypeError:
                    num_flag = True
                    array_flag = True

            except KeyError:
                try:
                    float(value)
                    num_flag = True
                    data.cosmo_arguments[key] = 0
                except ValueError:
                    num_flag = False
                    data.cosmo_arguments[key] = ''
                except TypeError:
                    num_flag = True
                    array_flag = True
            if num_flag is False:
                if data.cosmo_arguments[key].find(value) == -1:
                    data.cosmo_arguments[key] += ' '+value+' '
            else:
                if array_flag is False:
                    if float(data.cosmo_arguments[key]) < value:
                        data.cosmo_arguments[key] = value
                else:
                    data.cosmo_arguments[key] = '%.2g' % value[0]
                    for i in range(1, len(value)):
                        data.cosmo_arguments[key] += ',%.2g' % (value[i])

    def read_contamination_spectra(self, data):

        for nuisance in self.use_nuisance:
            # read spectrum contamination (so far, assumes only temperature
            # contamination; will be trivial to generalize to polarization when
            # such templates will become relevant)
            setattr(self, "%s_contamination" % nuisance,
                    np.zeros(self.l_max+1, 'float64'))
            try:
                File = open(os.path.join(
                    self.data_directory, getattr(self, "%s_file" % nuisance)),
                    'r')
                for line in File:
                    l = int(float(line.split()[0]))
                    if ((l >= 2) and (l <= self.l_max)):
                        exec ("self.%s_contamination[l]=float(line.split()[1])/(l*(l+1.)/2./math.pi)" % nuisance)
            except:
                print ('Warning: you did not pass a file name containing ')
                print ('a contamination spectrum regulated by the nuisance ')
                print ('parameter ',nuisance)

            # read renormalization factor
            # if it is not there, assume it is one, i.e. do not renormalize
            try:
                # do the following operation:
                # self.nuisance_contamination *= float(self.nuisance_scale)
                setattr(self, "%s_contamination" % nuisance,
                        getattr(self, "%s_contamination" % nuisance) *
                        float(getattr(self, "%s_scale" % nuisance)))
            except AttributeError:
                pass

            # read central value of nuisance parameter
            # if it is not there, assume one by default
            try:
                getattr(self, "%s_prior_center" % nuisance)
            except AttributeError:
                setattr(self, "%s_prior_center" % nuisance, 1.)

            # read variance of nuisance parameter
            # if it is not there, assume flat prior (encoded through
            # variance=0)
            try:
                getattr(self, "%s_prior_variance" % nuisance)
            except:
                setattr(self, "%s_prior_variance" % nuisance, 0.)

    def add_contamination_spectra(self, cl, data):

        # Recover the current value of the nuisance parameter.
        for nuisance in self.use_nuisance:
            nuisance_value = float(
                data.mcmc_parameters[nuisance]['current'] *
                data.mcmc_parameters[nuisance]['scale'])

            # add contamination spectra multiplied by nuisance parameters
            for l in range(2, self.l_max):
                exec ("cl['tt'][l] += nuisance_value*self.%s_contamination[l]" % nuisance)

        return cl

    def computeLikelihood(self, ctx):
        """
        Interface with CosmoHammer

        Parameters
        ----------
        ctx : Context
                Contains several dictionaries storing data and cosmological
                information

        """
        # Recover both instances from the context
        cosmo = ctx.get("cosmo")
        data = ctx.get("data")

        loglkl = self.loglkl(cosmo, data)

        return loglkl

    #def compute_loglkl_MPLike():



###################################
#
# END OF GENERIC LIKELIHOOD CLASS
#
###################################



###################################
# PRIOR TYPE LIKELIHOOD
# --> H0,...
###################################
class Likelihood_prior(Likelihood):

    def loglkl(self):
        raise NotImplementedError('Must implement method loglkl() in your likelihood')


###################################
# NEWDAT TYPE LIKELIHOOD
# --> spt,boomerang,etc.
###################################
class Likelihood_newdat(Likelihood):

    def __init__(self, path, data, command_line):

        Likelihood.__init__(self, path, data, command_line)

        self.need_cosmo_arguments(
            data, {'lensing': 'yes', 'output': 'tCl lCl pCl'})

        # open .newdat file
        newdatfile = open(
            os.path.join(self.data_directory, self.file), 'r')

        # find beginning of window functions file names
        window_name = newdatfile.readline().strip('\n').replace(' ', '')

        # initialize list of fist and last band for each type
        band_num = np.zeros(6, 'int')
        band_min = np.zeros(6, 'int')
        band_max = np.zeros(6, 'int')

        # read number of bands for each of the six types TT, EE, BB, EB, TE, TB
        line = newdatfile.readline()
        for i in range(6):
            band_num[i] = int(line.split()[i])

        # read string equal to 'BAND_SELECTION' or not
        line = str(newdatfile.readline()).strip('\n').replace(' ', '')

        # if yes, read 6 lines containing 'min, max'
        if (line == 'BAND_SELECTION'):
            for i in range(6):
                line = newdatfile.readline()
                band_min[i] = int(line.split()[0])
                band_max[i] = int(line.split()[1])

        # if no, set min to 1 and max to band_num (=use all bands)
        else:
            band_min = [1 for i in range(6)]
            band_max = band_num

        # read line defining calibration uncertainty
        # contains: flag (=0 or 1), calib, calib_uncertainty
        line = newdatfile.readline()
        calib = float(line.split()[1])
        if (int(line.split()[0]) == 0):
            self.calib_uncertainty = 0
        else:
            self.calib_uncertainty = float(line.split()[2])

        # read line defining beam uncertainty
        # contains: flag (=0, 1 or 2), beam_width, beam_sigma
        line = newdatfile.readline()
        beam_type = int(line.split()[0])
        if (beam_type > 0):
            self.has_beam_uncertainty = True
        else:
            self.has_beam_uncertainty = False
        beam_width = float(line.split()[1])
        beam_sigma = float(line.split()[2])

        # read flag (= 0, 1 or 2) for lognormal distributions and xfactors
        line = newdatfile.readline()
        likelihood_type = int(line.split()[0])
        if (likelihood_type > 0):
            self.has_xfactors = True
        else:
            self.has_xfactors = False

        # declare array of quantitites describing each point of measurement
        # size yet unknown, it will be found later and stored as
        # self.num_points
        self.obs = np.array([], 'float64')
        self.var = np.array([], 'float64')
        self.beam_error = np.array([], 'float64')
        self.has_xfactor = np.array([], 'bool')
        self.xfactor = np.array([], 'float64')

        # temporary array to know which bands are actually used
        used_index = np.array([], 'int')

        index = -1

        # scan the lines describing each point of measurement
        for cltype in range(6):
            if (int(band_num[cltype]) != 0):
                # read name (but do not use it)
                newdatfile.readline()
                for band in range(int(band_num[cltype])):
                    # read one line corresponding to one measurement
                    line = newdatfile.readline()
                    index += 1

                    # if we wish to actually use this measurement
                    if ((band >= band_min[cltype]-1) and
                            (band <= band_max[cltype]-1)):

                        used_index = np.append(used_index, index)

                        self.obs = np.append(
                            self.obs, float(line.split()[1])*calib**2)

                        self.var = np.append(
                            self.var,
                            (0.5*(float(line.split()[2]) +
                                  float(line.split()[3]))*calib**2)**2)

                        self.xfactor = np.append(
                            self.xfactor, float(line.split()[4])*calib**2)

                        if ((likelihood_type == 0) or
                                ((likelihood_type == 2) and
                                (int(line.split()[7]) == 0))):
                            self.has_xfactor = np.append(
                                self.has_xfactor, [False])
                        if ((likelihood_type == 1) or
                                ((likelihood_type == 2) and
                                (int(line.split()[7]) == 1))):
                            self.has_xfactor = np.append(
                                self.has_xfactor, [True])

                        if (beam_type == 0):
                            self.beam_error = np.append(self.beam_error, 0.)
                        if (beam_type == 1):
                            l_mid = float(line.split()[5]) +\
                                0.5*(float(line.split()[5]) +
                                     float(line.split()[6]))
                            self.beam_error = np.append(
                                self.beam_error,
                                abs(math.exp(
                                    -l_mid*(l_mid+1)*1.526e-8*2.*beam_sigma *
                                    beam_width)-1.))
                        if (beam_type == 2):
                            if (likelihood_type == 2):
                                self.beam_error = np.append(
                                    self.beam_error, float(line.split()[8]))
                            else:
                                self.beam_error = np.append(
                                    self.beam_error, float(line.split()[7]))

                # now, skip and unused part of the file (with sub-correlation
                # matrices)
                for band in range(int(band_num[cltype])):
                    newdatfile.readline()

        # number of points that we will actually use
        self.num_points = np.shape(self.obs)[0]

        # total number of points, including unused ones
        full_num_points = index+1

        # read full correlation matrix
        full_covmat = np.zeros((full_num_points, full_num_points), 'float64')
        for point in range(full_num_points):
            full_covmat[point] = newdatfile.readline().split()

        # extract smaller correlation matrix for points actually used
        covmat = np.zeros((self.num_points, self.num_points), 'float64')
        for point in range(self.num_points):
            covmat[point] = full_covmat[used_index[point], used_index]

        # recalibrate this correlation matrix
        covmat *= calib**4

        # redefine the correlation matrix, the observed points and their
        # variance in case of lognormal likelihood
        if (self.has_xfactors):

            for i in range(self.num_points):

                for j in range(self.num_points):
                    if (self.has_xfactor[i]):
                        covmat[i, j] /= (self.obs[i]+self.xfactor[i])
                    if (self.has_xfactor[j]):
                        covmat[i, j] /= (self.obs[j]+self.xfactor[j])

            for i in range(self.num_points):
                if (self.has_xfactor[i]):
                    self.var[i] /= (self.obs[i]+self.xfactor[i])**2
                    self.obs[i] = math.log(self.obs[i]+self.xfactor[i])

        # invert correlation matrix
        self.inv_covmat = np.linalg.inv(covmat)

        # read window function files a first time, only for finding the
        # smallest and largest l's for each point
        self.win_min = np.zeros(self.num_points, 'int')
        self.win_max = np.zeros(self.num_points, 'int')
        for point in range(self.num_points):
            for line in open(os.path.join(
                    self.data_directory, 'windows', window_name) +
                    str(used_index[point]+1), 'r'):
                if any([float(line.split()[i]) != 0.
                        for i in range(1, len(line.split()))]):
                    if (self.win_min[point] == 0):
                        self.win_min[point] = int(line.split()[0])
                    self.win_max[point] = int(line.split()[0])

        # infer from format of window function files whether we will use
        # polarisation spectra or not
        num_col = len(line.split())
        if (num_col == 2):
            self.has_pol = False
        else:
            if (num_col == 5):
                self.has_pol = True
            else:
                print(
                    "In likelihood %s. " % self.name +
                    "Window function files are understood if they contain " +
                    "2 columns (l TT), or 5 columns (l TT TE EE BB)." +
                    "In this case the number of columns is %d" % num_col)

        # define array of window functions
        self.window = np.zeros(
            (self.num_points, max(self.win_max)+1, num_col-1), 'float64')

        # go again through window function file, this time reading window
        # functions; that are distributed as: l TT (TE EE BB) where the last
        # columns contaim W_l/l, not W_l we mutiply by l in order to store the
        # actual W_l
        for point in range(self.num_points):
            for line in open(os.path.join(
                    self.data_directory, 'windows', window_name) +
                    str(used_index[point]+1), 'r'):
                l = int(line.split()[0])
                if (((self.has_pol is False) and (len(line.split()) != 2))
                        or ((self.has_pol is True) and
                            (len(line.split()) != 5))):
                    #raise io_mp.LikelihoodError(
                        print("In likelihood %s. " % self.name +
                        "for a given experiment, all window functions should" +
                        " have the same number of columns, 2 or 5. " +
                        "This is not the case here.")
                if ((l >= self.win_min[point]) and (l <= self.win_max[point])):
                    self.window[point, l, :] = [
                        float(line.split()[i])
                        for i in range(1, len(line.split()))]
                    self.window[point, l, :] *= l

        # eventually, initialise quantitites used in the marginalization over
        # nuisance parameters
        if ((self.has_xfactors) and
                ((self.calib_uncertainty > 1.e-4) or
                 (self.has_beam_uncertainty))):
            self.halfsteps = 5
            self.margeweights = np.zeros(2*self.halfsteps+1, 'float64')
            for i in range(-self.halfsteps, self.halfsteps+1):
                self.margeweights[i+self.halfsteps] = np.exp(
                    -(float(i)*3./float(self.halfsteps))**2/2)
            self.margenorm = sum(self.margeweights)

        # store maximum value of l needed by window functions
        self.l_max = max(self.win_max)

        # impose that the cosmological code computes Cl's up to maximum l
        # needed by the window function
        self.need_cosmo_arguments(data, {'l_max_scalars': self.l_max})

        # deal with nuisance parameters
        try:
            self.use_nuisance
            self.nuisance = self.use_nuisance
        except:
            self.use_nuisance = []
            self.nuisance = []
        self.read_contamination_spectra(data)

        # end of initialisation

    def loglkl(self, cosmo, data):
        # get Cl's from the cosmological code
        cl = self.get_cl(cosmo)

        # add contamination spectra multiplied by nuisance parameters
        cl = self.add_contamination_spectra(cl, data)

        # get likelihood
        lkl = self.compute_lkl(cl, cosmo, data)

        # add prior on nuisance parameters
        lkl = self.add_nuisance_prior(lkl, data)

        return lkl

    def compute_lkl(self, cl, cosmo, data):
        # checks that Cl's have been computed up to high enough l given window
        # function range. Normally this has been imposed before, so this test
        # could even be supressed.
        if (np.shape(cl['tt'])[0]-1 < self.l_max):
            #raise io_mp.LikelihoodError(
             print(
                "%s computed Cls till l=" % data.cosmological_module_name +
                "%d " % (np.shape(cl['tt'])[0]-1) +
                "while window functions need %d." % self.l_max)

        # compute theoretical bandpowers, store them in theo[points]
        theo = np.zeros(self.num_points, 'float64')

        for point in range(self.num_points):

            # find bandpowers B_l by convolving C_l's with [(l+1/2)/2pi W_l]
            for l in range(self.win_min[point], self.win_max[point]):

                theo[point] += cl['tt'][l]*self.window[point, l, 0] *\
                    (l+0.5)/2./math.pi

                if (self.has_pol):
                    theo[point] += (
                        cl['te'][l]*self.window[point, l, 1] +
                        cl['ee'][l]*self.window[point, l, 2] +
                        cl['bb'][l]*self.window[point, l, 3]) *\
                        (l+0.5)/2./math.pi

        # allocate array for differencve between observed and theoretical
        # bandpowers
        difference = np.zeros(self.num_points, 'float64')

        # depending on the presence of lognormal likelihood, calibration
        # uncertainty and beam uncertainity, use several methods for
        # marginalising over nuisance parameters:

        # first method: numerical integration over calibration uncertainty:
        if (self.has_xfactors and
                ((self.calib_uncertainty > 1.e-4) or
                 self.has_beam_uncertainty)):

            chisq_tmp = np.zeros(2*self.halfsteps+1, 'float64')
            chisqcalib = np.zeros(2*self.halfsteps+1, 'float64')
            beam_error = np.zeros(self.num_points, 'float64')

            # loop over various beam errors
            for ibeam in range(2*self.halfsteps+1):

                # beam error
                for point in range(self.num_points):
                    if (self.has_beam_uncertainty):
                        beam_error[point] = 1.+self.beam_error[point] *\
                            (ibeam-self.halfsteps)*3/float(self.halfsteps)
                    else:
                        beam_error[point] = 1.

                # loop over various calibraion errors
                for icalib in range(2*self.halfsteps+1):

                    # calibration error
                    calib_error = 1+self.calib_uncertainty*(
                        icalib-self.halfsteps)*3/float(self.halfsteps)

                    # compute difference between observed and theoretical
                    # points, after correcting the later for errors
                    for point in range(self.num_points):

                        # for lognormal likelihood, use log(B_l+X_l)
                        if (self.has_xfactor[point]):
                            difference[point] = self.obs[point] -\
                                math.log(
                                    theo[point]*beam_error[point] *
                                    calib_error+self.xfactor[point])
                        # otherwise use B_l
                        else:
                            difference[point] = self.obs[point] -\
                                theo[point]*beam_error[point]*calib_error

                    # find chisq with those corrections
                    # chisq_tmp[icalib] = np.dot(np.transpose(difference),
                    # np.dot(self.inv_covmat, difference))
                    chisq_tmp[icalib] = np.dot(
                        difference, np.dot(self.inv_covmat, difference))

                minchisq = min(chisq_tmp)

            # find chisq marginalized over calibration uncertainty (if any)
                tot = 0
                for icalib in range(2*self.halfsteps+1):
                    tot += self.margeweights[icalib]*math.exp(
                        max(-30., -(chisq_tmp[icalib]-minchisq)/2.))

                chisqcalib[ibeam] = -2*math.log(tot/self.margenorm)+minchisq

            # find chisq marginalized over beam uncertainty (if any)
            if (self.has_beam_uncertainty):

                minchisq = min(chisqcalib)

                tot = 0
                for ibeam in range(2*self.halfsteps+1):
                    tot += self.margeweights[ibeam]*math.exp(
                        max(-30., -(chisqcalib[ibeam]-minchisq)/2.))

                chisq = -2*math.log(tot/self.margenorm)+minchisq

            else:
                chisq = chisqcalib[0]

        # second method: marginalize over nuisance parameters (if any)
        # analytically
        else:

            # for lognormal likelihood, theo[point] should contain log(B_l+X_l)
            if (self.has_xfactors):
                for point in range(self.num_points):
                    if (self.has_xfactor[point]):
                        theo[point] = math.log(theo[point]+self.xfactor[point])

            # find vector of difference between observed and theoretical
            # bandpowers
            difference = self.obs-theo

            # find chisq
            chisq = np.dot(
                np.transpose(difference), np.dot(self.inv_covmat, difference))

            # correct eventually for effect of analytic marginalization over
            # nuisance parameters
            if ((self.calib_uncertainty > 1.e-4) or self.has_beam_uncertainty):

                denom = 1.
                tmpi = np.dot(self.inv_covmat, theo)
                chi2op = np.dot(np.transpose(difference), tmp)
                chi2pp = np.dot(np.transpose(theo), tmp)

                # TODO beam is not defined here !
                if (self.has_beam_uncertainty):
                    for points in range(self.num_points):
                        beam[point] = self.beam_error[point]*theo[point]
                    tmp = np.dot(self.inv_covmat, beam)
                    chi2dd = np.dot(np.transpose(beam), tmp)
                    chi2pd = np.dot(np.transpose(theo), tmp)
                    chi2od = np.dot(np.transpose(difference), tmp)

                if (self.calib_uncertainty > 1.e-4):
                    wpp = 1/(chi2pp+1/self.calib_uncertainty**2)
                    chisq = chisq-wpp*chi2op**2
                    denom = denom/wpp*self.calib_uncertainty**2
                else:
                    wpp = 0

                if (self.has_beam_uncertainty):
                    wdd = 1/(chi2dd-wpp*chi2pd**2+1)
                    chisq = chisq-wdd*(chi2od-wpp*chi2op*chi2pd)**2
                    denom = denom/wdd

                chisq += math.log(denom)

        # finally, return ln(L)=-chi2/2

        self.lkl = -0.5 * chisq
        return self.lkl


###################################
# CLIK TYPE LIKELIHOOD
# --> clik_fake_planck,clik_wmap,etc.
###################################
class Likelihood_clik(Likelihood):

    def __init__(self, path, data, command_line):

        Likelihood.__init__(self, path, data, command_line)
        self.need_cosmo_arguments(
            data, {'lensing': 'yes', 'output': 'tCl lCl pCl'})

        try:
            import clik
        except ImportError:
            #raise io_mp.MissingLibraryError(
            print(
                "You must first activate the binaries from the Clik " +
                "distribution. Please run : \n " +
                "]$ source /path/to/clik/bin/clik_profile.sh \n " +
                "and try again.")
        # for lensing, some routines change. Intializing a flag for easier
        # testing of this condition
        #if self.name == 'Planck_lensing':
        if 'lensing' in self.name and 'Planck' in self.name:
            self.lensing = True
        else:
            self.lensing = False

        try:
            if self.lensing:
                self.clik = clik.clik_lensing(self.path_clik)
                try:
                    self.l_max = max(self.clik.get_lmax())
                # following 2 lines for compatibility with lensing likelihoods of 2013 and before
                # (then, clik.get_lmax() just returns an integer for lensing likelihoods;
                # this behavior was for clik versions < 10)
                except:
                    self.l_max = self.clik.get_lmax()
            else:
                self.clik = clik.clik(self.path_clik)
                self.l_max = max(self.clik.get_lmax())
        except clik.lkl.CError:
            #raise io_mp.LikelihoodError(
            print(
                "The path to the .clik file for the likelihood "
                "%s was not found where indicated:\n%s\n"
                % (self.name,self.path_clik) +
                " Note that the default path to search for it is"
                " one directory above the path['clik'] field. You"
                " can change this behaviour in all the "
                "Planck_something.data, to reflect your local configuration, "
                "or alternatively, move your .clik files to this place.")
        except KeyError:
            #raise io_mp.LikelihoodError(
            print(
                "In the %s.data file, the field 'clik' of the " % self.name +
                "path dictionary is expected to be defined. Please make sure"
                " it is the case in you configuration file")

        self.need_cosmo_arguments(
            data, {'l_max_scalars': self.l_max})

        self.nuisance = list(self.clik.extra_parameter_names)

        # line added to deal with a bug in planck likelihood release: A_planck called A_Planck in plik_lite
        if (self.name == 'Planck_highl_lite') or (self.name == 'Planck_highl_TTTEEE_lite'):
            for i in range(len(self.nuisance)):
                if (self.nuisance[i] == 'A_Planck'):
                    self.nuisance[i] = 'A_planck'
            print( "In %s, MontePython corrected nuisance parameter name A_Planck to A_planck" % self.name)

        # testing if the nuisance parameters are defined. If there is at least
        # one non defined, raise an exception.
        exit_flag = False
        nuisance_parameter_names = data.get_mcmc_parameters(['nuisance'])
        for nuisance in self.nuisance:
            if nuisance not in nuisance_parameter_names:
                exit_flag = True
                print ('%20s\tmust be a fixed or varying nuisance parameter' % nuisance)

        if exit_flag:
            #raise io_mp.LikelihoodError(
            print(
                "The likelihood %s " % self.name +
                "expected some nuisance parameters that were not provided")

        # deal with nuisance parameters
        try:
            self.use_nuisance
        except:
            self.use_nuisance = []

        # Add in use_nuisance all the parameters that have non-flat prior
        for nuisance in self.nuisance:
            if hasattr(self, '%s_prior_center' % nuisance):
                self.use_nuisance.append(nuisance)

    def loglkl(self, cosmo, data):

        nuisance_parameter_names = data.get_mcmc_parameters(['nuisance'])

        # get Cl's from the cosmological code
        cl = self.get_cl(cosmo)

        # testing for lensing
        if self.lensing:
            try:
                length = len(self.clik.get_lmax())
                tot = np.zeros(
                    np.sum(self.clik.get_lmax()) + length +
                    len(self.clik.get_extra_parameter_names()))
            # following 3 lines for compatibility with lensing likelihoods of 2013 and before
            # (then, clik.get_lmax() just returns an integer for lensing likelihoods,
            # and the length is always 2 for cl['pp'], cl['tt'])
            except:
                length = 2
                tot = np.zeros(2*self.l_max+length + len(self.clik.get_extra_parameter_names()))
        else:
            length = len(self.clik.get_has_cl())
            tot = np.zeros(
                np.sum(self.clik.get_lmax()) + length +
                len(self.clik.get_extra_parameter_names()))

        # fill with Cl's
        index = 0
        if not self.lensing:
            for i in range(length):
                if (self.clik.get_lmax()[i] > -1):
                    for j in range(self.clik.get_lmax()[i]+1):
                        if (i == 0):
                            tot[index+j] = cl['tt'][j]
                        if (i == 1):
                            tot[index+j] = cl['ee'][j]
                        if (i == 2):
                            tot[index+j] = cl['bb'][j]
                        if (i == 3):
                            tot[index+j] = cl['te'][j]
                        if (i == 4):
                            tot[index+j] = 0 #cl['tb'][j] class does not compute tb
                        if (i == 5):
                            tot[index+j] = 0 #cl['eb'][j] class does not compute eb

                    index += self.clik.get_lmax()[i]+1

        else:
            try:
                for i in range(length):
                    if (self.clik.get_lmax()[i] > -1):
                        for j in range(self.clik.get_lmax()[i]+1):
                            if (i == 0):
                                tot[index+j] = cl['pp'][j]
                            if (i == 1):
                                tot[index+j] = cl['tt'][j]
                            if (i == 2):
                                tot[index+j] = cl['ee'][j]
                            if (i == 3):
                                tot[index+j] = cl['bb'][j]
                            if (i == 4):
                                tot[index+j] = cl['te'][j]
                            if (i == 5):
                                tot[index+j] = 0 #cl['tb'][j] class does not compute tb
                            if (i == 6):
                                tot[index+j] = 0 #cl['eb'][j] class does not compute eb

                        index += self.clik.get_lmax()[i]+1

            # following 8 lines for compatibility with lensing likelihoods of 2013 and before
            # (then, clik.get_lmax() just returns an integer for lensing likelihoods,
            # and the length is always 2 for cl['pp'], cl['tt'])
            except:
                for i in range(length):
                    for j in range(self.l_max):
                        if (i == 0):
                            tot[index+j] = cl['pp'][j]
                        if (i == 1):
                            tot[index+j] = cl['tt'][j]
                    index += self.l_max+1

        # fill with nuisance parameters
        for nuisance in self.clik.get_extra_parameter_names():

            # line added to deal with a bug in planck likelihood release: A_planck called A_Planck in plik_lite
            if (self.name == 'Planck_highl_lite') or (self.name == 'Planck_highl_TTTEEE_lite'):
                if nuisance == 'A_Planck':
                    nuisance = 'A_planck'

            if nuisance in nuisance_parameter_names:
                nuisance_value = data.mcmc_parameters[nuisance]['current'] *\
                    data.mcmc_parameters[nuisance]['scale']
            else:
                #raise io_mp.LikelihoodError(
                print(
                    "the likelihood needs a parameter %s. " % nuisance +
                    "You must pass it through the input file " +
                    "(as a free nuisance parameter or a fixed parameter)")
            #print "found one nuisance with name",nuisance
            tot[index] = nuisance_value
            index += 1

        # compute likelihood
        #print "lkl:",self.clik(tot)
        lkl = self.clik(tot)[0]

        # add prior on nuisance parameters
        lkl = self.add_nuisance_prior(lkl, data)

        return lkl


###################################
# MOCK CMB TYPE LIKELIHOOD
# --> mock planck, cmbpol, etc.
###################################
class Likelihood_mock_cmb(Likelihood):

    def __init__(self, path, data, command_line):

        Likelihood.__init__(self, path, data, command_line)

        self.need_cosmo_arguments(
            data, {'lensing': 'yes', 'output': 'tCl lCl pCl'})

        ################
        # Noise spectrum
        ################

        try:
            self.noise_from_file
        except:
            self.noise_from_file = False

        if self.noise_from_file:

            try:
                self.noise_file
            except:
                #raise io_mp.LikelihoodError("For reading noise from file, you must provide noise_file")
                print("For reading noise from file, you must provide noise_file")

            self.noise_T = np.zeros(self.l_max+1, 'float64')
            self.noise_P = np.zeros(self.l_max+1, 'float64')
            if self.LensingExtraction:
                self.Nldd = np.zeros(self.l_max+1, 'float64')

            if os.path.exists(os.path.join(self.data_directory, self.noise_file)):
                noise = open(os.path.join(
                    self.data_directory, self.noise_file), 'r')
                line = noise.readline()
                while line.find('#') != -1:
                    line = noise.readline()

                for l in range(self.l_min, self.l_max+1):
                    ll = int(float(line.split()[0]))
                    if l != ll:
                        # if l_min is larger than the first l in the noise file we can skip lines
                        # until we are at the correct l. Otherwise raise error
                        while l > ll:
                            try:
                                line = fid_file.readline()
                                ll = int(float(line.split()[0]))
                            except:
                                #raise io_mp.LikelihoodError("Mismatch between required values of l in the code and in the noise file")
                                print("Mismatch between required values of l in the code and in the noise file")
                        if l < ll:
                            #raise io_mp.LikelihoodError("Mismatch between required values of l in the code and in the noise file")
                            print("Mismatch between required values of l in the code and in the noise file")
                    # read noise for C_l in muK**2
                    self.noise_T[l] = float(line.split()[1])
                    self.noise_P[l] = float(line.split()[2])
                    if self.LensingExtraction:
                        try:
                            # read noise for C_l^dd = l(l+1) C_l^pp
                            self.Nldd[l] = float(line.split()[3])/(l*(l+1)/2./math.pi)
                        except:
                            #raise io_mp.LikelihoodError("For reading lensing noise from file, you must provide one more column")
                            print("For reading lensing noise from file, you must provide one more column")
                    line = noise.readline()
            else:
                #raise io_mp.LikelihoodError("Could not find file ",self.noise_file)
                print("Could not find file ",self.noise_file)


        else:
            # convert arcmin to radians
            self.theta_fwhm *= np.array([math.pi/60/180])
            self.sigma_T *= np.array([math.pi/60/180])
            self.sigma_P *= np.array([math.pi/60/180])

            # compute noise in muK**2
            self.noise_T = np.zeros(self.l_max+1, 'float64')
            self.noise_P = np.zeros(self.l_max+1, 'float64')

            for l in range(self.l_min, self.l_max+1):
                self.noise_T[l] = 0
                self.noise_P[l] = 0
                for channel in range(self.num_channels):
                    self.noise_T[l] += self.sigma_T[channel]**-2 *\
                                       math.exp(
                                           -l*(l+1)*self.theta_fwhm[channel]**2/8/math.log(2))
                    self.noise_P[l] += self.sigma_P[channel]**-2 *\
                                       math.exp(
                                           -l*(l+1)*self.theta_fwhm[channel]**2/8/math.log(2))
                self.noise_T[l] = 1/self.noise_T[l]
                self.noise_P[l] = 1/self.noise_P[l]


        # trick to remove any information from polarisation for l<30
        try:
            self.no_small_l_pol
        except:
            self.no_small_l_pol = False

        if self.no_small_l_pol:
            for l in range(self.l_min,30):
                # plug a noise level of 100 muK**2, equivalent to no detection at all of polarisation
                self.noise_P[l] = 100.

        # trick to remove any information from temperature above l_max_TT
        try:
            self.l_max_TT
        except:
            self.l_max_TT = False

        if self.l_max_TT:
            for l in range(self.l_max_TT+1,l_max+1):
                # plug a noise level of 100 muK**2, equivalent to no detection at all of temperature
                self.noise_T[l] = 100.

        # impose that the cosmological code computes Cl's up to maximum l
        # needed by the window function
        self.need_cosmo_arguments(data, {'l_max_scalars': self.l_max})

        # if you want to print the noise spectra:
        #test = open('noise_T_P','w')
        #for l in range(self.l_min, self.l_max+1):
        #    test.write('%d  %e  %e\n'%(l,self.noise_T[l],self.noise_P[l]))

        ###########################################################################
        # implementation of default settings for flags describing the likelihood: #
        ###########################################################################

        # - ignore B modes by default:
        try:
            self.Bmodes
        except:
            self.Bmodes = False
        # - do not use delensing by default:
        try:
            self.delensing
        except:
            self.delensing = False
        # - do not include lensing extraction by default:
        try:
            self.LensingExtraction
        except:
            self.LensingExtraction = False
        # - neglect TD correlation by default:
        try:
            self.neglect_TD
        except:
            self.neglect_TD = True
        # - use lthe lensed TT, TE, EE by default:
        try:
            self.unlensed_clTTTEEE
        except:
            self.unlensed_clTTTEEE = False
        # - do not exclude TTEE by default:
        try:
            self.ExcludeTTTEEE
            if self.ExcludeTTTEEE and not self.LensingExtraction:
                #raise io_mp.LikelihoodError("Mock CMB likelihoods where TTTEEE is not used have only been "
                print("Mock CMB likelihoods where TTTEEE is not used have only been "
                                            "implemented for the deflection spectrum (i.e. not for B-modes), "
                                            "but you do not seem to have lensing extraction enabled")
        except:
            self.ExcludeTTTEEE = False

        ##############################################
        # Delensing noise: implemented by  S. Clesse #
        ##############################################

        if self.delensing:

            try:
                self.delensing_file
            except:
                #raise io_mp.LikelihoodError("For delensing, you must provide delensing_file")
                print("For delensing, you must provide delensing_file")

            self.noise_delensing = np.zeros(self.l_max+1)
            if os.path.exists(os.path.join(self.data_directory, self.delensing_file)):
                delensing_file = open(os.path.join(
                    self.data_directory, self.delensing_file), 'r')
                line = delensing_file.readline()
                while line.find('#') != -1:
                    line = delensing_file.readline()

                for l in range(self.l_min, self.l_max+1):
                    ll = int(float(line.split()[0]))
                    if l != ll:
                        # if l_min is larger than the first l in the delensing file we can skip lines
                        # until we are at the correct l. Otherwise raise error
                        while l > ll:
                            try:
                                line = fid_file.readline()
                                ll = int(float(line.split()[0]))
                            except:
                                #raise io_mp.LikelihoodError("Mismatch between required values of l in the code and in the delensing file")
                                print("Mismatch between required values of l in the code and in the delensing file")
                        if l < ll:
                            #raise io_mp.LikelihoodError("Mismatch between required values of l in the code and in the delensing file")
                            print("Mismatch between required values of l in the code and in the delensing file")
                    self.noise_delensing[ll] = float(line.split()[2])/(ll*(ll+1)/2./math.pi)
                    # change 3 to 4 in the above line for CMBxCIB delensing
                    line = delensing_file.readline()

            else:
                #raise io_mp.LikelihoodError("Could not find file ",self.delensing_file)
                print("Could not find file ",self.delensing_file)

        ###############################################################
        # Read data for TT, EE, TE, [eventually BB or phi-phi, phi-T] #
        ###############################################################

        # default:
        if not self.ExcludeTTTEEE:
            numCls = 3
        # default 0 if excluding TT EE
        else:
            numCls = 0

        # deal with BB:
        if self.Bmodes:
            self.index_B = numCls
            numCls += 1

        # deal with pp, pT (p = CMB lensing potential):
        if self.LensingExtraction:
            self.index_pp = numCls
            numCls += 1
            if not self.ExcludeTTTEEE:
                self.index_tp = numCls
                numCls += 1

            if not self.noise_from_file:
                # provide a file containing NlDD (noise for the extracted
                # deflection field spectrum) This option is temporary
                # because at some point this module will compute NlDD
                # itself, when logging the fiducial model spectrum.
                try:
                    self.temporary_Nldd_file
                except:
                    #raise io_mp.LikelihoodError("For lensing extraction, you must provide a temporary_Nldd_file")
                    print("For lensing extraction, you must provide a temporary_Nldd_file")

                # read the NlDD file
                self.Nldd = np.zeros(self.l_max+1, 'float64')

                if os.path.exists(os.path.join(self.data_directory, self.temporary_Nldd_file)):
                    fid_file = open(os.path.join(self.data_directory, self.temporary_Nldd_file), 'r')
                    line = fid_file.readline()
                    while line.find('#') != -1:
                        line = fid_file.readline()
                    while (line.find('\n') != -1 and len(line) == 1):
                        line = fid_file.readline()
                    for l in range(self.l_min, self.l_max+1):
                        ll = int(float(line.split()[0]))
                        if l != ll:
                            # if l_min is larger than the first l in the delensing file we can skip lines
                            # until we are at the correct l. Otherwise raise error
                            while l > ll:
                                try:
                                    line = fid_file.readline()
                                    ll = int(float(line.split()[0]))
                                except:
                                    #raise io_mp.LikelihoodError("Mismatch between required values of l in the code and in the delensing file")
                                    print("Mismatch between required values of l in the code and in the delensing file")
                            if l < ll:
                                #raise io_mp.LikelihoodError("Mismatch between required values of l in the code and in the delensing file")
                                print("Mismatch between required values of l in the code and in the delensing file")
                        # this lines assumes that Nldd is stored in the
                        # 4th column (can be customised)
                        self.Nldd[ll] = float(line.split()[3])/(l*(l+1.)/2./math.pi)
                        line = fid_file.readline()
                else:
                    #raise io_mp.LikelihoodError("Could not find file ",self.temporary_Nldd_file)
                    print("Could not find file ",self.temporary_Nldd_file)

        # deal with fiducial model:
        # If the file exists, initialize the fiducial values
        self.Cl_fid = np.zeros((numCls, self.l_max+1), 'float64')
        self.fid_values_exist = False
        if os.path.exists(os.path.join(
                self.data_directory, self.fiducial_file)):
            self.fid_values_exist = True
            fid_file = open(os.path.join(
                self.data_directory, self.fiducial_file), 'r')
            line = fid_file.readline()
            while line.find('#') != -1:
                line = fid_file.readline()
            while (line.find('\n') != -1 and len(line) == 1):
                line = fid_file.readline()
            for l in range(self.l_min, self.l_max+1):
                ll = int(line.split()[0])
                if not self.ExcludeTTTEEE:
                    self.Cl_fid[0, ll] = float(line.split()[1])
                    self.Cl_fid[1, ll] = float(line.split()[2])
                    self.Cl_fid[2, ll] = float(line.split()[3])
                # read BB:
                if self.Bmodes:
                    try:
                        self.Cl_fid[self.index_B, ll] = float(line.split()[self.index_B+1])
                    except:
                        #raise io_mp.LikelihoodError(
                        print(
                            "The fiducial model does not have enough columns.")
                # read DD, TD (D = deflection field):
                if self.LensingExtraction:
                    try:
                        self.Cl_fid[self.index_pp, ll] = float(line.split()[self.index_pp+1])
                        if not self.ExcludeTTTEEE:
                            self.Cl_fid[self.index_tp, ll] = float(line.split()[self.index_tp+1])
                    except:
                        #raise io_mp.LikelihoodError(
                        print(
                            "The fiducial model does not have enough columns.")

                line = fid_file.readline()

        # Else the file will be created in the loglkl() function.

        # Explicitly display the flags to be sure that likelihood does what you expect:
        print ("Initialised likelihood_mock_cmb with following options:")
        if self.unlensed_clTTTEEE:
            print ("  unlensed_clTTTEEE is True")
        else:
            print ("  unlensed_clTTTEEE is False")
        if self.Bmodes:
            print( "  Bmodes is True")
        else:
            print ("  Bmodes is False")
        if self.delensing:
            print( "  delensing is True")
        else:
            print ("  delensing is False")
        if self.LensingExtraction:
            print ("  LensingExtraction is True")
        else:
            print ("  LensingExtraction is False")
        if self.neglect_TD:
            print ("  neglect_TD is True")
        else:
            print ("  neglect_TD is False")
        if self.ExcludeTTTEEE:
            print ("  ExcludeTTTEEE is True")
        else:
            print ("  ExcludeTTTEEE is False")
        print ("")

        # end of initialisation
        return

    def loglkl(self, cosmo, data):

        # get Cl's from the cosmological code (returned in muK**2 units)

        # if we want unlensed Cl's
        if self.unlensed_clTTTEEE:
            cl = self.get_unlensed_cl(cosmo)
            # exception: for non-delensed B modes we need the lensed BB spectrum
            # (this case is usually not useful/relevant)
            if self.Bmodes and (not self.delensing):
                    cl_lensed = self.get_cl(cosmo)
                    for l in range(self.lmax+1):
                        cl[l]['bb']=cl_lensed[l]['bb']

        # if we want lensed Cl's
        else:
            cl = self.get_cl(cosmo)
            # exception: for delensed B modes we need the unlensed spectrum
            if self.Bmodes and self.delensing:
                cl_unlensed = self.get_unlensed_cl(cosmo)
                for l in range(self.lmax+1):
                        cl[l]['bb']=cl_unlensed[l]['bb']

        # get likelihood
        lkl = self.compute_lkl(cl, cosmo, data)

        return lkl

    def compute_lkl(self, cl, cosmo, data):

        # Write fiducial model spectra if needed (return an imaginary number in
        # that case)
        if self.fid_values_exist is False:
            # Store the values now.
            fid_file = open(os.path.join(
                self.data_directory, self.fiducial_file), 'w')
            fid_file.write('# Fiducial parameters')
            for key, value in data.mcmc_parameters.iteritems():
                fid_file.write(', %s = %.5g' % (
                    key, value['current']*value['scale']))
            fid_file.write('\n')
            for l in range(self.l_min, self.l_max+1):
                fid_file.write("%5d  " % l)
                if not self.ExcludeTTTEEE:
                    fid_file.write("%.8g  " % (cl['tt'][l]+self.noise_T[l]))
                    fid_file.write("%.8g  " % (cl['ee'][l]+self.noise_P[l]))
                    fid_file.write("%.8g  " % cl['te'][l])
                if self.Bmodes:
                    # next three lines added by S. Clesse for delensing
                    if self.delensing:
                        fid_file.write("%.8g  " % (cl['bb'][l]+self.noise_P[l]+self.noise_delensing[l]))
                    else:
                        fid_file.write("%.8g  " % (cl['bb'][l]+self.noise_P[l]))
                if self.LensingExtraction:
                    # we want to store clDD = l(l+1) clpp
                    # and ClTD = sqrt(l(l+1)) Cltp
                    fid_file.write("%.8g  " % (l*(l+1.)*cl['pp'][l] + self.Nldd[l]))
                    if not self.ExcludeTTTEEE:
                        fid_file.write("%.8g  " % (math.sqrt(l*(l+1.))*cl['tp'][l]))
                fid_file.write("\n")
            print( '\n')
            warnings.warn(
                "Writing fiducial model in %s, for %s likelihood\n" % (
                    self.data_directory+'/'+self.fiducial_file, self.name))
            return 1j

        # compute likelihood

        chi2 = 0

        # count number of modes.
        # number of modes is different form number of spectra
        # modes = T,E,[B],[D=deflection]
        # spectra = TT,EE,TE,[BB],[DD,TD]
        # default:
        if not self.ExcludeTTTEEE:
            num_modes=2
        # default 0 if excluding TT EE
        else:
            num_modes=0
        # add B mode:
        if self.Bmodes:
            num_modes += 1
        # add D mode:
        if self.LensingExtraction:
            num_modes += 1

        Cov_obs = np.zeros((num_modes, num_modes), 'float64')
        Cov_the = np.zeros((num_modes, num_modes), 'float64')
        Cov_mix = np.zeros((num_modes, num_modes), 'float64')

        for l in range(self.l_min, self.l_max+1):

            if self.Bmodes and self.LensingExtraction:
                #raise io_mp.LikelihoodError("We have implemented a version of the likelihood with B modes, a version with lensing extraction, but not yet a version with both at the same time. You can implement it.")
                print("We have implemented a version of the likelihood with B modes, a version with lensing extraction, but not yet a version with both at the same time. You can implement it.")

            # case with B modes:
            elif self.Bmodes:
                Cov_obs = np.array([
                    [self.Cl_fid[0, l], self.Cl_fid[2, l], 0],
                    [self.Cl_fid[2, l], self.Cl_fid[1, l], 0],
                    [0, 0, self.Cl_fid[3, l]]])
                # next 5 lines added by S. Clesse for delensing
                if self.delensing:
                    Cov_the = np.array([
                        [cl['tt'][l]+self.noise_T[l], cl['te'][l], 0],
                        [cl['te'][l], cl['ee'][l]+self.noise_P[l], 0],
                        [0, 0, cl['bb'][l]+self.noise_P[l]+self.noise_delensing[l]]])
                else:
                    Cov_the = np.array([
                        [cl['tt'][l]+self.noise_T[l], cl['te'][l], 0],
                        [cl['te'][l], cl['ee'][l]+self.noise_P[l], 0],
                        [0, 0, cl['bb'][l]+self.noise_P[l]]])

            # case with lensing
            # note that the likelihood is based on ClDD (deflection spectrum)
            # rather than Clpp (lensing potential spectrum)
            # But the Bolztmann code input is Clpp
            # So we make the conversion using ClDD = l*(l+1.)*Clpp
            # So we make the conversion using ClTD = sqrt(l*(l+1.))*Cltp

            # just DD, i.e. no TT or EE.
            elif self.LensingExtraction and self.ExcludeTTTEEE:
                cldd_fid = self.Cl_fid[self.index_pp, l]
                cldd = l*(l+1.)*cl['pp'][l]
                Cov_obs = np.array([[cldd_fid]])
                Cov_the = np.array([[cldd+self.Nldd[l]]])

            # Usual TTTEEE plus DD and TD
            elif self.LensingExtraction:
                cldd_fid = self.Cl_fid[self.index_pp, l]
                cldd = l*(l+1.)*cl['pp'][l]
                if self.neglect_TD:
                    cltd_fid = 0.
                    cltd = 0.
                else:
                    cltd_fid = self.Cl_fid[self.index_tp, l]
                    cltd = math.sqrt(l*(l+1.))*cl['tp'][l]

                Cov_obs = np.array([
                    [self.Cl_fid[0, l], self.Cl_fid[2, l], 0.*self.Cl_fid[self.index_tp, l]],
                    [self.Cl_fid[2, l], self.Cl_fid[1, l], 0],
                    [cltd_fid, 0, cldd_fid]])
                Cov_the = np.array([
                    [cl['tt'][l]+self.noise_T[l], cl['te'][l], 0.*math.sqrt(l*(l+1.))*cl['tp'][l]],
                    [cl['te'][l], cl['ee'][l]+self.noise_P[l], 0],
                    [cltd, 0, cldd+self.Nldd[l]]])

            # case without B modes nor lensing:
            else:
                Cov_obs = np.array([
                    [self.Cl_fid[0, l], self.Cl_fid[2, l]],
                    [self.Cl_fid[2, l], self.Cl_fid[1, l]]])
                Cov_the = np.array([
                    [cl['tt'][l]+self.noise_T[l], cl['te'][l]],
                    [cl['te'][l], cl['ee'][l]+self.noise_P[l]]])

            # get determinant of observational and theoretical covariance matrices
            det_obs = np.linalg.det(Cov_obs)
            det_the = np.linalg.det(Cov_the)

            # get determinant of mixed matrix (= sum of N theoretical
            # matrices with, in each of them, the nth column replaced
            # by that of the observational matrix)
            det_mix = 0.
            for i in range(num_modes):
                Cov_mix = np.copy(Cov_the)
                Cov_mix[:, i] = Cov_obs[:, i]
                det_mix += np.linalg.det(Cov_mix)

            chi2 += (2.*l+1.)*self.f_sky *\
                (det_mix/det_the + math.log(det_the/det_obs) - num_modes)

        return -chi2/2


###################################
# MPK TYPE LIKELIHOOD
# --> sdss, wigglez, etc.
###################################
class Likelihood_mpk(Likelihood):

    def __init__(self, path, data, command_line, common=False, common_dict={}):

        Likelihood.__init__(self, path, data, command_line)

        # require P(k) from class
        self.need_cosmo_arguments(data, {'output': 'mPk'})

        if common:
            self.add_common_knowledge(common_dict)

        try:
            self.use_halofit
        except:
            self.use_halofit = False

        if self.use_halofit:
            self.need_cosmo_arguments(data, {'non linear': 'halofit'})

        # sdssDR7 by T. Brinckmann
        # Based on Reid et al. 2010 arXiv:0907.1659 - Note: arXiv version not updated
        try:
            self.use_sdssDR7
        except:
            self.use_sdssDR7 = False

        # read values of k (in h/Mpc)
        self.k_size = self.max_mpk_kbands_use-self.min_mpk_kbands_use+1
        self.mu_size = 1
        self.k = np.zeros((self.k_size), 'float64')
        self.kh = np.zeros((self.k_size), 'float64')

        # (JR) this reading in works in Gambit
        datafile = open(os.path.join(self.data_directory, self.kbands_file), 'r')
        for i in range(self.num_mpk_kbands_full):
            line = datafile.readline()
            while line.find('#') != -1:
                line = datafile.readline()
            if i+2 > self.min_mpk_kbands_use and i < self.max_mpk_kbands_use:
                self.kh[i-self.min_mpk_kbands_use+1] = float(line.split()[0])
        datafile.close()

        khmax = self.kh[-1]

        # check if need hight value of k for giggleZ
        try:
            self.use_giggleZ
        except:
            self.use_giggleZ = False

        # Try a new model, with an additional nuisance parameter. Note
        # that the flag use_giggleZPP0 being True requires use_giggleZ
        # to be True as well. Note also that it is defined globally,
        # and not for every redshift bin.
        if self.use_giggleZ:
            try:
                self.use_giggleZPP0
            except:
                self.use_giggleZPP0 = False
        else:
            self.use_giggleZPP0 = False

        # If the flag use_giggleZPP0 is set to True, the nuisance parameters
        # P0_a, P0_b, P0_c and P0_d are expected.
        if self.use_giggleZPP0:
            if 'P0_a' not in data.get_mcmc_parameters(['nuisance']):
                #raise io_mp.LikelihoodError(
                print(
                    "In likelihood %s. " % self.name +
                    "P0_a is not defined in the .param file, whereas this " +
                    "nuisance parameter is required when the flag " +
                    "'use_giggleZPP0' is set to true for WiggleZ")

        if self.use_giggleZ:
            datafile = open(os.path.join(self.data_directory,self.giggleZ_fidpk_file), 'r')

            line = datafile.readline()
            k = float(line.split()[0])
            line_number = 1
            while (k < self.kh[0]):
                line = datafile.readline()
                k = float(line.split()[0])
                line_number += 1
            ifid_discard = line_number-2
            while (k < khmax):
                line = datafile.readline()
                k = float(line.split()[0])
                line_number += 1
            datafile.close()
            self.k_fid_size = line_number-ifid_discard+1
            khmax = k

        if self.use_halofit:
            khmax *= 2

        # require k_max and z_max from the cosmological module
        if self.use_sdssDR7:
            self.need_cosmo_arguments(data, {'z_max_pk': self.zmax})
            self.need_cosmo_arguments(data, {'P_k_max_h/Mpc': 7.5*self.kmax})
        else:
            self.need_cosmo_arguments(
                data, {'P_k_max_h/Mpc': khmax, 'z_max_pk': self.redshift})

        # read information on different regions in the sky
        try:
            self.has_regions
        except:
            self.has_regions = False

        if (self.has_regions):
            self.num_regions = len(self.used_region)
            self.num_regions_used = 0
            for i in range(self.num_regions):
                if (self.used_region[i]):
                    self.num_regions_used += 1
            if (self.num_regions_used == 0):
                #raise io_mp.LikelihoodError(
                print(
                    "In likelihood %s. " % self.name +
                    "Mpk: no regions begin used in this data set")
        else:
            self.num_regions = 1
            self.num_regions_used = 1
            self.used_region = [True]

        # read window functions
        self.n_size = self.max_mpk_points_use-self.min_mpk_points_use+1

        self.window = np.zeros(
            (self.num_regions, self.n_size, self.k_size), 'float64')


        # (JR) this reading in works in GAMBIT
        datafile = open(os.path.join(self.data_directory, self.windows_file), 'r')
        for i_region in range(self.num_regions):
            for i in range(self.num_mpk_points_full):
                line = datafile.readline()
                while line.find('#') != -1:
                    line = datafile.readline()
                if (i+2 > self.min_mpk_points_use and i < self.max_mpk_points_use):
                    for j in range(self.k_size):
                        self.window[i_region, i-self.min_mpk_points_use+1, j] = float(line.split()[j+self.min_mpk_kbands_use-1])
        datafile.close()

        # read measurements
        self.P_obs = np.zeros((self.num_regions, self.n_size), 'float64')
        self.P_err = np.zeros((self.num_regions, self.n_size), 'float64')


        # (JR) this reading in works in GAMBIT
        datafile = open(os.path.join(self.data_directory, self.measurements_file), 'r')
        for i_region in range(self.num_regions):
            for i in range(self.num_mpk_points_full):
                line = datafile.readline()
                while line.find('#') != -1:
                    line = datafile.readline()
                if (i+2 > self.min_mpk_points_use and
                    i < self.max_mpk_points_use):
                    self.P_obs[i_region, i-self.min_mpk_points_use+1] = float(line.split()[3])
                    self.P_err[i_region, i-self.min_mpk_points_use+1] = float(line.split()[4])
        datafile.close()

        # read covariance matrices
        try:
            self.covmat_file
            self.use_covmat = True
        except:
            self.use_covmat = False

        try:
            self.use_invcov
        except:
            self.use_invcov = False

        self.invcov = np.zeros(
            (self.num_regions, self.n_size, self.n_size), 'float64')

        if self.use_covmat:
            cov = np.zeros((self.n_size, self.n_size), 'float64')
            invcov_tmp = np.zeros((self.n_size, self.n_size), 'float64')

            datafile = open(os.path.join(self.data_directory, self.covmat_file), 'r')
            for i_region in range(self.num_regions):
                for i in range(self.num_mpk_points_full):
                    line = datafile.readline()
                    while line.find('#') != -1:
                        line = datafile.readline()
                    if (i+2 > self.min_mpk_points_use and i < self.max_mpk_points_use):
                        for j in range(self.num_mpk_points_full):
                            if (j+2 > self.min_mpk_points_use and j < self.max_mpk_points_use):
                                cov[i-self.min_mpk_points_use+1,j-self.min_mpk_points_use+1] = float(line.split()[j])

                if self.use_invcov:
                    invcov_tmp = cov
                else:
                    invcov_tmp = np.linalg.inv(cov)
                for i in range(self.n_size):
                    for j in range(self.n_size):
                        self.invcov[i_region, i, j] = invcov_tmp[i, j]
            datafile.close()
        else:
            for i_region in range(self.num_regions):
                for j in range(self.n_size):
                    self.invcov[i_region, j, j] = \
                        1./(self.P_err[i_region, j]**2)

        # read fiducial model
        if self.use_giggleZ:
            self.P_fid = np.zeros((self.k_fid_size), 'float64')
            self.k_fid = np.zeros((self.k_fid_size), 'float64')
            datafile = open(os.path.join(self.data_directory,self.giggleZ_fidpk_file), 'r')
            for i in range(ifid_discard):
                line = datafile.readline()
            for i in range(self.k_fid_size):
                line = datafile.readline()
                self.k_fid[i] = float(line.split()[0])
                self.P_fid[i] = float(line.split()[1])
            datafile.close()

        # read integral constraint
        if self.use_sdssDR7:
            self.zerowindowfxn = np.zeros((self.k_size), 'float64')
            datafile = open(os.path.join(self.data_directory,self.zerowindowfxn_file), 'r')
            for i in range(self.k_size):
                line = datafile.readline()
                self.zerowindowfxn[i] = float(line.split()[0])
            datafile.close()
            self.zerowindowfxnsubtractdat = np.zeros((self.n_size), 'float64')
            datafile = open(os.path.join(self.data_directory,self.zerowindowfxnsubtractdat_file), 'r')
            line = datafile.readline()
            self.zerowindowfxnsubtractdatnorm = float(line.split()[0])
            for i in range(self.n_size):
                line = datafile.readline()
            self.zerowindowfxnsubtractdat[i] = float(line.split()[0])
            datafile.close()

        # initialize array of values for the nuisance parameters a1,a2
        if self.use_sdssDR7:
            nptsa1=self.nptsa1
            nptsa2=self.nptsa2
            a1maxval=self.a1maxval
            self.a1list=np.zeros(self.nptstot)
            self.a2list=np.zeros(self.nptstot)
            da1 = a1maxval/(nptsa1/2)
            da2 = self.a2maxpos(-a1maxval) / (nptsa2/2)
            count=0
            for i in range(-nptsa1/2, nptsa1/2+1):
                for j in range(-nptsa2/2, nptsa2/2+1):
                    a1val = da1*i
                    a2val = da2*j
                    if ((a2val >= 0.0 and a2val <= self.a2maxpos(a1val) and a2val >= self.a2minfinalpos(a1val)) or \
                        (a2val <= 0.0 and a2val <= self.a2maxfinalneg(a1val) and a2val >= self.a2minneg(a1val))):
                        if (self.testa1a2(a1val,a2val) == False):
                            #raise io_mp.LikelihoodError(
                            print(
                                'Error in likelihood %s ' % (self.name) +
                                'Nuisance parameter values not valid: %s %s' % (a1,a2) )
                        if(count >= self.nptstot):
                            #raise io_mp.LikelihoodError(
                            print(
                                'Error in likelihood %s ' % (self.name) +
                                'count > nptstot failure' )
                        self.a1list[count]=a1val
                        self.a2list[count]=a2val
                        count=count+1

        return

    # functions added for nuisance parameter space checks.
    def a2maxpos(self,a1val):
        a2max = -1.0
        if (a1val <= min(self.s1/self.k1,self.s2/self.k2)):
            a2max = min(self.s1/self.k1**2 - a1val/self.k1, self.s2/self.k2**2 - a1val/self.k2)
        return a2max

    def a2min1pos(self,a1val):
        a2min1 = 0.0
        if(a1val <= 0.0):
            a2min1 = max(-self.s1/self.k1**2 - a1val/self.k1, -self.s2/self.k2**2 - a1val/self.k2, 0.0)
        return a2min1

    def a2min2pos(self,a1val):
        a2min2 = 0.0
        if(abs(a1val) >= 2.0*self.s1/self.k1 and a1val <= 0.0):
            a2min2 = a1val**2/self.s1*0.25
        return a2min2

    def a2min3pos(self,a1val):
        a2min3 = 0.0
        if(abs(a1val) >= 2.0*self.s2/self.k2 and a1val <= 0.0):
            a2min3 = a1val**2/self.s2*0.25
        return a2min3

    def a2minfinalpos(self,a1val):
        a2minpos = max(self.a2min1pos(a1val),self.a2min2pos(a1val),self.a2min3pos(a1val))
        return a2minpos

    def a2minneg(self,a1val):
        if (a1val >= max(-self.s1/self.k1,-self.s2/self.k2)):
            a2min = max(-self.s1/self.k1**2 - a1val/self.k1, -self.s2/self.k2**2 - a1val/self.k2)
        else:
            a2min = 1.0
        return a2min

    def a2max1neg(self,a1val):
        if(a1val >= 0.0):
            a2max1 = min(self.s1/self.k1**2 - a1val/self.k1, self.s2/self.k2**2 - a1val/self.k2, 0.0)
        else:
            a2max1 = 0.0
        return a2max1

    def a2max2neg(self,a1val):
        a2max2 = 0.0
        if(abs(a1val) >= 2.0*self.s1/self.k1 and a1val >= 0.0):
            a2max2 = -a1val**2/self.s1*0.25
        return a2max2

    def a2max3neg(self,a1val):
        a2max3 = 0.0
        if(abs(a1val) >= 2.0*self.s2/self.k2 and a1val >= 0.0):
            a2max3 = -a1val**2/self.s2*0.25
        return a2max3

    def a2maxfinalneg(self,a1val):
        a2maxneg = min(self.a2max1neg(a1val),self.a2max2neg(a1val),self.a2max3neg(a1val))
        return a2maxneg

    def testa1a2(self,a1val, a2val):
        testresult = True
        # check if there's an extremum; either a1val or a2val has to be negative, not both
        if (a2val==0.):
             return testresult #not in the original code, but since a2val=0 returns True this way I avoid zerodivisionerror
        kext = -a1val/2.0/a2val
        diffval = abs(a1val*kext + a2val*kext**2)
        if(kext > 0.0 and kext <= self.k1 and diffval > self.s1):
            testresult = False
        if(kext > 0.0 and kext <= self.k2 and diffval > self.s2):
            testresult = False
        if (abs(a1val*self.k1 + a2val*self.k1**2) > self.s1):
            testresult = False
        if (abs(a1val*self.k2 + a2val*self.k2**2) > self.s2):
            testresult = False
        return testresult


    def add_common_knowledge(self, common_dictionary):
        """
        Add to a class the content of a shared dictionary of attributes

        The purpose of this method is to set some attributes globally for a Pk
        likelihood, that are shared amongst all the redshift bins (in
        WiggleZ.data for instance, a few flags and numbers are defined that
        will be transfered to wigglez_a, b, c and d

        """
        for key, value in common_dictionary.iteritems():
            # First, check if the parameter exists already
            try:
                exec("self.%s" % key)
                warnings.warn(
                    "parameter %s from likelihood %s will be replaced by " +
                    "the common knowledge routine" % (key, self.name))
            except:
                # (JR) had to adopt these check to work properly with ascii & unicode strings
                #   original line was -> 'if type(value) != type('foo')' 
                #   which crashed if one of the strings was unicode formated
                if ((not isinstance(value, str)) and (not isinstance(value,unicode))):
                    exec("self.%s = %s" % (key, value))
                else:
                    exec("self.%s = '%s'" % (key, value))

    # compute likelihood
    def loglkl(self, cosmo, data):

        # reduced Hubble parameter
        h = cosmo.h()

        # WiggleZ and sdssDR7 specific
        if self.use_scaling:
            # angular diameter distance at this redshift, in Mpc
            d_angular = cosmo.angular_distance(self.redshift)

            # radial distance at this redshift, in Mpc, is simply 1/H (itself
            # in Mpc^-1). Hz is an array, with only one element.
            r, Hz = cosmo.z_of_r([self.redshift])
            d_radial = 1/Hz[0]

            # scaling factor = (d_angular**2 * d_radial)^(1/3) for the
            # fiducial cosmology used in the data files of the observations
            # divided by the same quantity for the cosmology we are comparing with.
            # The fiducial values are stored in the .data files for
            # each experiment, and are truly in Mpc. Beware for a potential
            # difference with CAMB conventions here.
            scaling = pow(
                (self.d_angular_fid/d_angular)**2 *
                (self.d_radial_fid/d_radial), 1./3.)
        else:
            scaling = 1
        # get rescaled values of k in 1/Mpc
        self.k = self.kh*h*scaling

        # get P(k) at right values of k, convert it to (Mpc/h)^3 and rescale it
        P_lin = np.zeros((self.k_size), 'float64')

        # If the flag use_giggleZ is set to True, the power spectrum retrieved
        # from Class will get rescaled by the fiducial power spectrum given by
        # the GiggleZ N-body simulations CITE
        if self.use_giggleZ:
            P = np.zeros((self.k_fid_size), 'float64')
            for i in range(self.k_fid_size):
                P[i] = cosmo.pk(self.k_fid[i]*h, self.redshift)
                power = 0
                # The following create a polynome in k, which coefficients are
                # stored in the .data files of the experiments.
                for j in range(6):
                    power += self.giggleZ_fidpoly[j]*self.k_fid[i]**j
                # rescale P by fiducial model and get it in (Mpc/h)**3
                P[i] *= pow(10, power)*(h/scaling)**3/self.P_fid[i]

            if self.use_giggleZPP0:
                # Shot noise parameter addition to GiggleZ model. It should
                # recover the proper nuisance parameter, depending on the name.
                # I.e., Wigglez_A should recover P0_a, etc...
                tag = self.name[-2:]  # circle over "_a", "_b", etc...
                P0_value = data.mcmc_parameters['P0'+tag]['current'] *\
                    data.mcmc_parameters['P0'+tag]['scale']
                P_lin = np.interp(self.kh,self.k_fid,P+P0_value)
            else:
                # get P_lin by interpolation. It is still in (Mpc/h)**3
                P_lin = np.interp(self.kh, self.k_fid, P)

        elif self.use_sdssDR7:
            kh = np.logspace(math.log(1e-3),math.log(1.0),num=(math.log(1.0)-math.log(1e-3))/0.01+1,base=math.exp(1.0)) # k in h/Mpc
            # Rescale the scaling factor by the fiducial value for h divided by the sampled value
            # h=0.701 was used for the N-body calibration simulations
            scaling = scaling * (0.701/h)
            k = kh*h # k in 1/Mpc

            # Define redshift bins and associated bao 2 sigma value [NEAR, MID, FAR]
            z = np.array([0.235, 0.342, 0.421])
            sigma2bao = np.array([86.9988, 85.1374, 84.5958])
            # Initialize arrays
            # Analytical growth factor for each redshift bin
            D_growth = np.zeros(len(z))
            # P(k) *with* wiggles, both linear and nonlinear
            Plin = np.zeros(len(k), 'float64')
            Pnl = np.zeros(len(k), 'float64')
            # P(k) *without* wiggles, both linear and nonlinear
            Psmooth = np.zeros(len(k), 'float64')
            Psmooth_nl = np.zeros(len(k), 'float64')
            # Damping function and smeared P(k)
            fdamp = np.zeros([len(k), len(z)], 'float64')
            Psmear = np.zeros([len(k), len(z)], 'float64')
            # Ratio of smoothened non-linear to linear P(k)
            nlratio = np.zeros([len(k), len(z)], 'float64')
            # Loop over each redshift bin
            for j in range(len(z)):
                # Compute growth factor at each redshift
                # This growth factor is normalized by the growth factor today
                D_growth[j] = cosmo.scale_independent_growth_factor(z[j])
                # Compute Pk *with* wiggles, both linear and nonlinear
                # Get P(k) at right values of k in Mpc**3, convert it to (Mpc/h)^3 and rescale it
                # Get values of P(k) in Mpc**3
                for i in range(len(k)):
                    Plin[i] = cosmo.pk_lin(k[i], z[j])
                    Pnl[i] = cosmo.pk(k[i], z[j])
                # Get rescaled values of P(k) in (Mpc/h)**3
                Plin *= h**3 #(h/scaling)**3
                Pnl *= h**3 #(h/scaling)**3
                # Compute Pk *without* wiggles, both linear and nonlinear
                Psmooth = self.remove_bao(kh,Plin)
                Psmooth_nl = self.remove_bao(kh,Pnl)
                # Apply Gaussian damping due to non-linearities
                fdamp[:,j] = np.exp(-0.5*sigma2bao[j]*kh**2)
                Psmear[:,j] = Plin*fdamp[:,j]+Psmooth*(1.0-fdamp[:,j])
                # Take ratio of smoothened non-linear to linear P(k)
                nlratio[:,j] = Psmooth_nl/Psmooth

            # Save fiducial model for non-linear corrections using the flat fiducial
            # Omega_m = 0.25, Omega_L = 0.75, h = 0.701
            # Re-run if changes are made to how non-linear corrections are done
            # e.g. the halofit implementation in CLASS
            # To re-run fiducial, set <experiment>.create_fid = True in .data file
            # Can leave option enabled, as it will only compute once at the start

            # !!!!! --- Heads-up ---- !!!!
            # (JR) forced 'self.create_fid' to false for use with GAMBIT -> if true the function 
            #      'get_flat_fid' wipes content of cosmo container, fills it with params to 
            #       calculate a fiducial model, run CLASS with fiducial model and then the routine
            #       spits out a table in form of file. After that the cosmo object is filled 
            #       again.. We do not want any interference with the cosmo object or a CLASS run 
            #       initiated by MontePython so we are taking care of creating this 'fiducial'
            #       data file when installing MontePython through GAMBIT.
            # --|> This file has to be updated if something in the non-linear module of CLASS changes!!
            self.create_fid = False

            if self.create_fid == True:
                # Calculate relevant flat fiducial quantities
                fidnlratio, fidNEAR, fidMID, fidFAR = self.get_flat_fid(cosmo,data,kh,z,sigma2bao)
                try:
                    existing_fid = np.loadtxt(os.path.join(self.data_directory,'/sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.dat'))
                    print( 'sdss_lrgDR7: Checking fiducial deviations for near, mid and far bins:', np.sum(existing_fid[:,1] - fidNEAR),np.sum(existing_fid[:,2] - fidMID), np.sum(existing_fid[:,3] - fidFAR))
                    if np.sum(existing_fid[:,1] - fidNEAR) + np.sum(existing_fid[:,2] - fidMID) + np.sum(existing_fid[:,3] - fidFAR) < 10**-5:
                        self.create_fid = False
                except:
                    pass
                if self.create_fid == True:
                    print( 'sdss_lrgDR7: Creating fiducial file with Omega_b = 0.25, Omega_L = 0.75, h = 0.701')
                    print ('             Required for non-linear modeling')
                    # Save non-linear corrections from N-body sims for each redshift bin
                    arr=np.zeros((np.size(kh),7))
                    arr[:,0]=kh
                    arr[:,1]=fidNEAR
                    arr[:,2]=fidMID
                    arr[:,3]=fidFAR
                    # Save non-linear corrections from halofit for each redshift bin
                    arr[:,4:7]=fidnlratio
                    np.savetxt('data/sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.dat',arr)
                    self.create_fid = False
                    print ('             Fiducial created')

            # Load fiducial model
            #joined2 = os.path.join(self.data_directory, "sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.dat")
            #joined = os.path.join(self.data_directory,'/sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.dat')
            #print("Data directory %s" % self.data_directory )
            #print("Data directory %s and 2nd try %s" %  (joined, joined2))
            print("Trying to load %s" % os.path.join(self.data_directory,'sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.dat'))
            fiducial = np.loadtxt(os.path.join(self.data_directory,'sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.dat'))
            #fiducial = np.loadtxt('data/sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.dat')
            fid = fiducial[:,1:4]
            fidnlratio = fiducial[:,4:7]

            # Put all factors together to obtain the P(k) for each redshift bin
            Pnear=np.interp(kh,kh,Psmear[:,0]*(nlratio[:,0]/fidnlratio[:,0])*fid[:,0]*D_growth[0]**(-2.))
            Pmid =np.interp(kh,kh,Psmear[:,1]*(nlratio[:,1]/fidnlratio[:,1])*fid[:,1]*D_growth[1]**(-2.))
            Pfar =np.interp(kh,kh,Psmear[:,2]*(nlratio[:,2]/fidnlratio[:,2])*fid[:,2]*D_growth[2]**(-2.))

            # Define and rescale k
            self.k=self.kh*h*scaling
            # Weighted mean of the P(k) for each redshift bin
            P_lin=(0.395*Pnear+0.355*Pmid+0.250*Pfar)
            P_lin=np.interp(self.k,kh*h,P_lin)*(1./scaling)**3 # remember self.k is scaled but self.kh isn't

        else:
            # get rescaled values of k in 1/Mpc
            self.k = self.kh*h*scaling
            # get values of P(k) in Mpc**3
            for i in range(self.k_size):
                P_lin[i] = cosmo.pk(self.k[i], self.redshift)
            # get rescaled values of P(k) in (Mpc/h)**3
            P_lin *= (h/scaling)**3

        # infer P_th from P_lin. It is still in (Mpc/h)**3. TODO why was it
        # called P_lin in the first place ? Couldn't we use now P_th all the
        # way ?
        P_th = P_lin

        if self.use_sdssDR7:
            chisq =np.zeros(self.nptstot)
            chisqmarg = np.zeros(self.nptstot)

            Pth = P_th
            Pth_k = P_th*(self.k/h) # self.k has the scaling included, so self.k/h != self.kh
            Pth_k2 = P_th*(self.k/h)**2

            WPth = np.dot(self.window[0,:], Pth)
            WPth_k = np.dot(self.window[0,:], Pth_k)
            WPth_k2 = np.dot(self.window[0,:], Pth_k2)

            sumzerow_Pth = np.sum(self.zerowindowfxn*Pth)/self.zerowindowfxnsubtractdatnorm
            sumzerow_Pth_k = np.sum(self.zerowindowfxn*Pth_k)/self.zerowindowfxnsubtractdatnorm
            sumzerow_Pth_k2 = np.sum(self.zerowindowfxn*Pth_k2)/self.zerowindowfxnsubtractdatnorm

            covdat = np.dot(self.invcov[0,:,:],self.P_obs[0,:])
            covth  = np.dot(self.invcov[0,:,:],WPth)
            covth_k  = np.dot(self.invcov[0,:,:],WPth_k)
            covth_k2  = np.dot(self.invcov[0,:,:],WPth_k2)
            covth_zerowin  = np.dot(self.invcov[0,:,:],self.zerowindowfxnsubtractdat)
            sumDD = np.sum(self.P_obs[0,:] * covdat)
            sumDT = np.sum(self.P_obs[0,:] * covth)
            sumDT_k = np.sum(self.P_obs[0,:] * covth_k)
            sumDT_k2 = np.sum(self.P_obs[0,:] * covth_k2)
            sumDT_zerowin = np.sum(self.P_obs[0,:] * covth_zerowin)

            sumTT = np.sum(WPth*covth)
            sumTT_k = np.sum(WPth*covth_k)
            sumTT_k2 = np.sum(WPth*covth_k2)
            sumTT_k_k = np.sum(WPth_k*covth_k)
            sumTT_k_k2 = np.sum(WPth_k*covth_k2)
            sumTT_k2_k2 = np.sum(WPth_k2*covth_k2)
            sumTT_zerowin = np.sum(WPth*covth_zerowin)
            sumTT_k_zerowin = np.sum(WPth_k*covth_zerowin)
            sumTT_k2_zerowin = np.sum(WPth_k2*covth_zerowin)
            sumTT_zerowin_zerowin = np.sum(self.zerowindowfxnsubtractdat*covth_zerowin)

            currminchisq = 1000.0

            # analytic marginalization over a1,a2
            for i in range(self.nptstot):
                a1val = self.a1list[i]
                a2val = self.a2list[i]
                zerowinsub = -(sumzerow_Pth + a1val*sumzerow_Pth_k + a2val*sumzerow_Pth_k2)
                sumDT_tot = sumDT + a1val*sumDT_k + a2val*sumDT_k2 + zerowinsub*sumDT_zerowin
                sumTT_tot = sumTT + a1val**2.0*sumTT_k_k + a2val**2.0*sumTT_k2_k2 + \
                    zerowinsub**2.0*sumTT_zerowin_zerowin + \
                    2.0*a1val*sumTT_k + 2.0*a2val*sumTT_k2 + 2.0*a1val*a2val*sumTT_k_k2 + \
                    2.0*zerowinsub*sumTT_zerowin + 2.0*zerowinsub*a1val*sumTT_k_zerowin + \
                    2.0*zerowinsub*a2val*sumTT_k2_zerowin
                minchisqtheoryamp = sumDT_tot/sumTT_tot
                chisq[i] = sumDD - 2.0*minchisqtheoryamp*sumDT_tot + minchisqtheoryamp**2.0*sumTT_tot
                chisqmarg[i] = sumDD - sumDT_tot**2.0/sumTT_tot + math.log(sumTT_tot) - \
                    2.0*math.log(1.0 + math.erf(sumDT_tot/2.0/math.sqrt(sumTT_tot)))
                if(i == 0 or chisq[i] < currminchisq):
                    myminchisqindx = i
                    currminchisq = chisq[i]
                    currminchisqmarg = chisqmarg[i]
                    minchisqtheoryampminnuis = minchisqtheoryamp
                if(i == int(self.nptstot/2)):
                    chisqnonuis = chisq[i]
                    minchisqtheoryampnonuis = minchisqtheoryamp
                    if(abs(a1val) > 0.001 or abs(a2val) > 0.001):
                         print ('sdss_lrgDR7: ahhhh! violation!!', a1val, a2val)

            # numerically marginalize over a1,a2 now using values stored in chisq
            minchisq = np.min(chisqmarg)
            maxchisq = np.max(chisqmarg)

            LnLike = np.sum(np.exp(-(chisqmarg-minchisq)/2.0)/(self.nptstot*1.0))
            if(LnLike == 0):
                print('Error in likelihood %s ' % (self.name) +'LRG LnLike LogZero error.' )
                #    'LRG LnLike LogZero error.' )
                #LnLike = LogZero
                #raise io_mp.LikelihoodError(  # (JR) commented to avoid io_mp
                #    'Error in likelihood %s ' % (self.name) +
                #    'LRG LnLike LogZero error.' )
            else:
                chisq = -2.*math.log(LnLike) + minchisq
            #print 'DR7 chi2/2=',chisq/2.

        #if we are not using DR7
        else:
            W_P_th = np.zeros((self.n_size), 'float64')

            # starting analytic marginalisation over bias

            # Define quantities living in all the regions possible. If only a few
            # regions are selected in the .data file, many elements from these
            # arrays will stay at 0.
            P_data_large = np.zeros(
                (self.n_size*self.num_regions_used), 'float64')
            W_P_th_large = np.zeros(
                (self.n_size*self.num_regions_used), 'float64')
            cov_dat_large = np.zeros(
                (self.n_size*self.num_regions_used), 'float64')
            cov_th_large = np.zeros(
                (self.n_size*self.num_regions_used), 'float64')

            normV = 0

            # Loop over all the available regions
            for i_region in range(self.num_regions):
                # In each region that was selected with the array of flags
                # self.used_region, define boundaries indices, and fill in the
                # corresponding windowed power spectrum. All the unused regions
                # will still be set to zero as from the initialization, which will
                # not contribute anything in the final sum.

                if self.used_region[i_region]:
                    imin = i_region*self.n_size
                    imax = (i_region+1)*self.n_size-1

                    W_P_th = np.dot(self.window[i_region, :], P_th)
                    #print W_P_th
                    for i in range(self.n_size):
                        P_data_large[imin+i] = self.P_obs[i_region, i]
                        W_P_th_large[imin+i] = W_P_th[i]
                        cov_dat_large[imin+i] = np.dot(
                            self.invcov[i_region, i, :],
                            self.P_obs[i_region, :])
                        cov_th_large[imin+i] = np.dot(
                            self.invcov[i_region, i, :],
                            W_P_th[:])

            # Explain what it is TODO
            normV += np.dot(W_P_th_large, cov_th_large)
            # Sort of bias TODO ?
            b_out = np.sum(W_P_th_large*cov_dat_large) / \
                np.sum(W_P_th_large*cov_th_large)

            # Explain this formula better, link to article ?
            chisq = np.dot(P_data_large, cov_dat_large) - \
                np.dot(W_P_th_large, cov_dat_large)**2/normV
            #print 'WiggleZ chi2=',chisq/2.

        return -chisq/2

    def remove_bao(self,k_in,pk_in):
        # De-wiggling routine by Mario Ballardini

        # This k range has to contain the BAO features:
        k_ref=[2.8e-2, 4.5e-1]

        # Get interpolating function for input P(k) in log-log space:
        _interp_pk = scipy.interpolate.interp1d( np.log(k_in), np.log(pk_in),
                                                 kind='quadratic', bounds_error=False )
        interp_pk = lambda x: np.exp(_interp_pk(np.log(x)))

        # Spline all (log-log) points outside k_ref range:
        idxs = np.where(np.logical_or(k_in <= k_ref[0], k_in >= k_ref[1]))
        _pk_smooth = scipy.interpolate.UnivariateSpline( np.log(k_in[idxs]),
                                                         np.log(pk_in[idxs]), k=3, s=0 )
        pk_smooth = lambda x: np.exp(_pk_smooth(np.log(x)))

        # Find second derivative of each spline:
        fwiggle = scipy.interpolate.UnivariateSpline(k_in, pk_in / pk_smooth(k_in), k=3, s=0)
        derivs = np.array([fwiggle.derivatives(_k) for _k in k_in]).T
        d2 = scipy.interpolate.UnivariateSpline(k_in, derivs[2], k=3, s=1.0)

        # Find maxima and minima of the gradient (zeros of 2nd deriv.), then put a
        # low-order spline through zeros to subtract smooth trend from wiggles fn.
        wzeros = d2.roots()
        wzeros = wzeros[np.where(np.logical_and(wzeros >= k_ref[0], wzeros <= k_ref[1]))]
        wzeros = np.concatenate((wzeros, [k_ref[1],]))
        wtrend = scipy.interpolate.UnivariateSpline(wzeros, fwiggle(wzeros), k=3, s=0)

        # Construct smooth no-BAO:
        idxs = np.where(np.logical_and(k_in > k_ref[0], k_in < k_ref[1]))
        pk_nobao = pk_smooth(k_in)
        pk_nobao[idxs] *= wtrend(k_in[idxs])

        # Construct interpolating functions:
        ipk = scipy.interpolate.interp1d( k_in, pk_nobao, kind='linear',
                                          bounds_error=False, fill_value=0. )

        pk_nobao = ipk(k_in)

        return pk_nobao

    def get_flat_fid(self,cosmo,data,kh,z,sigma2bao):
        # SDSS DR7 LRG specific function
        # Compute fiducial properties for a flat fiducial
        # with Omega_m = 0.25, Omega_L = 0.75, h = 0.701
        

        raise io_mp.LikelihoodError(
                        "You entered the attribute 'get_flat_fid' of the 'Likelihood_mpk' object.\n" +
                        "This should never happen in GAMBIT as this routine is a bit dodgy as\n" +
                        "it manipulates the the 'cosmo' instance of the classy Class Class()\n" +
                        "by filling it with different parameters and executing a CLASS run.\n"+
                        "The purpose is to get a table with data from a fiducial cosmology.\n"+
                        "Therefore the GAMBIT patch provides this fiducial table which is supposed to be copied to\n"+
                        " \t'montepythonlike/<verion_number>/data/sdss_lrgDR7/sdss_lrgDR7_fiducialmodel.data'\n"+
                        "This message will show up if the copying did not work... (blame Janina)")

        ''' ---- MontePython original routine --- 
        param_backup = data.cosmo_arguments
        data.cosmo_arguments = {'P_k_max_h/Mpc': 1.5, 'ln10^{10}A_s': 3.0, 'N_ur': 3.04, 'h': 0.701,
                                'omega_b': 0.035*0.701**2, 'non linear': ' halofit ', 'YHe': 0.24, 'k_pivot': 0.05,
                                'n_s': 0.96, 'tau_reio': 0.084, 'z_max_pk': 0.5, 'output': ' mPk ',
                                'omega_cdm': 0.215*0.701**2, 'T_cmb': 2.726}
        cosmo.empty()
        cosmo.set(data.cosmo_arguments)
        cosmo.compute(['lensing'])
        h = data.cosmo_arguments['h']
        k = kh*h
        # P(k) *with* wiggles, both linear and nonlinear
        Plin = np.zeros(len(k), 'float64')
        Pnl = np.zeros(len(k), 'float64')
        # P(k) *without* wiggles, both linear and nonlinear
        Psmooth = np.zeros(len(k), 'float64')
        Psmooth_nl = np.zeros(len(k), 'float64')
        # Damping function and smeared P(k)
        fdamp = np.zeros([len(k), len(z)], 'float64')
        Psmear = np.zeros([len(k), len(z)], 'float64')
        # Ratio of smoothened non-linear to linear P(k)
        fidnlratio = np.zeros([len(k), len(z)], 'float64')
        # Loop over each redshift bin
        for j in range(len(z)):
            # Compute Pk *with* wiggles, both linear and nonlinear
            # Get P(k) at right values of k in Mpc**3, convert it to (Mpc/h)^3 and rescale it
            # Get values of P(k) in Mpc**3
            for i in range(len(k)):
                Plin[i] = cosmo.pk_lin(k[i], z[j])
                Pnl[i] = cosmo.pk(k[i], z[j])
            # Get rescaled values of P(k) in (Mpc/h)**3
            Plin *= h**3 #(h/scaling)**3
            Pnl *= h**3 #(h/scaling)**3
            # Compute Pk *without* wiggles, both linear and nonlinear
            Psmooth = self.remove_bao(kh,Plin)
            Psmooth_nl = self.remove_bao(kh,Pnl)
            # Apply Gaussian damping due to non-linearities
            fdamp[:,j] = np.exp(-0.5*sigma2bao[j]*kh**2)
            Psmear[:,j] = Plin*fdamp[:,j]+Psmooth*(1.0-fdamp[:,j])
            # Take ratio of smoothened non-linear to linear P(k)
            fidnlratio[:,j] = Psmooth_nl/Psmooth

        # Polynomials to shape small scale behavior from N-body sims
        kdata=kh
        fidpolyNEAR=np.zeros(np.size(kdata))
        fidpolyNEAR[kdata<=0.194055] = (1.0 - 0.680886*kdata[kdata<=0.194055] + 6.48151*kdata[kdata<=0.194055]**2)
        fidpolyNEAR[kdata>0.194055] = (1.0 - 2.13627*kdata[kdata>0.194055] + 21.0537*kdata[kdata>0.194055]**2 - 50.1167*kdata[kdata>0.194055]**3 + 36.8155*kdata[kdata>0.194055]**4)*1.04482
        fidpolyMID=np.zeros(np.size(kdata))
        fidpolyMID[kdata<=0.19431] = (1.0 - 0.530799*kdata[kdata<=0.19431] + 6.31822*kdata[kdata<=0.19431]**2)
        fidpolyMID[kdata>0.19431] = (1.0 - 1.97873*kdata[kdata>0.19431] + 20.8551*kdata[kdata>0.19431]**2 - 50.0376*kdata[kdata>0.19431]**3 + 36.4056*kdata[kdata>0.19431]**4)*1.04384
        fidpolyFAR=np.zeros(np.size(kdata))
        fidpolyFAR[kdata<=0.19148] = (1.0 - 0.475028*kdata[kdata<=0.19148] + 6.69004*kdata[kdata<=0.19148]**2)
        fidpolyFAR[kdata>0.19148] = (1.0 - 1.84891*kdata[kdata>0.19148] + 21.3479*kdata[kdata>0.19148]**2 - 52.4846*kdata[kdata>0.19148]**3 + 38.9541*kdata[kdata>0.19148]**4)*1.03753

        fidNEAR=np.interp(kh,kdata,fidpolyNEAR)
        fidMID=np.interp(kh,kdata,fidpolyMID)
        fidFAR=np.interp(kh,kdata,fidpolyFAR)

        cosmo.empty()
        data.cosmo_arguments = param_backup
        cosmo.set(data.cosmo_arguments)
        cosmo.compute(['lensing'])

        return fidnlratio, fidNEAR, fidMID, fidFAR
        '''
    
class Likelihood_sn(Likelihood):

    def __init__(self, path, data, command_line):

        Likelihood.__init__(self, path, data, command_line)

        # try and import pandas
        try:
            import pandas
        except ImportError:
            #raise io_mp.MissingLibraryError(
            print(
                "This likelihood has a lot of IO manipulation. You have "
                "to install the 'pandas' library to use it. Please type:\n"
                "`(sudo) pip install pandas --user`")

        # check that every conflicting experiments is not present in the list
        # of tested experiments, in which case, complain
        if hasattr(self, 'conflicting_experiments'):
            for conflict in self.conflicting_experiments:
                if conflict in data.experiments:
                    #raise io_mp.LikelihoodError(
                    print(
                        'conflicting %s measurements, you can ' % conflict +
                        ' have either %s or %s ' % (self.name, conflict) +
                        'as an experiment, not both')

        # Read the configuration file, supposed to be called self.settings.
        # Note that we unfortunately can not
        # immediatly execute the file, as it is not formatted as strings.
        assert hasattr(self, 'settings') is True, (
            "You need to provide a settings file")
        self.read_configuration_file()

    def read_configuration_file(self):
        """
        Extract Python variables from the configuration file

        This routine performs the equivalent to the program "inih" used in the
        original c++ library.
        """
        settings_path = os.path.join(self.data_directory, self.settings)
        with open(settings_path, 'r') as config:
            for line in config:
                # Dismiss empty lines and commented lines
                if line and line.find('#') == -1 and line not in ['\n', '\r\n']:
                    lhs, rhs = [elem.strip() for elem in line.split('=')]
                    # lhs will always be a string, so set the attribute to this
                    # likelihood. The right hand side requires more work.
                    # First case, if set to T or F for True or False
                    if str(rhs) in ['T', 'F']:
                        rhs = True if str(rhs) == 'T' else False
                    # It can also be a path, starting with 'data/'. We remove
                    # this leading folder path
                    elif str(rhs).find('data/') != -1:
                        rhs = rhs.replace('data/', '')
                    else:
                        # Try  to convert it to a float
                        try:
                            rhs = float(rhs)
                        # If it fails, it is a string
                        except ValueError:
                            rhs = str(rhs)
                    # Set finally rhs to be a parameter of the class
                    setattr(self, lhs, rhs)

    def read_matrix(self, path):
        """
        extract the matrix from the path

        This routine uses the blazing fast pandas library (0.10 seconds to load
        a 740x740 matrix). If not installed, it uses a custom routine that is
        twice as slow (but still 4 times faster than the straightforward
        numpy.loadtxt method)

        .. note::

            the length of the matrix is stored on the first line... then it has
            to be unwrapped. The pandas routine read_table understands this
            immediatly, though.

        """
        from pandas import read_table
        path = os.path.join(self.data_directory, path)
        # The first line should contain the length.
        with open(path, 'r') as text:
            length = int(text.readline())

        # Note that this function does not require to skiprows, as it
        # understands the convention of writing the length in the first
        # line
        matrix = read_table(path).as_matrix().reshape((length, length))

        return matrix

    def read_light_curve_parameters(self):
        """
        Read the file jla_lcparams.txt containing the SN data

        .. note::

            the length of the resulting array should be equal to the length of
            the covariance matrices stored in C00, etc...

        """
        from pandas import read_table
        path = os.path.join(self.data_directory, self.data_file)

        # Recover the names of the columns. The names '3rdvar' and 'd3rdvar'
        # will be changed, because 3rdvar is not a valid variable name
        with open(path, 'r') as text:
            clean_first_line = text.readline()[1:].strip()
            names = [e.strip().replace('3rd', 'third')
                     for e in clean_first_line.split()]

        lc_parameters = read_table(
            path, sep=' ', names=names, header=0, index_col=False)
        return lc_parameters


class Likelihood_clocks(Likelihood):
    """Base implementation of H(z) measurements"""

    def __init__(self, path, data, command_line):

        Likelihood.__init__(self, path, data, command_line)

        # Read the content of the data file, containing z, Hz and error
        total = np.loadtxt(
            os.path.join(self.data_directory, self.data_file))

        # Store the columns separately
        self.z = total[:, 0]
        self.Hz = total[:, 1]
        self.err = total[:, 2]

    def loglkl(self, cosmo, data):

        # Store the speed of light in km/s
        c_light_km_per_sec = const.c/1000.
        chi2 = 0

        # Loop over the redshifts
        for index, z in enumerate(self.z):
            # Query the cosmo module for the Hubble rate (in 1/Mpc), and
            # convert it to km/s/Mpc
            H_cosmo = cosmo.Hubble(z)*c_light_km_per_sec
            # Add to the tota chi2
            chi2 += (self.Hz[index]-H_cosmo)**2/self.err[index]**2

        return -0.5 * chi2

###################################
# ISW-Likelihood
# by B. Stoelzner
###################################
class Likelihood_isw(Likelihood):
    def __init__(self, path, data, command_line):
        # Initialize
        Likelihood.__init__(self, path, data, command_line)
        self.need_cosmo_arguments(data, {'output': 'mPk','P_k_max_h/Mpc' : 300,'z_max_pk' : 5.1})

        # Read l,C_l, and the covariance matrix of the autocorrelation of the survey and the crosscorrelation of the survey with the CMB
        self.l_cross,cl_cross=np.loadtxt(os.path.join(self.data_directory,self.cl_cross_file),unpack=True,usecols=(0,1))
        self.l_auto,cl_auto=np.loadtxt(os.path.join(self.data_directory,self.cl_auto_file),unpack=True,usecols=(0,1))
        cov_cross=np.loadtxt(os.path.join(self.data_directory,self.cov_cross_file))
        cov_auto=np.loadtxt(os.path.join(self.data_directory,self.cov_auto_file))

        # Extract data in the specified range in l.
        self.l_cross=self.l_cross[self.l_min_cross:self.l_max_cross+1]
        cl_cross=cl_cross[self.l_min_cross:self.l_max_cross+1]
        self.l_auto=self.l_auto[self.l_min_auto:self.l_max_auto+1]
        cl_auto=cl_auto[self.l_min_auto:self.l_max_auto+1]
        cov_cross=cov_cross[self.l_min_cross:self.l_max_cross+1,self.l_min_cross:self.l_max_cross+1]
        cov_auto=cov_auto[self.l_min_auto:self.l_max_auto+1,self.l_min_auto:self.l_max_auto+1]

        # Create logarithically spaced bins in l.
        self.bins_cross=np.ceil(np.logspace(np.log10(self.l_min_cross),np.log10(self.l_max_cross),self.n_bins_cross+1))
        self.bins_auto=np.ceil(np.logspace(np.log10(self.l_min_auto),np.log10(self.l_max_auto),self.n_bins_auto+1))

        # Bin l,C_l, and covariance matrix in the previously defined bins
        self.l_binned_cross,self.cl_binned_cross,self.cov_binned_cross=self.bin_cl(self.l_cross,cl_cross,self.bins_cross,cov_cross)
        self.l_binned_auto,self.cl_binned_auto,self.cov_binned_auto=self.bin_cl(self.l_auto,cl_auto,self.bins_auto,cov_auto)

        # Read the redshift distribution of objects in the survey, perform an interpolation of dN/dz(z), and calculate the normalization in this redshift bin
        zz,dndz=np.loadtxt(os.path.join(self.data_directory,self.dndz_file),unpack=True,usecols=(0,1))
        self.dndz=scipy.interpolate.interp1d(zz,dndz,kind='cubic')
        self.norm=scipy.integrate.quad(self.dndz,self.z_min,self.z_max)[0]

    def bin_cl(self,l,cl,bins,cov=None):
        # This function bins l,C_l, and the covariance matrix in given bins in l
        B=[]
        for i in range(1,len(bins)):
            if i!=len(bins)-1:
                a=np.where((l<bins[i])&(l>=bins[i-1]))[0]
            else:
                a=np.where((l<=bins[i])&(l>=bins[i-1]))[0]
            c=np.zeros(len(l))
            c[a]=1./len(a)
            B.append(c)
        l_binned=np.dot(B,l)
        cl_binned=np.dot(B,cl)
        if cov is not None:
            cov_binned=np.dot(B,np.dot(cov,np.transpose(B)))
            return l_binned,cl_binned,cov_binned
        else:
            return l_binned,cl_binned

    def integrand_cross(self,z,cosmo,l):
        # This function will be integrated to calculate the exspected crosscorrelation between the survey and the CMB
        c= const.c/1000.
        H0=cosmo.h()*100
        Om=cosmo.Omega0_m()
        k=lambda z:(l+0.5)/(cosmo.angular_distance(z)*(1+z))
        return (3*Om*H0**2)/((c**2)*(l+0.5)**2)*self.dndz(z)*cosmo.Hubble(z)*cosmo.scale_independent_growth_factor(z)*scipy.misc.derivative(lambda z:cosmo.scale_independent_growth_factor(z)*(1+z),x0=z,dx=1e-4)*cosmo.pk(k(z),0)/self.norm

    def integrand_auto(self,z,cosmo,l):
        # This function will be integrated to calculate the expected autocorrelation of the survey
        c= const.c/1000.
        H0=cosmo.h()*100
        k=lambda z:(l+0.5)/(cosmo.angular_distance(z)*(1+z))
        return (self.dndz(z))**2*(cosmo.scale_independent_growth_factor(z))**2*cosmo.pk(k(z),0)*cosmo.Hubble(z)/(cosmo.angular_distance(z)*(1+z))**2/self.norm**2

    def compute_loglkl(self, cosmo, data,b):
        # Retrieve sampled parameter
        A=data.mcmc_parameters['A_ISW']['current']*data.mcmc_parameters['A_ISW']['scale']

        # Calculate the expected auto- and crosscorrelation by integrating over the redshift.
        cl_binned_cross_theory=np.array([(scipy.integrate.quad(self.integrand_cross,self.z_min,self.z_max,args=(cosmo,self.bins_cross[ll]))[0]+scipy.integrate.quad(self.integrand_cross,self.z_min,self.z_max,args=(cosmo,self.bins_cross[ll+1]))[0]+scipy.integrate.quad(self.integrand_cross,self.z_min,self.z_max,args=(cosmo,self.l_binned_cross[ll]))[0])/3 for ll in range(self.n_bins_cross)])
        cl_binned_auto_theory=np.array([scipy.integrate.quad(self.integrand_auto,self.z_min,self.z_max,args=(cosmo,ll),epsrel=1e-8)[0] for ll in self.l_binned_auto])

        # Calculate the chi-square of auto- and crosscorrelation
        chi2_cross=np.asscalar(np.dot(self.cl_binned_cross-A*b*cl_binned_cross_theory,np.dot(np.linalg.inv(self.cov_binned_cross),self.cl_binned_cross-A*b*cl_binned_cross_theory)))
        chi2_auto=np.asscalar(np.dot(self.cl_binned_auto-b**2*cl_binned_auto_theory,np.dot(np.linalg.inv(self.cov_binned_auto),self.cl_binned_auto-b**2*cl_binned_auto_theory)))
        return -0.5*(chi2_cross+chi2_auto)



class Data(object):
    """
    Store all relevant data to communicate between the different modules.
    (JR) added input:
        str data_file: string with path to datafile (folder containing data)
        str arr experiments: array with string off all experiments used in scan 

    """

    def __init__(self, command_line, path, experiments):  
        """
        The Data class holds the cosmological information, the parameters from
        the MCMC run, the information coming from the likelihoods. It is a wide
        collections of information, with in particular two main dictionaries:
        cosmo_arguments and mcmc_parameters.

        It defines several useful **methods**. The following ones are called
        just once, at initialization:

        * :func:`fill_mcmc_parameters`
        * :func:`read_file`
        * :func:`read_version`
        * :func:`group_parameters_in_blocks`

        On the other hand, these two following functions are called every step.

        * :func:`check_for_slow_step`
        * :func:`update_cosmo_arguments`

        Finally, the convenient method :func:`get_mcmc_parameters` will be
        called in many places, to return the proper list of desired parameters.

        It has a number of different **attributes**, and the more important
        ones are listed here:

        * :attr:`boundary_loglike`
        * :attr:`cosmo_arguments`
        * :attr:`mcmc_parameters`
        * :attr:`need_cosmo_update`
        * :attr:`log_flag`

        .. note::

            The `experiments` attribute is extracted from the parameter file,
            and contains the list of likelihoods to use

        .. note::

            The path argument will be used in case it is a first run, and hence
            a new folder is created. If starting from an existing folder, this
            dictionary will be compared with the one extracted from the
            log.param, and will use the latter while warning the user.

        .. warning::

            New in version 2.0.0, you can now specify an oversampling of the
            nuisance parameters, to hasten the execution of a run with
            likelihoods that have many of them. You should specify a new field
            in the parameter file, `data.over_sampling = [1, ...]`, that
            contains a 1 on the first element, and then the over sampling of
            the desired likelihoods. This array must have the same size as the
            number of blocks (1 for the cosmo + 1 for each likelihood with
            varying nuisance parameters). You need to call the code with the
            flag `-j jast` for it to be used.

        To create an instance of this class, one must feed the following
        parameters and keyword arguments:

        Parameters
        ----------
        command_line : NameSpace
            NameSpace containing the input from the :mod:`parser_mp`. It
            stores the input parameter file, the jumping methods, the output
            folder, etc...  Most of the information extracted from the
            command_file will be transformed into :class:`Data` attributes,
            whenever it felt meaningful to do so.
        path : dict
            Contains a dictionary of important local paths. It is used here to
            find the cosmological module location.

        """

        # Initialisation of the random seed
        rd.seed()

        # Store the parameter file
        #self.param = command_line.param
        #self.param = 

        # Recover jumping method from command_line
        self.jumping = ""
        self.jumping_factor = 1

        # Store the rest of the command line
        self.command_line = ""

        # Initialise the path dictionnary.
        self.path = path

        self.boundary_loglike = -1e30
        """
        Define the boundary loglike, the value used to defined a loglike
        that is out of bounds. If a point in the parameter space is affected to
        this value, it will be automatically rejected, hence increasing the
        multiplicity of the last accepted point.
        """

        # Creation of the two main dictionnaries:
        self.cosmo_arguments = {}
        """
        Simple dictionary that will serve as a communication interface with the
        cosmological code. It contains all the parameters for the code that
        will not be set to their default values.  It is updated from
        :attr:`mcmc_parameters`.

        :rtype:   dict
        """
        self.mcmc_parameters = {}
        #self.mcmc_parameters = mcmc_parameters
        """
        Ordered dictionary of dictionaries, it contains everything needed by
        the :mod:`mcmc` module for the MCMC procedure.  Every parameter name
        will be the key of a dictionary, containing the initial configuration,
        role, status, last accepted point and current point.

        :rtype: ordereddict
        """

        # Arguments for PyMultiNest
        self.NS_param_names = []
        self.NS_arguments = {}
        """
        Dictionary containing the parameters needed by the PyMultiNest sampler.
        It is filled just before the run of the sampler.  Those parameters not
        defined will be set to the default value of PyMultiNest.

        :rtype: dict
        """

        # Arguments for PyPolyChord 
        self.PC_param_names = []
        self.PC_arguments = {}
        """
        Dictionary containing the parameters needed by the PyPolyChord sampler.
        It is filled just before the run of the sampler.  Those parameters not
        defined will be set to the default value of PyPolyChord.

        :rtype: dict
        """

        # Initialise the experiments attribute
        self.experiments = experiments

        # Initialise the oversampling setting
        self.over_sampling = []
        """
        List storing the respective over sampling of the parameters. The first
        entry, applied to the cosmological parameters, will always be 1.
        Setting it to anything else would simply rescale the whole process. If
        not specified otherwise in the parameter file, all other numbers will
        be set to 1 as well.

        :rtype: list
        """

        # Default value for the number of steps
        self.N = 10

        # Create the variable out, and out_name, which will be initialised
        # later by the :mod:`io_mp` module
        self.out = None
        self.out_name = ''

        # If the parameter file is not a log.param, the path will be read
        # before reading the parameter file.
        #if self.param.find('log.param') == -1:
        #   self.path.update(path)

        # Read from the parameter file to fill properly the mcmc_parameters
        # dictionary.
        #self.fill_mcmc_parameters()

        # Test if the recovered path agrees with the one extracted from
        # the configuration file.
        if self.path != {}:
            if not self.path.has_key('root'):
                self.path.update({'root': path['root']})
            if self.path != path:
                warnings.warn(
                    "Your code location in the log.param file is "
                    "in contradiction with your .conf file. "
                    "I will use the one from log.param.")

        # Determine which cosmological code is in use
        if self.path['cosmo'].find('class') != -1:
            self.cosmological_module_name = 'CLASS'
        else:
            self.cosmological_module_name = None

        # check for MPI
        try:
            from mpi4py import MPI
            comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
        except ImportError:
            # set all chains to master if no MPI
            rank = 0

        # Recover the cosmological code version (and git hash if relevant).
        # To implement a new cosmological code, please add another case to the
        # test below.
        if self.cosmological_module_name == 'CLASS':
            # Official version number
            common_file_path = os.path.join(
                self.path['cosmo'], 'include', 'common.h')
            with open(common_file_path, 'r') as common_file:
                for line in common_file:
                    if line.find('_VERSION_') != -1:
                        self.version = line.split()[-1].replace('"', '')
                        break
            #if not command_line.silent and not rank:
            #    print 'with CLASS %s' % self.version
            # Git version number and branch
            try:
                # This nul_file helps to get read of a potential useless error
                # message
                with open(os.devnull, "w") as nul_file:
                    self.git_version = sp.Popen(
                        ["git", "rev-parse", "HEAD"],
                        cwd=self.path['cosmo'],
                        stdout=sp.PIPE,
                        stderr=nul_file).communicate()[0].strip()
                    self.git_branch = sp.Popen(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        cwd=self.path['cosmo'],
                        stdout=sp.PIPE,
                        stderr=nul_file).communicate()[0].strip()
            except (sp.CalledProcessError, OSError):
                # Note, OSError seems to be raised on some systems, instead of
                # sp.CalledProcessError - which seems to be linked to the
                # existence of os.devnull, so now both error are caught.
                warnings.warn(
                    "Running CLASS from a non version-controlled repository")
                self.git_version, self.git_branch = '', ''

            # If using an existing log.param, read in and compare this number
            # to the already stored one
            '''if self.param.find('log.param') != -1:
                try:
                    version, git_version, git_branch = self.read_version(
                        self.param_file)
                    if version != self.version:
                        warnings.warn(
                            "Your version of CLASS: %s" % self.version +
                            " does not match the one used previously" +
                            " in this folder (%s)." % version +
                            " Proceed with caution")
                    else:
                        if self.git_branch != git_branch:
                            warnings.warn(
                                "CLASS set to branch %s" % self.git_branch +
                                ", wrt. the one used in the log.param:" +
                                " %s." % git_branch)
                        if self.git_version != git_version:
                            warnings.warn(
                                "CLASS set to version %s" % self.git_version +
                                ", wrt. the one used in the log.param:" +
                                " %s." % git_version)

                except AttributeError:
                    # This error is raised when the regular expression match
                    # failed - due to comparing to an old log.param that did
                    # not have this feature properly implemented. Ignore this.
                    pass '''

        else:
            raise io_mp.CosmologicalModuleError(
                "If you want to check for another cosmological module version"
                " please add an elif clause to this part")

        # End of initialisation with the parameter file
        #self.param_file.close()

        self.log_flag = False
        """
        Stores the information whether or not the likelihood data files need to
        be written down in the log.param file. Initially at False.

        :rtype: bool
        """

        self.need_cosmo_update = True
        """
        `added in version 1.1.1`. It stores the truth value of whether the
        cosmological block of parameters was changed from one step to another.
        See :meth:`group_parameters_in_blocks`

        :rtype: bool
        """

        # logging the parameter file (only if folder does not exist !)
        ## temporary variable for readability
        '''log_param = os.path.join(command_line.folder, 'log.param')
        # (JR) commented -- don't need to store files or data 
        if (os.path.exists(command_line.folder) and
                not os.path.exists(log_param)):
            if command_line.param is not None:
                warnings.warn(
                    "Detecting empty folder, logging the parameter file")
                io_mp.log_parameters(self, command_line)
                self.log_flag = True
        if not os.path.exists(command_line.folder):
            os.makedirs(command_line.folder)
            # Logging of parameters
            io_mp.log_parameters(self, command_line)
            self.log_flag = True'''
#
#        #if not command_line.silent and not rank:
#        #    print '\nTesting likelihoods for:\n ->',
        #    print ', '.join(self.experiments)+'\n'

        #self.initialise_likelihoods(self.experiments)          #(JR) commented

        # Storing parameters by blocks of speed
        #self.group_parameters_in_blocks()          #(JR) commented

        # Finally, log the cosmo_arguments used. This comes in the end, because
        # it can be modified inside the likelihoods init functions
        #(JR) commented
        #if self.log_flag:
        #    io_mp.log_cosmo_arguments(self, command_line)
        #    io_mp.log_default_configuration(self, command_line)

        # Log plotting parameter names file for compatibility with GetDist
        #io_mp.log_parameter_names(self, command_line)

        '''   def fill_mcmc_parameters(self):
        """
        Initializes the ordered dictionary :attr:`mcmc_parameters` from
        the input parameter file.

        It uses :meth:`read_file`, and initializes instances of
        :class:`parameter` to actually fill in :attr:`mcmc_parameters`.

        """

        # Define temporary quantities, only to simplify the input in the
        # parameter file
        self.parameters = od()

        # Read from the parameter file everything
        try:
            self.param_file = open(self.param, 'r')
        except IOError:
            raise io_mp.ConfigurationError(
                "Error in initializing the Data class, the parameter file " +
                "{0} does not point to a proper file".format(self.param))
        # In case the parameter file is a log.param, scan first once the file
        # to extract only the path dictionnary.
        if self.param.find('log.param') != -1:
            self.read_file(self.param, 'data', field='path')
        self.read_file(self.param, 'data')

        # Test here whether the number of parameters extracted correspond to
        # the number of lines (to make sure no doublon is present)
        number_of_parameters = sum(
            [1 for l in open(self.param, 'r') if l and l.find('#') == -1
             and l.find('data.parameters[') != -1])
        if number_of_parameters != len(self.parameters):
            raise io_mp.ConfigurationError(
                "You probably have two lines in your parameter files with "
                "the same parameter name. This is most probably an error, "
                "which will cause problems down the line. Please fix this.")

        # Do the same for every experiments - but only if you are starting a
        # new folder. Otherwise, this step will actually be done when
        # initializing the likelihood.
        if self.param.find('log.param') == -1:
            for experiment in self.experiments:
                self.read_file(self.param, experiment, separate=True)

        # Finally create all the instances of the Parameter given the input.
        for key, value in self.parameters.iteritems():
            self.mcmc_parameters[key] = Parameter(value, key)

            # When there is no prior edge requested, the syntax consists in setting it to 'None' in the input file.
            # There is also an old syntax which is deprecated: '-1'.
            # We still allow for that, but just after parsing it, we substitute it with 'None'.
            # When the user really wants a prior edge in -1, he can write -1.0, then the next lines will not substitute it.
            for i in [1,2]:
                if (str(self.mcmc_parameters[key]['initial'][i]) == '-1'):
                    self.mcmc_parameters[key]['initial'][i] = None

        """
        Transform from parameters dictionary to mcmc_parameters dictionary of
        instances from the class :class:`parameter` (inheriting from dict)
        """
'''
    def initialise_likelihoods(self, experiments):
        """
        Given an array of experiments, return an ordered dict of instances

        .. Note::

            in the __init__ method, experiments is naturally self.experiments,
            but it is useful to keep it as a parameter, for the case of
            importance sampling.

        """
        print("Enter initialise_likelihoods")
        self.lkl = od()
        # adding the likelihood directory to the path, to import the module
        # then, for each library, calling an instance of the likelihood.
        # Beware, though, if you add new likelihoods, they should go to the
        # folder likelihoods/yourlike/yourlike.py, and contain a yourlike.data,
        # otherwise the following set of commands will not work anymore.

        # For the logging if log_flag is True, each likelihood will log its
        # parameters

        # Due to problems in relative import, this line must be there. Until a
        # better solution is found. It adds the root folder of the MontePython
        # used as the first element in the sys.path
        sys.path.insert(0, self.path['root'])

        for elem in experiments:

            folder = os.path.abspath(os.path.join(
                self.path['MontePython'], "likelihoods", "%s" % elem))
            # add the folder of the likelihood to the path of libraries to...
            # ... import easily the likelihood.py program
            try:
                exec("from likelihoods.%s import %s" % (
                    elem, elem))
            except ImportError as message:
                raise io_mp.ConfigurationError(
                    "Trying to import the %s likelihood" % elem +
                    " as asked in the parameter file, and failed."
                    " Please make sure it is in the `montepython/"
                    "likelihoods` folder, and is a proper python "
                    "module. Check also that the name of the class"
                    " defined in the __init__.py matches the name "
                    "of the folder. In case this is not enough, "
                    "here is the original message: %s\n" % message)
            # Initialize the likelihoods. Depending on the values of
            # command_line and log_flag, the routine will call slightly
            # different things. If log_flag is True, the log.param will be
            # appended.
            try:
                print("self.lkl['%s'] = %s('%s/%s.data',\
                    self, self.command_line)" % (
                    elem, elem, folder, elem))
                exec ("self.lkl['%s'] = %s('%s/%s.data',\
                    self, self.command_line)" % (
                    elem, elem, folder, elem))
            except KeyError as e:
                if e.find('clik') != -1:
                    raise io_mp.ConfigurationError(
                        "You should provide a 'clik' entry in the dictionary "
                        "path defined in the file default.conf")
                else:
                    raise io_mp.ConfigurationError(
                        "The following key: '%s' was not found" % e)

    def read_file(self, param, structure, field='', separate=False):
        """
        Execute all lines concerning the Data class from a parameter file

        All lines starting with `data.` will be replaced by `self.`, so the
        current instance of the class will contain all the information.

        .. note::

            A rstrip() was added at the end, because of an incomprehensible bug
            on some systems that imagined some inexistent characters at the end
            of the line... Now should work

        .. note::

            A security should be added to protect from obvious attacks.

        Parameters
        ----------
        param : str
            Name of the parameter file
        structure : str
            Name of the class entries we want to execute (mainly, data, or any
            other likelihood)

        Keyword Arguments
        -----------------
        field : str
            If nothing is specified, this routine will execute all the lines
            corresponding to the `structure` parameters. If you specify a
            specific field, like `path`, only this field will be read and
            executed.
        separate : bool
            If this flag is set to True, a container class will be created for
            the structure field, so instead of appending to the namespace of
            the data instance, it will append to a sub-namespace named in the
            same way that the desired structure. This is used to extract custom
            values from the likelihoods, allowing to specify values for the
            likelihood directly in the parameter file.

        """
        if separate:
            exec("self.%s = Container()" % structure)
        with open(param, 'r') as param_file:
            for line in param_file:
                if line.find('#') == -1 and line:
                    lhs = line.split('=')[0]
                    if lhs.find(structure+'.') != -1:
                        if field:
                            # If field is not an empty string, you want to skip
                            # the execution of the line (exec statement) if you
                            # do not find the exact searched field
                            if lhs.find('.'.join([structure, field])) == -1:
                                continue
                        if not separate:
                            exec(line.replace(structure+'.', 'self.').rstrip())
                        else:
                            exec(line.replace(
                                structure+'.', 'self.'+structure+'.').rstrip())

    def group_parameters_in_blocks(self):
        """
        Regroup mcmc parameters by blocks of same speed

        This method divides all varying parameters from :attr:`mcmc_parameters`
        into as many categories as there are likelihoods, plus one (the slow
        block of cosmological parameters).

        It creates the attribute :attr:`block_parameters`, to be used in the
        module :mod:`mcmc`.

        .. note::

            It does not compute by any mean the real speed of each parameter,
            instead, every parameter belonging to the same likelihood will
            be considered as fast as its neighbour.

        .. warning::

            It assumes that the nuisance parameters are already written
            sequentially, and grouped together (not necessarily in the order
            described in :attr:`experiments`). If you mix up the different
            nuisance parameters in the .param file, this routine will not
            method as intended. It also assumes that the cosmological
            parameters are written at the beginning of the file.

        """
        array = []
        # First obvious block is all cosmological parameters
        array.append(len(self.get_mcmc_parameters(['varying', 'cosmo'])))
        # Then, store all nuisance parameters
        nuisance = self.get_mcmc_parameters(['varying', 'nuisance'])

        # Create an array to keep track of the already taken into account
        # nuisance parameters. This will come in handy when using likelihoods
        # that share some nuisance parameters.
        used_nuisance = []
        for likelihood in self.lkl.itervalues():
            count = 0
            for elem in nuisance:
                if elem in likelihood.nuisance:
                    if elem not in used_nuisance:
                        count += 1
                        used_nuisance.append(elem)
            likelihood.varying_nuisance_parameters = count

        # Then circle through them
        index = 0
        while index < len(nuisance):
            elem = nuisance[index]
            flag = False
            # For each one, check if they belong to a likelihood
            for likelihood in self.lkl.itervalues():
                if (elem in likelihood.nuisance) and (index < len(nuisance)):
                    # If yes, store the number of nuisance parameters needed
                    # for this likelihood.
                    flag = True
                    array.append(
                        likelihood.varying_nuisance_parameters+array[-1])
                    index += likelihood.varying_nuisance_parameters
                    continue
            if not flag:
                # If the loop reaches this part, it means this nuisance
                # parameter was associated with no likelihood: this should not
                # happen
                raise io_mp.ConfigurationError(
                    "nuisance parameter %s " % elem +
                    "is associated to no likelihood")
        # Store the result
        self.block_parameters = array

        # Setting a default value for the over_sampling array
        if not self.over_sampling:
            self.over_sampling = [1 for _ in range(len(self.block_parameters))]
        # Test that the over_sampling list has the same size as
        # block_parameters.
        else:
            try:
                assert len(self.block_parameters) == len(self.over_sampling)
            except AssertionError:
                raise io_mp.ConfigurationError(
                    "The length of the over_sampling field should be"
                    " equal to the number of blocks (one for cosmological "
                    "parameters, plus one for each likelihood with "
                    "nuisance parameters)")

        # Create a list of indices corresponding of the oversampling strategy
        self.assign_over_sampling_indices()

    def assign_over_sampling_indices(self):
        """
        Create the list of varied parameters given the oversampling
        """
        self.over_sampling_indices = []
        for index in range(len(self.get_mcmc_parameters(['varying']))):
            if index == 0:
                self.over_sampling_indices.append(index)
            else:
                block_index = self.block_parameters.index(
                    [i for i in self.block_parameters if index < i][0])
                for _ in range(self.over_sampling[block_index]):
                    self.over_sampling_indices.append(index)

    def read_version(self, param_file):
        """
        Extract version and subversion from an existing log.param
        """
        # Read the first line (cosmological code version)
        first_line = param_file.readline()
        param_file.seek(0)
        regexp = re.match(
            ".*\(branch: (.*), hash: (.*)\).*",
            first_line)
        version = first_line.split()[1]
        git_branch, git_version = regexp.groups()
        return version, git_version, git_branch

    def get_mcmc_parameters(self, table_of_strings):
        """
        Returns an ordered array of parameter names filtered by
        `table_of_strings`.

        Parameters
        ----------
        table_of_strings : list
            List of strings whose role and status must be matched by a
            parameter. For instance,

            >>> data.get_mcmc_parameters(['varying'])
            ['omega_b', 'h', 'amplitude', 'other']

            will return a list of all the varying parameters, both
            cosmological and nuisance ones (derived parameters being `fixed`,
            they wont be part of this list). Instead,

            >>> data.get_mcmc_parameters(['nuisance', 'varying'])
            ['amplitude', 'other']

            will only return the nuisance parameters that are being varied.

        """
        table = []
        for key, value in self.mcmc_parameters.iteritems():
            number = 0
            for subvalue in value.itervalues():
                for string in table_of_strings:
                    if subvalue == string:
                        number += 1
            if number == len(table_of_strings):
                table.append(key)
        return table

    def check_for_slow_step(self, new_step):
        """
        Check whether the value of cosmological parameters were
        changed, and if no, skip computation of the cosmology.

        """
        parameter_names = self.get_mcmc_parameters(['varying'])
        cosmo_names = self.get_mcmc_parameters(['cosmo'])

        need_change = 0

        # For all elements in the varying parameters:
        for elem in parameter_names:
            i = parameter_names.index(elem)
            # If it is a cosmological parameter
            if elem in cosmo_names:
                if self.mcmc_parameters[elem]['current'] != new_step[i]:
                    need_change += 1

        # If any cosmological value was changed,
        if need_change > 0:
            self.need_cosmo_update = True
        else:
            self.need_cosmo_update = False

        for likelihood in self.lkl.itervalues():
            # If the cosmology changed, you need to recompute the likelihood
            # anyway
            if self.need_cosmo_update:
                likelihood.need_update = True
                continue
            # Otherwise, check if the nuisance parameters of this likelihood
            # were changed
            need_change = 0
            for elem in parameter_names:
                i = parameter_names.index(elem)
                if elem in likelihood.nuisance:
                    if self.mcmc_parameters[elem]['current'] != new_step[i]:
                        need_change += 1
            if need_change > 0:
                likelihood.need_update = True
            else:
                likelihood.need_update = False

    def update_cosmo_arguments(self):
        """
        Put in :attr:`cosmo_arguments` the current values of
        :attr:`mcmc_parameters`

        This method is called at every step in the Markov chain, to update the
        dictionary. In the Markov chain, the scale is not remembered, so one
        has to apply it before giving it to the cosmological code.

        .. note::

            When you want to define new parameters in the Markov chain that do
            not have a one to one correspondance to a cosmological name, you
            can redefine its behaviour here. You will find in the source
            several such examples.

        .. note::

            For complex CLASS parameters, that expect a string of numbers
            separated with commas, you can now use the name of the argument,
            for instance :code:`m_ncdm`, then append a double underscore and a
            number. So if you run with two cosmological parameters,
            :code:`m_ncdm__1` and :code:`m_ncdm__2`, this function will
            automatically concatenate the two and feed class :code:`m_ncdm`.
            You still have to make sure that the other variables are properly
            set, like :code:`N_ncdm` to 2, in this example.

        """
        # For all elements in any cosmological parameters
        for elem in self.get_mcmc_parameters(['cosmo']):
            # Fill in the dictionnary with the current value of parameters
            self.cosmo_arguments[elem] = \
                self.mcmc_parameters[elem]['current'] *\
                self.mcmc_parameters[elem]['scale']

        # For all elements in the cosmological parameters from the mcmc list,
        # translate any-one that is not directly a CLASS parameter into one.
        # The try: except: syntax ensures that the first call
        for elem in self.get_mcmc_parameters(['cosmo']):
            # infer h from Omega_Lambda and delete Omega_Lambda
            if elem == 'Omega_Lambda':
                omega_b = self.cosmo_arguments['omega_b']
                omega_cdm = self.cosmo_arguments['omega_cdm']
                Omega_Lambda = self.cosmo_arguments['Omega_Lambda']
                self.cosmo_arguments['h'] = math.sqrt(
                    (omega_b+omega_cdm) / (1.-Omega_Lambda))
                del self.cosmo_arguments[elem]
            # infer omega_cdm from Omega_L and delete Omega_L
            elif elem == 'Omega_L':
                omega_b = self.cosmo_arguments['omega_b']
                h = self.cosmo_arguments['h']
                Omega_L = self.cosmo_arguments['Omega_L']
                self.cosmo_arguments['omega_cdm'] = (1.-Omega_L)*h*h-omega_b
                del self.cosmo_arguments[elem]
            # infer omega_cdm from omega_m (assuming one standard massive neutrino and omega_nu=m_nu/93.14) and delete omega_m
            elif elem == 'omega_m':
                omega_b = self.cosmo_arguments['omega_b']
                omega_m = self.cosmo_arguments['omega_m']
                try:
                    omega_nu = self.cosmo_arguments['m_ncdm'] / 93.14
                except:
                    omega_nu = 0.
                self.cosmo_arguments['omega_cdm'] = omega_m - omega_b - omega_nu
                del self.cosmo_arguments[elem]
            elif elem == 'ln10^{10}A_s':
                self.cosmo_arguments['A_s'] = math.exp(
                    self.cosmo_arguments[elem]) / 1.e10
                del self.cosmo_arguments[elem]
            elif elem == 'exp_m_2_tau_As':
                tau_reio = self.cosmo_arguments['tau_reio']
                self.cosmo_arguments['A_s'] = self.cosmo_arguments[elem] * \
                    math.exp(2.*tau_reio)
                del self.cosmo_arguments[elem]
            elif elem == 'f_cdi':
                self.cosmo_arguments['n_cdi'] = self.cosmo_arguments['n_s']
            elif elem == 'beta':
                self.cosmo_arguments['alpha'] = 2.*self.cosmo_arguments['beta']
            elif elem == 'M_tot_NH' or elem == '{\sum}m_nu_NH':
                # By T. Brinckmann
                # Normal hierarchy massive neutrinos. Calculates the individual
                # neutrino masses from M_tot_NH and deletes M_tot_NH
                if not self.cosmo_arguments['N_ncdm'] == 3:
                    raise ValueError(
                        "N_ncdm is not equal to 3."
                        " This value should be exactly 3.")
                # From Esteban et al. 2016: https://arxiv.org/abs/1611.01514
                delta_m_squared_atm=2.524e-3 #2.45e-3
                delta_m_squared_sol=7.50e-5 #7.50e-5
                #m1_func = lambda m1, M_tot, d_m_sq_atm, d_m_sq_sol: M_tot**2. + 0.5*d_m_sq_sol - d_m_sq_atm + m1**2. - 2.*M_tot*m1 - 2.*M_tot*(d_m_sq_sol+m1**2.)**0.5 + 2.*m1*(d_m_sq_sol+m1**2.)**0.5
                m1_func = lambda m1, M_tot, d_m_sq_atm, d_m_sq_sol: M_tot - m1 - (d_m_sq_sol + m1**2.)**0.5 - (d_m_sq_atm + m1**2.)**0.5
                m1,opt_output,success,output_message = fsolve(m1_func,self.cosmo_arguments[elem]/3.,(self.cosmo_arguments[elem],delta_m_squared_atm,delta_m_squared_sol),full_output=True)
                if not success == 1:
                    raise ValueError(
                        "Failed to estimate m1. Reason: "+output_message+
                        " Exiting run.")
                m1 = m1[0]
                m2 = (delta_m_squared_sol + m1**2.)**0.5
                #m3 = (delta_m_squared_atm + 0.5*(m2**2. + m1**2.))**0.5
                m3 = (delta_m_squared_atm + m1**2.)**0.5
                if m1+m2+m3 > self.cosmo_arguments[elem]+0.001*self.cosmo_arguments[elem]:
                    raise ValueError(
                        "Failed to estimate m1 resulting in sum(m_i) > M_tot."
                        " Exiting run.")
                self.cosmo_arguments['m_ncdm'] = r'%g, %g, %g' % (m1,m2,m3)
                del self.cosmo_arguments[elem]
            elif elem == 'M_tot_IH'or elem == '{\sum}m_nu_IH':
                # By T. Brinckmann
                # Inverted hierarchy massive neutrinos. Calculates the individual
                # neutrino masses from M_tot_IH and deletes M_tot_IH
                if not self.cosmo_arguments['N_ncdm'] == 3:
                    raise ValueError(
                        "N_ncdm is not equal to 3."
                        " This value should be exactly 3.")
                # From Esteban et al. 2016: https://arxiv.org/abs/1611.01514
                delta_m_squared_atm=-2.514e-3 #-2.45e-3
                delta_m_squared_sol=7.50e-5 #7.50e-5
                #m1_func = lambda m1, M_tot, d_m_sq_atm, d_m_sq_sol: M_tot**2. + 0.5*d_m_sq_sol - d_m_sq_atm + m1**2. - 2.*M_tot*m1 - 2.*M_tot*(d_m_sq_sol+m1**2.)**0.5 + 2.*m1*(d_m_sq_sol+m1**2.)**0.5
                m1_func = lambda m1, M_tot, d_m_sq_atm, d_m_sq_sol: M_tot - m1 - (d_m_sq_sol + m1**2.)**0.5 - (abs(d_m_sq_atm + d_m_sq_sol + m1**2.))**0.5
                m1,opt_output,success,output_message = fsolve(m1_func,self.cosmo_arguments[elem]/2.,(self.cosmo_arguments[elem],delta_m_squared_atm,delta_m_squared_sol),full_output=True)
                if not success == 1:
                    raise ValueError(
                        "Failed to estimate m1. Reason: "+output_message+
                        " Exiting run.")
                m1 = m1[0]
                m2 = (delta_m_squared_sol + m1**2.)**0.5
                #m3 = (delta_m_squared_atm + 0.5*(m2**2. + m1**2.))**0.5
                m3 = (delta_m_squared_atm + m2**2.)**0.5
                if m1+m2+m3 > self.cosmo_arguments[elem]+0.001*self.cosmo_arguments[elem]:
                    raise ValueError(
                        "Failed to estimate m1 resulting in sum(m_i) > M_tot."
                        "Exiting run.")
                if delta_m_squared_atm + delta_m_squared_sol + m1**2. < 0.:
                    raise ValueError(
                        "Failed to correctly estimate m1. Found m1^2 = %f < %f,"
                        "but m1^2 should always be greater than this value." % (m1**2.,- delta_m_squared_sol - delta_m_squared_atm))
                self.cosmo_arguments['m_ncdm'] = r'%g, %g, %g' % (m1,m2,m3)
                del self.cosmo_arguments[elem]
            elif elem == 'M_tot' or elem == '{\sum}m_nu':
                # By T. Brinckmann
                # Massive neutrinos with identical non-zero mass. Calculates the
                # individual neutrino masses from M_tot and deletes M_tot
                if not self.cosmo_arguments['N_ncdm'] == 1:
                    raise ValueError(
                        "N_ncdm is not equal to 1."
                        " This value should be exactly 1.")
                self.cosmo_arguments['m_ncdm'] = self.cosmo_arguments[elem]/self.cosmo_arguments['deg_ncdm']
                del self.cosmo_arguments[elem]
            elif elem == 'm_s_eff':
                # By T. Brinckmann
                # conversion from effective sterile neutrino mass to physical sterile neutrino mass, assuming that this
                # is the ncdm species number 2 and that it is Dodelson-Widrow like (i.e same temperature as active neutrinos)
                #print self.cosmo_arguments
                #self.cosmo_arguments['m_ncdm__2'] = self.cosmo_arguments['deg_ncdm__2']*self.cosmo_arguments[elem]
                m_s_eff = self.cosmo_arguments[elem]/self.cosmo_arguments['deg_ncdm__2']
                self.cosmo_arguments['m_ncdm'] = r'%g, %g' % (float(self.cosmo_arguments['m_ncdm']), m_s_eff)
                del self.cosmo_arguments[elem]
            elif elem == 'log10N_dg':
                self.cosmo_arguments['N_dg'] = 10**(self.cosmo_arguments[elem])
                del self.cosmo_arguments[elem]
            elif elem == 'log10fn':
                self.cosmo_arguments['f_nadm'] = 10**(self.cosmo_arguments[elem])
                del self.cosmo_arguments[elem]
            elif elem == 'log10Gamma':
                self.cosmo_arguments['invtau0_nadm_dg'] = 10**(self.cosmo_arguments[elem])
                del self.cosmo_arguments[elem]
            elif elem == 'w0wa':
                self.cosmo_arguments['wa_fld'] = self.cosmo_arguments[elem] - self.cosmo_arguments['w0_fld']
                del self.cosmo_arguments[elem]

            # Finally, deal with all the parameters ending with __i, where i is
            # an integer. Replace them all with their name without the trailing
            # double underscore, concatenated with each other. The test is
            # always on the one ending with __1, as it will be the first on the
            # list, and deal with all the others.
            elif re.search(r'__1', elem):
                original_name = re.search(r'(.*)__1', elem).groups()[0]
                # Recover the values of all the other elements
                values = [self.cosmo_arguments[elem]]
                for other_elem in self.get_mcmc_parameters(['cosmo']):
                    match = re.search(r'%s__([2-9])' % original_name,
                                      other_elem)
                    if match:
                        values.append(self.cosmo_arguments[other_elem])
                # create the cosmo_argument
                self.cosmo_arguments[original_name] = ', '.join(
                    ['%g' % value for value in values])
                # Delete the now obsolete entries of the dictionary
                for index in range(1, len(values)+1):
                    del self.cosmo_arguments[
                        original_name + '__%i' % index]
    @staticmethod
    def folder_is_initialised(folder):
        """
        Static method to call for checking if a folder was already initialised

        This method can be used to speed up the mpi initialisation in
        :mod:`run`. If a process finds that the folder is already a proper
        Monte Python one, it sends directly a 'go' signal to its next in line.

        .. warning::

            This method assumes that the last lines of the log.param are the
            path indication. If this would ever change, adjust this method
            accordingly.

        """
        # If the folder is not there, easy answer: False!
        if not os.path.isdir(folder):
            return False
        # Recover the log.param from the folder, and assert it exists
        log_param_path = os.path.join(folder, 'log.param')
        if not os.path.isfile(log_param_path):
            return False
        # Quickly load it to a string, and assert that the path has been
        # written (which are the last lines)
        with open(log_param_path, 'r') as log_param:
            text = log_param.readlines()
            if text[-1].find('path[') != -1:
                return True
            else:
                return False

    def __cmp__(self, other):
        """
        Redefinition of the 'compare' method for two instances of this class.

        It will decide which basic operations to perform when the code asked if
        two instances are the same (in case you want to launch a new chain in
        an existing folder, with your own parameter file) Comparing
        cosmological code versions (warning only, will not fail the comparison)

        """
        if self.version != other.version:
            warnings.warn(
                "You are running with a different version of your " +
                "cosmological code")

        # Defines unordered version of the dictionaries of parameters
        self.uo_parameters = {}
        other.uo_parameters = {}

        # Check if all the experiments are tested again,
        if len(list(set(other.experiments).symmetric_difference(
                set(self.experiments)))) == 0:
            # Check that they have been called with the same .data file, stored
            # in dictionary when initializing.
            for experiment in self.experiments:
                for elem in self.lkl[experiment].dictionary:
                    if self.lkl[experiment].dictionary[elem] != \
                            other.lkl[experiment].dictionary[elem]:
                        print ('in your parameter file: ')
                        print (self.lkl[experiment].dictionary)
                        print ('in log.param:           ')
                        print (other.lkl[experiment].dictionary)
                        return -1
            # Fill in the unordered version of dictionaries
            for key, elem in self.mcmc_parameters.iteritems():
                self.uo_parameters[key] = elem['initial']
            for key, elem in other.mcmc_parameters.iteritems():
                other.uo_parameters[key] = elem['initial']

            # And finally compare them (standard comparison between
            # dictionnaries, will return True if both have the same keys and
            # values associated to them.
            return cmp(self.uo_parameters, other.uo_parameters)
        else:
            return -1

    def __call__(self, ctx):
        """
        Interface layer with CosmoHammer

        Store quantities to a the context, to be accessed by the Cosmo Module
        and each of the likelihoods.

        Parameters
        ----------
        ctx : context
                Contains several dictionaries storing data and cosmological
                information

        """
        # Recover the cosmological parameter value from the context
        parameters = ctx.getParams()

        # Storing them as current points
        for index, elem in enumerate(self.get_mcmc_parameters(["varying"])):
            self.mcmc_parameters[elem]['current'] = parameters[index]

        # Propagating this to the cosmo_arguments dictionary
        self.update_cosmo_arguments()

        # Store itself into the context
        ctx.add('data', self)


def get_availible_likelihoods(backendDir):
    ''' Function that reads and returns a list of all folder names in the MontePython/montepython/likelihoods folder.
        The output is used in GAMBIT to check if the user requested to use a likelihood which is actually not availible
        in the installed version of MontePython. 
        
        Input:
        ------
        str backendDir: string containing backend directory of MontePython

        Output:
        -------
        list output: list of strings containing the names of available likelihoods
    '''
    output = [dI for dI in os.listdir(backendDir+"/likelihoods/") if os.path.isdir(os.path.join(backendDir+'/likelihoods/',dI))]

    return output