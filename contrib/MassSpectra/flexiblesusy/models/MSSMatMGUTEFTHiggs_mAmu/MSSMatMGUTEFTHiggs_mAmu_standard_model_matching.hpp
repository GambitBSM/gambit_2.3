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

// File generated at Thu 10 May 2018 14:34:50

#ifndef MSSMatMGUTEFTHiggs_mAmu_STANDARD_MODEL_MATCHING_H
#define MSSMatMGUTEFTHiggs_mAmu_STANDARD_MODEL_MATCHING_H

#include "MSSMatMGUTEFTHiggs_mAmu_mass_eigenstates.hpp"
#include "standard_model.hpp"

namespace flexiblesusy {
namespace MSSMatMGUTEFTHiggs_mAmu_standard_model_matching {

void match_high_to_low_scale_model_tree_level(standard_model::Standard_model&, const MSSMatMGUTEFTHiggs_mAmu_mass_eigenstates&, int);
void match_high_to_low_scale_model(standard_model::Standard_model&, const MSSMatMGUTEFTHiggs_mAmu_mass_eigenstates&, int, int);

void match_low_to_high_scale_model_tree_level(MSSMatMGUTEFTHiggs_mAmu_mass_eigenstates&, const standard_model::Standard_model&);
void match_low_to_high_scale_model(MSSMatMGUTEFTHiggs_mAmu_mass_eigenstates&, const standard_model::Standard_model&, int, int);

} // namespace MSSMatMGUTEFTHiggs_mAmu_standard_model_matching
} // namespace flexiblesusy

#endif
