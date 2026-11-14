# WhateverXe 0.8.2 R16 patch series

Base: [WhateverXe 0.8.2](https://github.com/b00t0x/WhateverXe/tree/4512191b9643e2391431fbd9639305b61568ee32), commit `4512191b9643e2391431fbd9639305b61568ee32`.
Apply the production patch and then the test-fixture adaptation, in `series` order, using `git apply --check` followed by `git apply` for each patch. Both replayed successfully in a clean source tree.

The resulting source is published at `src/WhateverXe`. Replay proves that these changes apply to the pinned official source. It is not a recompilation or proof that this is the complete input tree used for the deployed binary.

WhateverXe and these derived patches retain its BSD 3-Clause license in `LICENSE.txt`. Existing upstream attribution remains in the patch context. The local R16 work adapts panel ownership/handoff, accelerator diagnostics, software-media policy and backlight arithmetic; it does not originate upstream firmware-wiring support.
