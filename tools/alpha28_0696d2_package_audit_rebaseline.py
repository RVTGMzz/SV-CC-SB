#!/usr/bin/env python3
import alpha28_0696d2_package_audit as legacy
from alpha28_0696d2_rebaseline_contract import canonical_outputs

legacy.EXPECTED = {state: sha for state, (_, sha) in canonical_outputs().items()}
legacy.main()
