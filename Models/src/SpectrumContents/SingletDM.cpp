//   GAMBIT: Global and Modular BSM Inference Tool
//   *********************************************
///  \file
///
///  Class defining the parameters that SubSpectrum 
///  objects providing Scalar Singlet Dark Matter
///  spectrum data must provide
///
///  *********************************************
///
///  Authors: 
///  <!-- add name and date if you modify -->
///   
///  \author Ben Farmer
///          (benjamin.farmer@fysik.su.se)
///  \date 2016 Feb
///
///
///  \author James McKay
///          (j.mckay14@imperial.ac.uk)
///  \date 2016 Mar
///
///  *********************************************

#ifndef __singlet_DM_contents_hpp__
#define __singlet_DM_contents_hpp__

#include "gambit/Models/SpectrumContents/RegisteredSpectra.hpp"

namespace Gambit {

  SpectrumContents::SingletDM::SingletDM()
  {
     setName("SingletDM");


     addParameter(Par::mass1, "vev"      );
     addParameter(Par::dimensionless, "lambda_hS");
     addParameter(Par::dimensionless, "lambda_S");
     addParameter(Par::dimensionless, "lambda_h");

     addParameter(Par::Pole_Mass, "h0");
     addParameter(Par::Pole_Mass, "S" );
  }

}
#endif