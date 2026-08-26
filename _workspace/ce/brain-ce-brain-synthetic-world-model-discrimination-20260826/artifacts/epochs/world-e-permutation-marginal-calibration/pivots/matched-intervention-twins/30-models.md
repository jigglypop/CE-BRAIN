# Twin confirmation models

Status: COMPLETE

The parent R/F/G/O/S fit and selection procedures are reused without feature,
ridge, threshold, count or tie-break changes. Every candidate's chosen
train/validation fit is carried into confirmation. No twin result can select or
refit a model.

All confirmation forecasts are closed-loop rollouts initialized from the two
observed initial samples. The only new object is the arm contrast
$\widehat D_m=\widehat Y_m^{(1)}-\widehat Y_m^{(0)}$.
