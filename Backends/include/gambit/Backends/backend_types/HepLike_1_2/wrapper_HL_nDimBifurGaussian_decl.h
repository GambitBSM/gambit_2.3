#ifndef __wrapper_HL_nDimBifurGaussian_decl_HepLike_1_2_h__
#define __wrapper_HL_nDimBifurGaussian_decl_HepLike_1_2_h__

#include <cstddef>
#include <string>
#include <vector>
#include "forward_decls_wrapper_classes.h"
#include "gambit/Backends/wrapperbase.hpp"
#include "abstract_HL_nDimBifurGaussian.h"
#include "wrapper_HL_Data_decl.h"
#include <boost/numeric/ublas/matrix.hpp>

#include "identification.hpp"

namespace CAT_3(BACKENDNAME,_,SAFE_VERSION)
{
   
   
   class HL_nDimBifurGaussian : public HL_Data
   {
         // Member variables: 
      public:
         // -- Static factory pointers: 
         static Abstract_HL_nDimBifurGaussian* (*__factory0)();
         static Abstract_HL_nDimBifurGaussian* (*__factory1)(::std::basic_string<char>);
   
         // -- Other member variables: 
   
         // Member functions: 
      public:
         void Read();
   
         double GetChi2(::std::vector<double> theory);
   
         double GetLikelihood(::std::vector<double> theory);
   
         double GetLogLikelihood(::std::vector<double> theory);
   
         double GetChi2(::std::vector<double> theory, ::boost::numeric::ublas::matrix<double> theory_cov);
   
         double GetLikelihood(::std::vector<double> theory, ::boost::numeric::ublas::matrix<double> theory_cov);
   
         double GetLogLikelihood(::std::vector<double> theory, ::boost::numeric::ublas::matrix<double> theory_cov);
   
         bool Restrict(::std::vector<std::basic_string<char>> arg_1);
   
         ::std::vector<std::basic_string<char>> GetObservables();
   
   
         // Wrappers for original constructors: 
      public:
         HL_nDimBifurGaussian();
         HL_nDimBifurGaussian(::std::basic_string<char> s);
   
         // Special pointer-based constructor: 
         HL_nDimBifurGaussian(Abstract_HL_nDimBifurGaussian* in);
   
         // Copy constructor: 
         HL_nDimBifurGaussian(const HL_nDimBifurGaussian& in);
   
         // Assignment operator: 
         HL_nDimBifurGaussian& operator=(const HL_nDimBifurGaussian& in);
   
         // Destructor: 
         ~HL_nDimBifurGaussian();
   
         // Returns correctly casted pointer to Abstract class: 
         Abstract_HL_nDimBifurGaussian* get_BEptr() const;
   
   };
   
}


#include "gambit/Backends/backend_undefs.hpp"

#endif /* __wrapper_HL_nDimBifurGaussian_decl_HepLike_1_2_h__ */
