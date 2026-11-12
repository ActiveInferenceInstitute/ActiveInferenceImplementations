# Full test suite for ActiveInferenceImplementations.
#
# The mean-field VMP model is declared in `specs/normal_vmp.gnn.md`, so these
# tests read the declarations from that document and check that the RxInfer
# message passing result agrees with the properties the specification states.
#
# `test/static_tests.jl` holds the gates that do not need RxInfer and runs as
# its own fast arm; this file includes it and adds inference.
#
# Run the documented gate with:
#
#     julia --project=. test/runtests.jl

using Distributions
using Random
using Test

using RxInfer

@model function normal_estimation(y, m_μ, m_v, w_α, w_β)
    m ~ NormalMeanVariance(m_μ, m_v)
    w ~ Gamma(shape = w_α, rate = w_β)
    for i in eachindex(y)
        y[i] ~ NormalMeanPrecision(m, w)
    end
end

"""Run the declared mean-field VMP inference and return the RxInfer result."""
function declared_inference(data)
    return infer(
        model = normal_estimation(
            m_μ = PARAMETERS.m_prior_mean,
            m_v = PARAMETERS.m_prior_variance,
            w_α = PARAMETERS.w_prior_shape,
            w_β = PARAMETERS.w_prior_rate,
        ),
        data = (y = data,),
        constraints = MeanField(),
        initialization = @initialization(begin
            q(m) = vague(NormalMeanVariance)
            q(w) = vague(GammaShapeRate)
        end),
        iterations = PARAMETERS.vmp_iterations,
        free_energy = true,
    )
end

@testset "ActiveInferenceImplementations" begin
    # The static gates run as their own arm (`test/static_tests.jl`); here they
    # are part of the same aggregate count.
    include(joinpath(@__DIR__, "static_tests.jl"))

    @testset "mean-field VMP recovers the declared data statistics" begin
        data = declared_data(PARAMETERS)
        result = declared_inference(data)
        m_marginals = result.posteriors[:m]
        w_marginals = result.posteriors[:w]

        @test length(m_marginals) == PARAMETERS.vmp_iterations
        @test length(w_marginals) == PARAMETERS.vmp_iterations
        @test length(result.free_energy) == PARAMETERS.vmp_iterations

        # Sample statistics of the declared data.
        sample_mean = mean(data)
        sample_precision = 1 / var(data)

        # The mean-field posterior is not the exact Normal-Gamma posterior, so
        # the tolerances below are loose on purpose: they check the recovery,
        # not an analytic equality.
        @test isapprox(mean(m_marginals[end]), sample_mean; atol = 0.1)
        @test isapprox(mean(w_marginals[end]), sample_precision; atol = 0.02)

        # The approximation concentrates on the data as the iterations run.
        @test abs(mean(m_marginals[end]) - sample_mean) <
              abs(mean(m_marginals[1]) - sample_mean)
        @test std(m_marginals[end]) < std(m_marginals[1])

        # The free energy is the objective the iterations minimize.
        @test result.free_energy[end] < result.free_energy[1]
    end
end
