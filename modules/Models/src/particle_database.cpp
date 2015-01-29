//   GAMBIT: Global and Modular BSM Inference Tool
//   *********************************************
///  \file
///
///  GAMBIT particle database.  Add to this if you
///  need to define a new particle.  
///
///  Single particles can be added with:
///   add_particle("particle_id", (pdg_code, context_int))
///  where context_int is some context-dependent integer
///  that helps identify uni
///
///  Multiple particles with an index can be added with:
///   add_particle_set("X", 
///    (pdg_code_1, context_int_1),
///    (pdg_code_2, context_int_2),
///    (pdg_code_3, context_int_3),
///    ...
///    (pdg_code_n, context_int_n) )
///  This will produce particles with string IDs
///  "X_1", "X_2", "X_3", ..., "X_n".
///
///  *********************************************
///
///  Authors (add name and date if you modify):
///   
///  \author Pat Scott  
///          (p.scott@imperial.ac.uk)
///  \date 2015 Jan
///
///  *********************************************


#include "partmap.hpp"
#include "particle_macros.hpp"

namespace Gambit
{

  namespace Models
  {

    void define_particles(partmap* particles)
    {
      // Ben: I am hereby claiming context integer 0 in the name of MSSM mass eigenstates!
      //  I am still a little unsure what the "best" string names to use here are. I was
      //  just going with the strings close to those already used in flexibleSUSY, but now
      //  I am somewhat leaning towards something close to those used by Pythia since they
      //  might be more familiar to people. That is what is currently used below (though
      //  I don't have individual names for particles which flexibleSUSY puts into groups,
      //  since that was a headache).
      //  Anyway we should settle on something fairly quickly to avoid further such headaches later.


      // ---- Standard Model gauge bosons (context = 0) ----

      add_particle("g",     ( 21, 0) )
      add_particle("gamma", ( 22, 0) )
      add_particle("Z0",    ( 23, 0) )
      add_particle("W+",    ( 24, 0) )
      add_particle("W-",    (-24, 0) )


      // ---- Standard Model mass eigenstates (context = 0) ----

      // Mass ordered down and up type quarks
      add_particle_set("d",    (( 1, 0), ( 3, 0), ( 5, 0)) )
      add_particle_set("dbar", ((-1, 0), (-3, 0), (-5, 0)) )
      add_particle_set("u",    (( 2, 0), ( 4, 0), ( 6, 0)) )
      add_particle_set("ubar", ((-2, 0), (-4, 0), (-6, 0)) )
      // Mass ordered charged leptons and neutrinos 
      add_particle_set("e-", (( 11, 0), ( 13, 0), ( 15, 0)) )
      add_particle_set("e+", ((-11, 0), (-13, 0), (-15, 0)) )
      add_particle_set("nu", (( 12, 0), ( 14, 0), ( 16, 0)) )


      // ---- Standard Model flavour eigenstates (context = 1) ----

      // Quarks
      add_particle("d",     (  1, 1) )
      add_particle("u",     (  2, 1) )
      add_particle("s",     (  3, 1) )
      add_particle("c",     (  4, 1) )
      add_particle("b",     (  5, 1) )
      add_particle("t",     (  6, 1) )
      add_particle("dbar",  ( -1, 1) )
      add_particle("ubar",  ( -2, 1) )
      add_particle("sbar",  ( -3, 1) )
      add_particle("cbar",  ( -4, 1) )
      add_particle("bbar",  ( -5, 1) )
      add_particle("tbar",  ( -6, 1) )
      // Leptons
      add_particle("e-",    ( 11, 1) )
      add_particle("mu-",   ( 13, 1) )
      add_particle("tau-",  ( 15, 1) )
      add_particle("e+",    (-11, 1) )
      add_particle("mu+",   (-13, 1) )
      add_particle("tau+",  (-15, 1) )
      // Neutrinos
      add_particle("nu_e"  , (12, 1) )
      add_particle("nu_mu" , (14, 1) )
      add_particle("nu_tau", (16, 1) )


      // ---- MSSM sparticle mass eigenstates ---- (TODO to be extended to NMSSM)
      // Defined according to SLHA2 (http://arxiv.org/pdf/0801.0045v3.pdf, see eq. 28 - 31)

      // Gluino
      add_particle("~g", (1000021,0) )
      // Mass-ordered neutral, pseudoscalar, and charged Higgs bosons
      add_particle_set("h0", ((25, 0), (35, 0)) )
      add_particle("A0", ( 36, 0) )
      add_particle("H+", ( 37, 0) )
      add_particle("H-", (-37, 0) )
      // Mass-ordered down and up-type squarks
      add_particle_set("~d",    (( 1000001, 0), ( 1000003, 0), ( 1000005, 0),
                                 ( 2000001, 0), ( 2000003, 0), ( 2000005, 0)) )
      add_particle_set("~u",    (( 1000002, 0), ( 1000004, 0), ( 1000006, 0),
                                 ( 2000002, 0), ( 2000004, 0), ( 2000006, 0)) )
      add_particle_set("~dbar", ((-1000001, 0), (-1000003, 0), (-1000005, 0),
                                 (-2000001, 0), (-2000003, 0), (-2000005, 0)) )
      add_particle_set("~ubar", ((-1000002, 0), (-1000004, 0), (-1000006, 0),
                                 (-2000002, 0), (-2000004, 0), (-2000006, 0)) )
      // Mass-ordered sleptons and sneutrinos 
      add_particle_set("~e-", (( 1000011, 0), ( 1000013, 0), ( 1000015, 0),
                               ( 2000011, 0), ( 2000013, 0), ( 2000015, 0)) )
      add_particle_set("~e+", ((-1000011, 0), (-1000013, 0), (-1000015, 0),
                               (-2000011, 0), (-2000013, 0), (-2000015, 0)) )
      add_particle_set("~nu", (( 1000012, 0), ( 1000014, 0), ( 1000016, 0)) )
      // Mass-ordered charginos and neutralinos
      add_particle_set("~chi0", (( 1000022, 0), ( 1000023, 0), (1000025, 0), (1000035, 0)) )
      add_particle_set("~chi+", (( 1000024, 0), ( 1000037, 0)) )
      add_particle_set("~chi-", ((-1000024, 0), (-1000037, 0)) )


      // ---- RPV NMSSM mass eigenstates (context = 10) ---- //TODO not yet totally complete?

      // Example extension of neutrino set to account for mixing with NMSSM neutralinos
      add_particle_set("nu_RPV", ((12, 10), (14, 10), (16, 10), 
           (1000022, 10), (1000023, 10), (1000025, 10), (1000035, 10), (1000045, 10)) )


    }// end define_particles

  }

}

