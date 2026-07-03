"""
Rate limiting preko slowapi - štiti write endpointe i login od zloupotrebe
(npr. brute-force pokušaja lozinke, spam kreiranja ticketa).

Limitiranje je po IP adresi klijenta (default slowapi strategija).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
