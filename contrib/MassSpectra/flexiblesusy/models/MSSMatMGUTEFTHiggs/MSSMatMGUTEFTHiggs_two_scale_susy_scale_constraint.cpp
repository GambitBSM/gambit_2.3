// ====================================================================
// This file is part of FlexibleSUSY.
//
// FlexibleSUSY is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published
// by the Free Software Foundation, either version 3 of the License,
// or (at your option) any later version.
//
// FlexibleSUSY is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with FlexibleSUSY.  If not, see
// <http://www.gnu.org/licenses/>.
// ====================================================================

// File generated at Thu 10 May 2018 14:36:17

#include "MSSMatMGUTEFTHiggs_two_scale_susy_scale_constraint.hpp"
#include "MSSMatMGUTEFTHiggs_two_scale_model.hpp"
#include "wrappers.hpp"
#include "logger.hpp"
#include "error.hpp"
#include "ew_input.hpp"
#include "gsl_utils.hpp"
#include "minimizer.hpp"
#include "raii.hpp"
#include "root_finder.hpp"
#include "threshold_loop_functions.hpp"

#include <cmath>

namespace flexiblesusy {

#define DERIVEDPARAMETER(p) model->p()
#define EXTRAPARAMETER(p) model->get_##p()
#define INPUTPARAMETER(p) model->get_input().p
#define MODELPARAMETER(p) model->get_##p()
#define PHASE(p) model->get_##p()
#define BETAPARAMETER(p) beta_functions.get_##p()
#define BETAPARAMETER1(l,p) beta_functions_##l##L.get_##p()
#define BETA(p) beta_##p
#define BETA1(l,p) beta_##l##L_##p
#define LowEnergyConstant(p) Electroweak_constants::p
#define MZPole qedqcd.displayPoleMZ()
#define STANDARDDEVIATION(p) Electroweak_constants::Error_##p
#define Pole(p) model->get_physical().p
#define SCALE model->get_scale()
#define THRESHOLD static_cast<int>(model->get_thresholds())
#define MODEL model
#define MODELCLASSNAME MSSMatMGUTEFTHiggs<Two_scale>

MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::MSSMatMGUTEFTHiggs_susy_scale_constraint(
   MSSMatMGUTEFTHiggs<Two_scale>* model_, const softsusy::QedQcd& qedqcd_)
   : model(model_)
   , qedqcd(qedqcd_)
{
   initialize();
}

void MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::apply()
{
   check_model_ptr();



   model->calculate_DRbar_masses();
   update_scale();

   // apply user-defined susy scale constraints
   const auto TanBeta = INPUTPARAMETER(TanBeta);
   const auto vd = MODELPARAMETER(vd);
   const auto vu = MODELPARAMETER(vu);

   MODEL->set_vu(Re(TanBeta*Sqrt((Sqr(vd) + Sqr(vu))/(1 + Sqr(TanBeta)))));
   MODEL->set_vd(Re(Sqrt((Sqr(vd) + Sqr(vu))/(1 + Sqr(TanBeta)))));
   MODEL->solve_ewsb();

}

double MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::get_scale() const
{
   return scale;
}

double MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::get_initial_scale_guess() const
{
   return initial_scale_guess;
}

const MSSMatMGUTEFTHiggs_input_parameters& MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::get_input_parameters() const
{
   check_model_ptr();

   return model->get_input();
}

MSSMatMGUTEFTHiggs<Two_scale>* MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::get_model() const
{
   return model;
}

void MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::set_model(Model* model_)
{
   model = cast_model<MSSMatMGUTEFTHiggs<Two_scale>*>(model_);
}

void MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::set_sm_parameters(
   const softsusy::QedQcd& qedqcd_)
{
   qedqcd = qedqcd_;
}

const softsusy::QedQcd& MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::get_sm_parameters() const
{
   return qedqcd;
}

void MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::clear()
{
   scale = 0.;
   initial_scale_guess = 0.;
   model = nullptr;
   qedqcd = softsusy::QedQcd();
}

void MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::initialize()
{
   check_model_ptr();

   const auto MassBInput = INPUTPARAMETER(MassBInput);
   const auto mq2Input = INPUTPARAMETER(mq2Input);
   const auto mu2Input = INPUTPARAMETER(mu2Input);

   initial_scale_guess = Sqrt(Sqrt(mq2Input(2,2))*Sqrt(mu2Input(2,2)) + 4*Sqr(
      MassBInput));

   scale = initial_scale_guess;
}

void MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::update_scale()
{
   check_model_ptr();

   const auto ZU = MODELPARAMETER(ZU);
   const auto MSu = MODELPARAMETER(MSu);

   scale = Sqrt(Power(MSu(0),Sqr(Abs(ZU(0,2))) + Sqr(Abs(ZU(0,5))))*Power(MSu(1
      ),Sqr(Abs(ZU(1,2))) + Sqr(Abs(ZU(1,5))))*Power(MSu(2),Sqr(Abs(ZU(2,2))) +
      Sqr(Abs(ZU(2,5))))*Power(MSu(3),Sqr(Abs(ZU(3,2))) + Sqr(Abs(ZU(3,5))))*Power
      (MSu(4),Sqr(Abs(ZU(4,2))) + Sqr(Abs(ZU(4,5))))*Power(MSu(5),Sqr(Abs(ZU(5,2))
      ) + Sqr(Abs(ZU(5,5)))));


}

void MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>::check_model_ptr() const
{
   if (!model)
      throw SetupError("MSSMatMGUTEFTHiggs_susy_scale_constraint<Two_scale>: "
                       "model pointer is zero!");
}

} // namespace flexiblesusy
