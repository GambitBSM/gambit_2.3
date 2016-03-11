//   GAMBIT: Global and Modular BSM Inference Tool
//   *********************************************
///  \file                                       
///                                               
///  List of types which are printable by GAMBIT printers
///  NO LONGER AUTOMATICALLY GENERATED! Manually update this
///  list when you want to add a new printable type.
///                                               
///  *********************************************
///                                               
///  Authors:                                     
///                                               
///  \author Ben Farmer
///          (benjamin.farmer@fysik.su.se)
///  \date 2016 Jan
///                                               
///  *********************************************
                                                  
#ifndef __printable_types_hpp__                 
#define __printable_types_hpp__                 

#include <map>
#include "gambit/Utils/model_parameters.hpp"

typedef unsigned int uint;
typedef unsigned long ulong;
typedef std::map<std::string,double> map_str_dbl; // can't have commas in macro input
 
#define PRINTABLE_TYPES  \
(bool)                   \
(int)(uint)(long)(ulong) \
(float)(double)          \
(std::vector<bool>)      \
(std::vector<int>)       \
(std::vector<double>)    \
(ModelParameters)        \
(triplet<double>)        \
(map_str_dbl)            \

#endif // defined __printable_types_hpp__
