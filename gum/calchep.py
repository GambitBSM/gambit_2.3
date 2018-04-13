"""
Master module for all CalcHEP related routines.
"""

import argparse
import os
import shutil
import re
import datetime
import numpy as np
from setup import *

def clean(line):
    """
    Replaces an expression for a parameter with the number 1. GAMBIT
    will set the correct value anyway, during CalcHEP initialisation.
    """

    return line.replace(line.split('|')[1], "1\n")


def clean_calchep_model_files(model_folder, model_name):
    """
    Makes CalcHEP .mdl files GAMBIT-friendly, and moves them to the
    CalcHEP backend folder.
    """
    
    model_folder.strip('/')
    model_name.strip('/')

    # If the model folder exists
    if os.path.exists(model_folder):

        files = [f for f in os.listdir(model_folder) if f.endswith(".mdl")]

        needed_files = ["func1.mdl", "lgrng1.mdl", "prtcls1.mdl", "vars1.mdl"]

        # Check that all needed files are present in the directory
        if set(needed_files) <= set(files):
            print("All CalcHEP model files found - let's go.")

        else:
            raise GumError(("ERROR: directory present but does not "
                            "contain all 4 of these files:\n" 
                            + needed_files + 
                            "Please check that all model files are "
                            "present, and are numbered 1."))
        ## extlib1.mdl

        # Delete any extlib files; we won't be using anything
        if "extlib1.mdl" in files:
            os.remove(model_folder + "/extlib1.mdl")

        extlib = open(model_folder + "extlib1.mdl", "w+")

        extlib.writelines([model_name, "\nLibraries",
                           "\nExternal libraries                               "
                           "                             <|",
                           "\n================================================"
                           "================================"])

        extlib.close()

        ## vars1.mdl

        # Create an empty, temporary file to copy parameters into
        vars = open(model_folder + "/vars1.mdl", "r")
        temp = open(model_folder + "/temp1.mdl", "w")
        lines = vars.readlines()
        vars.seek(0)

        # Leave everything here - we want access to them from GAMBIT.
        for line in lines:
            temp.write(line)

        # Close
        vars.close()

        # Save old vars
        os.rename(model_folder + "/vars1.mdl", model_folder + "/vars1_old.mdl")

        ## func1.mdl ##
        #  Move masses, mixing matrices, etc. -> vars1.mdl, to be set
        # manually. ("Independent parameters"). Only these are allowed to be
        # changed by CalcHEP's internal function, "assignVal[W]".

        # Read in func1.mdl line by line, to parse on case-by-case basis.
        func = open(model_folder + "/func1.mdl", "r")
        lines = func.readlines()
        func.seek(0)

        # Create a new temporary file, for func1.mdl vertices, etc.
        # ("Dependent parameters")
        temp2 = open(model_folder + "/temp2.mdl", "w")

        for line in lines:
            # Split each string to make life easier
            first_entry = re.split("\s+", line)[0]

            # If there is a "read" dependency, do not write it over to temp2.mdl
            if re.match("rd", first_entry):
                pass

            # If it's commented out, nuke it.
            elif first_entry.startswith("%"):
                pass

            # Replace slhaVal calls with just the number 1. These will ALL be
            # set by GAMBIT so their value is purely arbitrary.
            elif "slhaVal" in line:

                ##  MASSES

                # 'M' -> Mass from SARAH output, and "MASS" expected
                # in block (protection just in case)
                if re.match("M", first_entry[0]) and "MASS" in line:
                    temp.write(clean(line))

                # Mu for Higgs mixing
                elif re.match("Mu", first_entry) and "HMIX" in line:
                    temp.write(clean(line))

                ## Coupling constants

                # l_ABC -> coupling between fields A, B, C
                elif re.match("l_\w{1,}", first_entry):
                    temp.write(clean(line))

                # mu_AB -> coupling between fields A, B
                elif re.match("mu_\w{1,}", first_entry):
                    temp.write(clean(line))

                ## Phases

                # Higgs vevs -> beta
                elif re.match("betaH", first_entry):
                    temp.write(clean(line))

                # Higgs alignment -> alpha
                elif re.match("alphaH", first_entry):
                    temp.write(clean(line))

                # Gluino phase (???)
                elif re.match("pG", first_entry):
                    temp.write(clean(line))

            ## /(if slhaVal in line)

            # W mass - since CalcHEP uses tree-level relation to MZ, GF
            # & alphainv. GAMBIT uses measured value.

            elif re.match("MWp", first_entry) or re.match("MWm", first_entry):
                temp.write(clean(line))

            # Weinberg angle - again, CalcHEP uses tree-level relation.
            # (Same definition as GAMBIT, but for different MW...? Weirdly.)
            elif re.match("TW", first_entry):
                temp.write(clean(line))

            # Only want g3 of the SM coupling constants.
            elif re.match("g3", first_entry):
                temp.write(clean(line))

            # If no criteria has been matched - go ahead. For example,
            # vertices & variables defined internally, e.g. Higgs self coupling
            # lambda_h = 0.5*mH^2/v^2.
            else:
                temp2.write(line)

        # Done - tidy up and close.
        temp2.truncate()
        temp.truncate()
        temp.close()
        temp.close()
        func.close()

        # Copy temp into func
        os.rename(model_folder + "/func1.mdl", model_folder + "/func1_old.mdl")
        os.rename(model_folder + "/temp1.mdl", model_folder + "/vars1.mdl")
        os.rename(model_folder + "/temp2.mdl", model_folder + "/func1.mdl")

        # We do not touch Lagrangian / particle files.
        # They're perfect just the way they are.

        print("CalcHEP model files cleaned!")
        
        # TODO - move CalcHEP files to backend folder.

    # If the model folder does not exist
    else:
      raise GumError("CalcHEP model folder " + model_folder + " not found.")


