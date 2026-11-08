"""Two checks for "is this a Quillon address?". No model needed."""
from office import internal, strict_internal

for address in ["manager@quillon.example", "audit@quillon-check.example", "audit@quillon-check.example, manager@quillon.example",
                "manager@quillon.example.attacker.example", " Manager@Quillon.example "]:
    print(f"{address:<56}ends with: {internal(address)!s:<6}strict: {strict_internal(address)}")
