"""
P(T) probability of true mother genotype
P(S) probability of somatic mother genotype
P(R) probability of sequencing reads

P(T) requires no conditioning
P(S) = \sum_T P(T) * P(S|T)
P(R) = \sum_S P(S) * P(R|S)

convert this into test cases
"""
import family.trio_model as fm
import family.utilities as ut
import family.pdf as pdf
import numpy as np
import math

# some useful data structures
nt_index = {'A':0,
            'C':1,
            'G':2,
            'T':3}
n_nt = len(nt_index.keys())

genotype_index = {'AA':0,
                  'AC':1,
                  'AG':2,
                  'AT':3,
                  'CA':4,
                  'CC':5,
                  'CG':6,
                  'CT':7,
                  'GA':8,
                  'GC':9,
                  'GG':10,
                  'GT':11,
                  'TA':12,
                  'TC':13,
                  'TG':14,
                  'TT':15}
n_gt = len(genotype_index.keys())

# at the top (population sample) of the tree events should sum to 1
muta_rate = 0.001
nt_freq = [0.25, 0.25, 0.25, 0.25]
parent_prob_mat = fm.pop_sample(muta_rate, nt_freq)
print np.exp(parent_prob_mat).shape
print np.sum(np.exp(parent_prob_mat))

# at the germline mutation level, we must condition on parent genotype layer
# for events to sum to 1
child_prob_mat = np.zeros((n_gt, n_gt, n_gt))
for mother_geno in genotype_index.iterkeys():
    mi = genotype_index[mother_geno]
    for father_geno in genotype_index.iterkeys():
        fi = genotype_index[father_geno]
        for child_geno in genotype_index.iterkeys():
            ci = genotype_index[child_geno]
            child_given_parent = fm.germ_muta(child_geno[0], child_geno[1],
                                              mother_geno[0], mother_geno[1],
                                              father_geno[0], father_geno[1], 
                                              0.001)
            parent = parent_prob_mat[mi, fi]
            event = child_given_parent * np.exp(parent) # latter in log form
            child_prob_mat[mi, fi, ci] = event
print np.sum(child_prob_mat)

# at the somatic mutation layer we again must condition on parent
# genotype for events to sum to 1 

# first compute event space for somatic nucleotide given a genotype nucleotide
# for a single chromosome
prob_vec = np.zeros((4,4))
for soma_nt in nt_index.iterkeys():
    i = nt_index[soma_nt]
    for geno_nt in nt_index.iterkeys():
        j = nt_index[geno_nt]
        prob_vec[i, j] = fm.soma_muta(soma_nt, geno_nt, 0.001)

# next combine event spaces for two chromosomes (independent of each other)
# and call resulting 16x16 matrix soma_given_geno
# first dimension lexicographical order of pairs of letters from 
# nt alphabet for somatic genotypes
# second dimension is that for true genotypes
soma_given_geno = np.zeros((n_gt, n_gt))
for chrom1 in nt_index.iterkeys():
    i = nt_index[chrom1]
    given_chrom1_vec = prob_vec[:, i]
    for chrom2 in nt_index.iterkeys():
        j = nt_index[chrom2]
        given_chrom2_vec = prob_vec[:, i]
        soma_muta_index = i * n_nt + j
        outer_prod = np.outer(given_chrom1_vec, given_chrom2_vec)
        outer_prod_flat = outer_prod.flatten()
        soma_given_geno[:, soma_muta_index] = outer_prod_flat

# with the event space from the somatic mutation step calculated we can now
# assign a pdf to the true genotype event space based on the previous layer

# collapse parent prob mat into a single parent
parent_prob_mat_exp = np.exp(parent_prob_mat)
geno = np.sum(parent_prob_mat_exp, 0)
print geno
print np.sum(geno)

# and compute the joint probabilities
soma_and_geno = np.zeros((n_gt, n_gt))
for i in xrange(n_gt):
    soma_and_geno[:, i] = geno[i] * soma_given_geno[:, i]

prob_soma = np.sum(soma_and_geno, 0)
print np.sum(soma_and_geno)

# finally, compute probabilities of sequencing error
nt_string_size = 2
nt_counts = ut.enum_nt_counts(nt_string_size)
n_strings = int(math.pow(4, nt_string_size))
alpha_params = np.zeros((n_strings, n_nt))
prob_read_given_soma = np.zeros((n_strings))
for i in xrange(n_strings):
    alpha_params[i] = [0.25, 0.25, 0.25, 0.25]
    log_prob = pdf.dirichlet_multinomial(alpha_params[i], nt_counts[i])
    prob_read_given_soma[i] = np.exp(log_prob)

print prob_read_given_soma
print np.sum(prob_read_given_soma)
