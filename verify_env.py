"""verify_env.py - prove the environment works before writing any real code."""

import sys

print("python    ", sys.version.split()[0])

import numpy
import scipy
import matplotlib
print("numpy     ", numpy.__version__)
print("scipy     ", scipy.__version__)
print("matplotlib", matplotlib.__version__)

import pennylane as qml
print("pennylane ", qml.version())

import pyscf
from pyscf import gto, scf, fci
print("pyscf     ", pyscf.__version__)
print()

mol = gto.M(atom="H 0 0 0; H 0 0 0.735",
            basis="sto-3g",
            unit="Angstrom",
            verbose=0)

mf = scf.RHF(mol).run(verbose=0)
e_fci = fci.FCI(mf).kernel()[0]

print(f"nuclear repulsion  {mol.energy_nuc():12.6f} Ha")
print(f"Hartree-Fock       {mf.e_tot:12.6f} Ha   (expect -1.116999)")
print(f"FCI                {e_fci:12.6f} Ha   (expect -1.137306)")
print(f"correlation energy {mf.e_tot - e_fci:12.6f} Ha")
print()

import numpy as np
BOHR = 1.8897261254578281
coords = np.array([0.0, 0.0, 0.0,
                   0.0, 0.0, 0.735 * BOHR])
H, n_qubits = qml.qchem.molecular_hamiltonian(["H", "H"], coords,
                                              basis="sto-3g")
print(f"qubits required    {n_qubits}")
print(f"Pauli terms        {len(H.terms()[0])}")
print()
print("environment OK")
