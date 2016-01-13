//  GAMBIT: Global and Modular BSM Inference Tool
//  *********************************************
///  \file
///
///  Scanner method implementations.
///
///  *********************************************
///
///  Authors (add name and date if you modify):
///   
///  \author Christoph Weniger
///          (c.weniger@uva.nl)
///  \date 2013 May, June, July
//
///  \author Gregory Martinez
///          (gregory.david.martinez@gmail.com)
///  \date 2013 July 2013/Feb 2014
///
///  \author Pat Scott
///          (patscott@physics.mcgill.ca)
///  \date 2013 Aug
///
///  *********************************************

#ifndef __scan_hpp__
#define __scan_hpp__

#include "gambit/ScannerBit/printer_interface.hpp"
#include "gambit/ScannerBit/factory_defs.hpp"
#include "gambit/ScannerBit/priors/composite.hpp"
#include "gambit/Utils/yaml_options.hpp"

namespace Gambit
{
        namespace Scanner
        {       
                class Scan_Manager
                {
                  private:
                        const Factory_Base *factory;
                        const Options options;
                        const Priors::CompositePrior *prior;
                        printer_interface *printerInterface;
                        // Flag to indicate whether or not the prior and factory need deleting in the destructor.  Do not reset!
                        bool has_local_prior_and_factory;

                  public:
                        Scan_Manager (const Factory_Base*, const Options, const Priors::CompositePrior*, printer_interface* = 0);
                        ~Scan_Manager();
                        int Run();                       
                };             
        }
}

#endif
