#!/usr/bin/env python3
import alpha28_0696d2_window_environment_matrix as legacy
from alpha28_0696d2_rebaseline_contract import canonical_outputs, materialize, verify

legacy.APPROVED = canonical_outputs()
materialize()
verify()
legacy.apply()
legacy.validate()
