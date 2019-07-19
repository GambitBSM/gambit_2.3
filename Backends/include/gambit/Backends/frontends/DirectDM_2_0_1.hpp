//   GAMBIT: Global and Modular BSM Inference Tool
//   *********************************************
///  \file
///
///  Frontend header for the DirectDM backend.
///
///  *********************************************
///
///  Authors (add name and date if you modify):
///
///  \author Sanjay Bloor
///          (sanjay.bloor12@imperial.ac.uk)
///  \date 2018 Sep, Oct
///
///  *********************************************

#define BACKENDNAME DirectDM
#define BACKENDLANG Python
#define VERSION 2.0.1
#define SAFE_VERSION 2_0_1

LOAD_LIBRARY

// Forward declaration of custom return type (defined in gambit/Backends/backend_types/DDCalc.hpp)
namespace Gambit { class NREO_DM_nucleon_couplings; }

BE_CONV_FUNCTION(get_NR_WCs_flav, NREO_DM_nucleon_couplings, (map_str_dbl&, double&, int&, std::string&), "get_NR_WCs_flav")
BE_CONV_FUNCTION(get_NR_WCs_EW, NREO_DM_nucleon_couplings, (map_str_dbl&, double&, double&, double&, double&, std::string&), "get_NR_WCs_EW")

// Undefine macros to avoid conflict with other backends
#include "gambit/Backends/backend_undefs.hpp"
