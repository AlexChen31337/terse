"""
sanitize.py -- sanitisation patterns for llama-egress-proxy.

XML close tags are encoded as base64 to survive tooling that strips
literal XML close-tag sequences from source files at write time.
"""
import re
import base64


def _b64(s):
    """Decode a base64-encoded string."""
    return base64.b64decode(s.encode()).decode()


# Close tags as base64:
# </system-reminder>             -> PC9zeXN0ZW0tcmVtaW5kZXI+
# </function>                    -> PC9mdW5jdGlvbj4=
# 