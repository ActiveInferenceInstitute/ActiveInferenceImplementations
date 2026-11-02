# GNN Specification: ActiveInferenceImplementations Mean-Field VMP Normal Estimation

## GNNSection

ActInfVariational

## GNNVersionAndFlags

GNN v1.1

## ModelName

ActiveInferenceImplementations Mean-Field VMP Normal Estimation

## ModelAnnotation

Variational generative model of `n` Normal observations with an unknown mean
`m` and an unknown precision `w`, estimated by mean-field variational message
passing in `RxInfer.jl/01_message_passing.ipynb`.

- `m ~ NormalMeanVariance(m_prior_mean, m_prior_variance)` and
  `w ~ Gamma(shape = w_prior_shape, rate = w_prior_rate)` are the priors; the
  observations `y_i ~ NormalMeanPrecision(m, w)` are conditionally independent
  given `m` and `w`.
- The approximate posterior factorizes as `q(m, w) = q(m) q(w)`, the
  `MeanField()` constraint applied in the notebook, and the message passing
  scheme is iterated `vmp_iterations` times.
- The notebook reads the declared scalars with `src/spec_reader.jl`, so this
  document is the single source of truth for the priors, the data statistics,
  the observation count, the iteration count, and the seed.
- `RxInfer.jl/00_intro.ipynb` uses the Beta-Bernoulli coin model instead. That
  model is not declared here: its canonical GNN document is
  `specs/coin_flip.gnn.md` in ActInf_RxInfer.
- This is a continuous exponential-family model with a latent precision. GNN's
  framework renderers target discrete POMDPs (including the linear-Gaussian
  `CONTINUOUS` strategy), so this document is validated and read by tooling
  rather than rendered.

## StateSpaceBlock

m[1,type=float]         # Latent mean of the Normal likelihood
w[1,type=float]         # Latent precision of the Normal likelihood
y[100,1,type=float]     # Normal observations

## Connections

m>y
w>y

## InitialParameterization

m_prior_mean={(0.0)}
m_prior_variance={(10.0)}
w_prior_shape={(0.1)}
w_prior_rate={(10.0)}
data_mean={(-4.0)}
data_precision={(0.2)}
n_observations={(100)}
vmp_iterations={(10)}
seed={(1234)}

## Equations

Priors and likelihood:

m ~ NormalMeanVariance(m_prior_mean, m_prior_variance)
w ~ Gamma(shape = w_prior_shape, rate = w_prior_rate)
y_i | m, w ~ NormalMeanPrecision(m, w),  i = 1, ..., n

Mean-field variational approximation, iterated by message passing:

q(m, w) = q(m) q(w)

Properties the implementation reports for the declared run:

mean(q(m)) concentrates on the sample mean of y
mean(q(w)) concentrates on the sample precision 1 / var(y)
the free energy trace decreases over the vmp_iterations iterations

## Time

Static

## ActInfOntologyAnnotation

m=HiddenState
w=Precision
y=Observation

## ModelParameters

model_family: normal_mean_precision_mean_field
latent_variable: m
latent_precision: w
observations: y
prior_mean: 0.0
prior_variance: 10.0
prior_precision_shape: 0.1
prior_precision_rate: 10.0
approximation: mean_field
inference: variational_message_passing
vmp_iterations: 10
n_observations: 100
data_mean: -4.0
data_precision: 0.2
seed: 1234
implementation: RxInfer.jl/01_message_passing.ipynb
reader: src/spec_reader.jl

## Footer

ActiveInferenceImplementations mean-field VMP Normal estimation — canonical
GNN fixture of ActiveInferenceImplementations. Authored by hand as the single
source of truth for the model in `RxInfer.jl/01_message_passing.ipynb`.
Verified with the pinned upstream parser recorded in `specs/gnn-pin.json`.

## Signature

Not cryptographically signed.