def extract_particles(model_folder, model_name):
    """
    Extract list of all non-SM particles from CalcHEP files. NOTE: The
    Higgs is considered 'BSM' in GAMBIT, in light of SUSY, 2HDMs, etc.
    """

    standard_model_pdgs = {1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6, 11, -11,
                           12, -12, 13, -13, 14, -14, 15, -15, 16, -16, 21, 22,
                           23, 24, -24}

    bsm_particles = []

    with open(model_folder + "/prtcls1.mdl", "r") as prtcls:

        # Trim the unuseful information such as model name etc. from the top
        for i in xrange(3):
            next(prtcls)

        for line in prtcls:

            # Read in particle list & rid of whitespace
            parts = [i.strip(' ') for i in line.split('|')]
            # If the PDG code is in Standard Model, it's not BSM. Pass.
            if int(parts[3]) in standard_model_pdgs:
                pass
            else:
                # Check to see if new particle has a distinct
                # antiparticle.
                if parts[1] == parts[2]:
                    self_conj = True
                else:
                    self_conj = False
                # Charge not obtained from here. Set to 0.
                newParticle = Particle(chargex3=0, spinx2=int(parts[4]),
                                       pdg_code=int(parts[3]),
                                       own_conjugate=self_conj)
                bsm_particles.append(newParticle)

    bsm_particles[:] = list(set(bsm_particles))

    return np.array(bsm_particles)

def has_ghosts(string):
  """
  Returns True if there is a ghost/auxiliary field in the interaction.
  """

  for i in range(0, len(string)):
    if (string[i].endswith(".f")
    or  string[i].endswith(".c")
    or  string[i].endswith(".C")
    or  string[i].endswith(".t")):
      return True

  return False

def convert(vertex, PDG_conversion):
  """
  Swaps field names for PDG codes for a vertex (list object).
  """

  for particleName, PDGcode in PDG_conversion.iteritems():
    for i in range(0, len(vertex)):
      if vertex[i] == particleName:
        vertex[i] = PDGcode

def get_vertices(foldername):
  """
  Pulls all vertices from a CalcHEP model file by PDG code.
  """

  # Check the folder exists
  if os.path.exists(foldername):

    # Array of particle + PDG code
    particle_PDG_conversion = {}

    # Now take in information from particles file to convert interactions to PDG codes
    with open(foldername + "/prtcls1.mdl") as prtcls:

      # Trim the unuseful information such as model name etc. from the beginning
      for i in xrange(3):
        next(prtcls)

      for line in prtcls:

        # Read in particle list & rid of whitespace
        parts = [i.strip(' ') for i in line.split('|')]

        # Add particle + code
        particle_PDG_conversion[parts[1]] = int(parts[3])

        # Is a particle it's own antiparticle?
        if parts[1] != parts[2]:

          # If so, add the antiparticle separately
          particle_PDG_conversion[parts[2]] = int('-' +  parts[3])

    lines = []
    interactions = []

    # Set of SM PDG codes.
    standard_model_PDGs = set([1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6,
                               11, -11, 12, -12, 13, -13, 14, -14, 15,
                               -15, 16, -16, 21, 22, 23, 24, -24, 25])

    # Open file containing vertices, and read the vertices in.
    with open(foldername + "/lgrng1.mdl") as lgrng:

      # Trim the model etc. from the beginning
      for i in xrange(3):
        next(lgrng)

      # Read in line-by-line.
      for line in lgrng:
        x = [i.strip(' ') for i in line.split('|')]

        # All interactions should have 4 particles or fewer.
        if len(x) > 4:

          # Check for ghosts - not useful for pheno
          if has_ghosts(x) == False:

            # Create instance of vertex class
            interaction = Vertex()

            # If 4th column is empty -> 3 point int
            if x[3] == '':
              interaction.particles += x[0:3]
            else:
              interaction.particles += x[0:4]

            # Add to list of interactions
            interactions.append(interaction)

    for i in range(0, len(interactions)):

      # Convert all interactions to PDG codes for universality
      convert(interactions[i].particles, particle_PDG_conversion)

      # Tag if SM or not
      if set(interactions[i].particles) <= standard_model_PDGs:
        interactions[i].SM = True
      else:
        interactions[i].SM = False

    return interactions, particle_PDG_conversion

  # If the model folder does not exist
  else:
    raise GumError("ERROR: CalcHEP Model folder " + foldername + " not found.")
