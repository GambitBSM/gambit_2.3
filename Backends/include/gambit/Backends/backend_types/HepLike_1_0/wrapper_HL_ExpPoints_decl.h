#ifndef __wrapper_HL_ExpPoints_decl_HepLike_1_0_h__
#define __wrapper_HL_ExpPoints_decl_HepLike_1_0_h__

#include <cstddef>
#include "forward_decls_wrapper_classes.h"
#include "gambit/Backends/wrapperbase.hpp"
#include "abstract_HL_ExpPoints.h"
#include "wrapper_HL_Data_decl.h"
#include <string>
#include <vector>

#include "identification.hpp"

namespace CAT_3(BACKENDNAME,_,SAFE_VERSION)
{
   
   
   class HL_ExpPoints : public HL_Data
   {
         // Member variables: 
      public:
         // -- Static factory pointers: 
         static Abstract_HL_ExpPoints* (*__factory0)();
         static Abstract_HL_ExpPoints* (*__factory1)(::std::basic_string<char, std::char_traits<char>, std::allocator<char> >);
   
         // -- Other member variables: 
   
         // Member functions: 
      public:
         void Read();
   
         double GetChi2(::std::vector<double, std::allocator<double> > theory);
   
         double GetLogLikelihood(::std::vector<double, std::allocator<double> > theory);
   
         double GetLikelihood(::std::vector<double, std::allocator<double> > theory);
   
         bool InitData();
   
   
         // Wrappers for original constructors: 
      public:
         HL_ExpPoints();
         HL_ExpPoints(::std::basic_string<char, std::char_traits<char>, std::allocator<char> > s);
   
         // Special pointer-based constructor: 
         HL_ExpPoints(Abstract_HL_ExpPoints* in);
   
         // Copy constructor: 
         HL_ExpPoints(const HL_ExpPoints& in);
   
         // Assignment operator: 
         HL_ExpPoints& operator=(const HL_ExpPoints& in);
   
         // Destructor: 
         ~HL_ExpPoints();
   
         // Returns correctly casted pointer to Abstract class: 
         Abstract_HL_ExpPoints* get_BEptr() const;
   
   };
   
}


#include "gambit/Backends/backend_undefs.hpp"

#endif /* __wrapper_HL_ExpPoints_decl_HepLike_1_0_h__ */
