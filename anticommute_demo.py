"""anticommute_demo.py - why the naive qubit encoding fails."""

import numpy as np

I  = np.eye(2)
Z  = np.diag([1, -1]).astype(complex)
sp = np.array([[0, 0], [1, 0]], dtype=complex)   # |1><0| : creates an electron
k  = np.kron

# --- NAIVE: a_p^dag = sigma^+ on qubit p, and nothing else ---
n0 = k(I, sp)      # qubit 0
n1 = k(sp, I)      # qubit 1
print("NAIVE  a0+a1+ == a1+a0+ ?", np.allclose(n0 @ n1, n1 @ n0),
      " <- they COMMUTE: wrong for fermions")

# --- JORDAN-WIGNER: a_p^dag = (Z on every qubit below p) * sigma^+ on p ---
j0 = k(I, sp)      # p=0: nothing below, so no string
j1 = k(sp, Z)      # p=1: Z on qubit 0, sigma^+ on qubit 1
print("JW     a0+a1+ == -a1+a0+ ?", np.allclose(j0 @ j1, -(j1 @ j0)),
      " <- they ANTICOMMUTE: correct")

print("because Z and sigma^+ on the SAME qubit anticommute:",
      np.allclose(Z @ sp, -sp @ Z))
