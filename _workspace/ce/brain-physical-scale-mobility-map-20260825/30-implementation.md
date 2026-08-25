# Implementation record

Status: COMPLETE

Implemented `reality_stone/python/reality_stone/clarus/physical_scale_mobility.py` as a dependency-free exact-rational certificate. It exposes the supplied homogeneous scales, arbitrary scalar mobility, normalized mobility, physical window, reference speed and power, conditional speed and Euclidean dissipation uppers, exact atanh-series logarithm bounds, and physical decay-rate bounds.

The implementation distinguishes three contraction regimes. For $0<q<1$ it returns an exact rational logarithm/rate enclosure. For $q=0$ it returns a finite-window-collapse status and no logarithmic rate. For $q=1$ it returns a named non-certificate and zero positive-rate bound. All invalid types, signs, canonical forms, and series depths fail closed.

No empirical defaults, neural labels, tensor mobility, or mixed-unit coordinate inference were added.

