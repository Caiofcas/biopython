# This file is part of the Biopython distribution and governed by your
# choice of the "Biopython License Agreement" or the "BSD 3-Clause License".
# Please see the LICENSE file that should have been included as part of this
# package.
"""Calculate the Pseudo-Amino Acid Composition described by Chou, 2001.

Method is implemented as described in:

Chou, Kuo-Chen. Prediction of Protein Cellular Attributes Using
Pseudo-Amino Acid Composition. PROTEINS: Structure, Function, and
Genetics 43:246 –255 (2001).


Hidrophobicity, Hidrophilicity and Side-Chain Mass values are the same
as used in the original paper.
"""

from Bio.Data.IUPACData import protein_letters, protein_weights
from Bio.SeqUtils.ProtParamData import hw, ta

# TODO: add tests
# standard test
# test with diferent parameters (including scales)
# test scale with missing param
# TODO: add example with given scales
# Normalized scales

# Normalized Hidrophobicity
# Original Values from Tanfordl J. Am. Chem. Soc. 84:4240-4274(1962)
H_1_sum = sum(ta.values())
H_1_std = sum([(ta[aa] - H_1_sum) / 20 for aa in protein_letters])
H_1 = {aa: (ta[aa] - H_1_sum) / H_1_std for aa in protein_letters}

# Normalized Hidrophilicity
# Original Values from Hopp and Wood, Proc. Natl. Acad. Sci. U.S.A. 78:3824-3828(1981)
H_2_sum = sum(hw.values())
H_2_std = sum([(hw[aa] - H_2_sum) / 20 for aa in protein_letters])
H_2 = {aa: (hw[aa] - H_2_sum) / H_2_std for aa in protein_letters}

# Normalized side chain weights
M_sum = sum(protein_weights.values())
M_std = sum([(protein_weights[aa] - M_sum) / 20 for aa in protein_letters])
M = {aa: (protein_weights[aa] - M_sum) / M_std for aa in protein_letters}


class PseudoAAC:
    """A Class for calculating Chou's PseudoAAC of a given protein.

    Parameters
    ----------
    :protein_sequence: A ``Bio.Seq`` or string object containing a protein
                       sequence.
    :aa_percents: A dictionary with amino acid letters as keys and its
                  relative frequences as floats, e.g. ``{"A": 0.3, "C": 0.17, ...}``.
                  Default: ``None``. If ``None``, the dict will be calculated
                  from the given sequence.

    Methods
    -------
    :pseudoAAC(l_param,weight,scales): Calculates the Pseudo-AAC with given parameters.

    Examples
    --------
    The methods of this class can either be accessed from the class itself
    or from a ``ProtParam.ProteinAnalysis`` object (with partially different
    names):

    >>> from Bio.SeqUtils.PseudoAAC import PseudoAAC
    >>> protein = PseudoAAC("ACKLAA")
    >>> paac = protein.pseudoAAC()
    >>> print(len(paac))
    23
    >>> print(f"{paac[0]:.3f}")
    0.475
    >>> print(f"{paac[3]:.3f}")
    0.000
    >>> print(f"{paac[21]:.3f}")
    0.019

    >>> from Bio.SeqUtils.ProtParam import ProteinAnalysis as PA
    >>> protein = PA("MAEGEITTFTALTEKFNLPPGNYKKPKLLYCSNGGHFLRILPDGTVDGT"
    ...              "RDRSDQHIQLQLSAESVGEVYIKSTETGQYLAMDTSGLLYGSQTPSEEC"
    ...              "LFLERLEENHYNTYTSKKHAEKNWFVGLKKNGSCKRGPRTHYGQKAILF"
    ...              "LPLPV")
    >>> paac = protein.pseudoAAC()
    >>> print(f"{paac[0]:.3f}")
    0.038
    >>> print(f"{paac[3]:.3f}")
    0.075
    >>> print(f"{paac[21]:.3f}")
    0.016

    """

    def __init__(self, protein_sequence, aa_percents=None):
        """Initialize the class."""
        self.seq = str(protein_sequence).upper()
        self.L = len(self.seq)
        if not aa_percents:
            from Bio.SeqUtils.ProtParam import ProteinAnalysis as _PA

            aa_percents = _PA(self.seq).get_amino_acids_percent()

        self.aac = aa_percents

    def _calc_correlation(self, aa1, aa2, scales):
        return sum([(s[aa1] - s[aa2]) ** 2 for s in scales]) / len(scales)

    def _std_convert_scales(self, scales):
        """Perform the standard conversion on provided scales (PRIVATE)."""
        normalized = []
        for H in scales:
            s = sum(H.values())
            std = sum([(H[aa] - s) / 20 for aa in protein_letters])
            H = {aa: (H[aa] - s) / std for aa in protein_letters}
            normalized.append(H)
        return normalized

    def pseudoAAC(self, l_param=3, weight=0.05, scales=None):
        """Calculate the Pseudo AminoAcid Composition described by Chou, 2001.

        Calculates the Pseudo-Amino Acid Compositions utilizing the given l_param,
        weight and scales. Scales should be a list of dictionaries, where each
        dictionary has all standard aminoacids as keys and numbers as values.

        Default values for l_param and weight are 3 and 0.05 respectively. Default
        scales utilized are Hidrophilicity (Hoop & Wood, 1981), Hidrophobicity
        (Tanford, 1962) and Side Chain Mass.

        Returns a list of size 20+l_param with the components.
        """
        if scales is None:
            scales = [H_1, H_2, M]
        else:
            # check if scales contain values for all aa
            for i, s in enumerate(scales):
                for aa in protein_letters:
                    if s.get(aa) is None:
                        raise KeyError(f"scale {i} is missing value for aa: {aa}")

            scales = self._std_convert_scales(scales)

        # Calculate correlation parameters
        theta = []
        for j in range(1, l_param + 1):
            t_j = sum(
                [
                    self._calc_correlation(self.seq[i], self.seq[i + j], scales)
                    for i in range(self.L - j)
                ]
            )
            t_j /= self.L - j
            theta.append(t_j)

        # Sum of all AAC values is one by definition
        sum_term = 1 + weight * sum(theta)

        # First 20 terms reflect the effect of AAC
        X = [self.aac[k] / sum_term for k in protein_letters]

        # Components 21 to 20 + lambda reflect the effect of sequence order
        X += [weight * t / sum_term for t in theta]

        return X
