#ifndef __wrapper_SLHAinterface_def_Pythia_8_212_h__
#define __wrapper_SLHAinterface_def_Pythia_8_212_h__

#include "wrapper_Info_decl.h"
#include "wrapper_Settings_decl.h"
#include "wrapper_Rndm_decl.h"
#include "wrapper_Couplings_decl.h"
#include "wrapper_ParticleData_decl.h"
#include <sstream>
#include "wrapper_SusyLesHouches_decl.h"
#include "wrapper_CoupSUSY_decl.h"

#include "identification.hpp"

namespace CAT_3(BACKENDNAME,_,SAFE_VERSION)
{
    
    namespace Pythia8
    {
        
        // Member functions: 
        inline void SLHAinterface::setPtr(WrapperBase< Pythia8::Abstract_Info >* infoPtrIn)
        {
            wrapperbase::BEptr->setPtr__BOSS((*infoPtrIn).BEptr);
        }
        
        inline void SLHAinterface::init(WrapperBase< Pythia8::Abstract_Settings >& settings, WrapperBase< Pythia8::Abstract_Rndm >* rndmPtr, WrapperBase< Pythia8::Abstract_Couplings >* couplingsPtrIn, WrapperBase< Pythia8::Abstract_ParticleData >* particleDataPtr, bool& useSHLAcouplings, ::std::basic_stringstream<char, std::char_traits<char>, std::allocator<char> >& ParticleDataBuffer)
        {
            wrapperbase::BEptr->init__BOSS(*settings.BEptr, (*rndmPtr).BEptr, (*couplingsPtrIn).BEptr, (*particleDataPtr).BEptr, useSHLAcouplings, ParticleDataBuffer);
        }
        
        inline bool SLHAinterface::initSLHA(WrapperBase< Pythia8::Abstract_Settings >& settings, WrapperBase< Pythia8::Abstract_ParticleData >* particleDataPtr)
        {
            return wrapperbase::BEptr->initSLHA__BOSS(*settings.BEptr, (*particleDataPtr).BEptr);
        }
        
        inline void SLHAinterface::pythia2slha(WrapperBase< Pythia8::Abstract_ParticleData >* particleDataPtr)
        {
            wrapperbase::BEptr->pythia2slha__BOSS((*particleDataPtr).BEptr);
        }
        
        
        // Wrappers for original constructors: 
        inline Pythia8::SLHAinterface::SLHAinterface() :
            WrapperBase<Pythia8::Abstract_SLHAinterface>(__factory0()),
            slha(&(wrapperbase::BEptr->slha_ref__BOSS())),
            coupSUSY(&(wrapperbase::BEptr->coupSUSY_ref__BOSS())),
            meMode(wrapperbase::BEptr->meMode_ref__BOSS())
        {
            wrapperbase::BEptr->wrapper__BOSS(this);
            wrapperbase::BEptr->can_delete_wrapper(false);  // Override setting in wrapper__BOSS
            _memberVariablesInit();
        }
        
        // Special pointer-based constructor: 
        inline Pythia8::SLHAinterface::SLHAinterface(Pythia8::Abstract_SLHAinterface* in) :
            WrapperBase<Pythia8::Abstract_SLHAinterface>(in),
            slha(&(wrapperbase::BEptr->slha_ref__BOSS())),
            coupSUSY(&(wrapperbase::BEptr->coupSUSY_ref__BOSS())),
            meMode(wrapperbase::BEptr->meMode_ref__BOSS())
        {
            wrapperbase::BEptr->wrapper__BOSS(this);
            wrapperbase::BEptr->can_delete_wrapper(false);  // Override setting in wrapper__BOSS
            _memberVariablesInit();
        }
        
        inline Pythia8::SLHAinterface::SLHAinterface(Pythia8::Abstract_SLHAinterface* const & in, bool) :
            WrapperBase<Pythia8::Abstract_SLHAinterface>(in, true),
            slha(&(wrapperbase::BEptr->slha_ref__BOSS())),
            coupSUSY(&(wrapperbase::BEptr->coupSUSY_ref__BOSS())),
            meMode(wrapperbase::BEptr->meMode_ref__BOSS())
        {
            wrapperbase::BEptr->wrapper__BOSS(this);
            wrapperbase::BEptr->can_delete_wrapper(false);  // Override setting in wrapper__BOSS
            _memberVariablesInit();
        }
        
        // Copy constructor: 
        inline Pythia8::SLHAinterface::SLHAinterface(const SLHAinterface& in) :
            WrapperBase<Pythia8::Abstract_SLHAinterface>(in),
            slha(&(wrapperbase::BEptr->slha_ref__BOSS())),
            coupSUSY(&(wrapperbase::BEptr->coupSUSY_ref__BOSS())),
            meMode(wrapperbase::BEptr->meMode_ref__BOSS())
        {
            wrapperbase::BEptr->can_delete_me(true);
            wrapperbase::BEptr->wrapper__BOSS(this);
            wrapperbase::BEptr->can_delete_wrapper(false);  // Override setting in wrapper__BOSS
            _memberVariablesInit();
        }
        
        // Assignment operator: 
        inline Pythia8::SLHAinterface& SLHAinterface::operator=(const SLHAinterface& in)
        {
            WrapperBase<Pythia8::Abstract_SLHAinterface>::operator=(in);
            return *this;
        }
        
        
        // Destructor: 
        inline Pythia8::SLHAinterface::~SLHAinterface()
        {
        }
        
        
        // Member variable initialiser: 
        inline void Pythia8::SLHAinterface::_memberVariablesInit()
        {
            (slha).WrapperBase<Pythia8::Abstract_SusyLesHouches>::BEptr->can_delete_wrapper(false);
            (slha).WrapperBase<Pythia8::Abstract_SusyLesHouches>::BEptr->can_delete_me(false);
            (coupSUSY).WrapperBase<Pythia8::Abstract_CoupSUSY>::BEptr->can_delete_wrapper(false);
            (coupSUSY).WrapperBase<Pythia8::Abstract_CoupSUSY>::BEptr->can_delete_me(false);
        }
        
    }
    
}


#include "gambit/Backends/backend_undefs.hpp"

#endif /* __wrapper_SLHAinterface_def_Pythia_8_212_h__ */