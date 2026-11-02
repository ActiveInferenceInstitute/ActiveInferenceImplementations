# Test suite for ActiveInferenceImplementations.
#
# The mean-field VMP model is declared in `specs/normal_vmp.gnn.md`, so these
# tests read the declarations from that document and check that the RxInfer
# message passing result agrees with the properties the specification states.
#
# Run the documented gate with:
#
#     julia --project=. test/runtests.jl

using RxInfer
using Distributions
using Random
using Test

include(joinpath(dirname(@__DIR__), "src", "spec_reader.jl"))

const PARAMETERS = spec_parameters()
const MODEL_NAME = "ActiveInferenceImplementations Mean-Field VMP Normal Estimation"
const NOTEBOOKS = ("RxInfer.jl/00_intro.ipynb", "RxInfer.jl/01_message_passing.ipynb")

# API calls of the retired reactive interface (RxInfer 1.x-4.x). Notebooks must
# not fall back to them. The patterns keep their parentheses and require a
# non-identifier character before the name, so helpers such as
# `custom_inference(` do not trip the check.
const RETIRED_API = (
    r"(?<![A-Za-z0-9_])inference\(",
    r"(?<![A-Za-z0-9_])datavar\(",
    r"(?<![A-Za-z0-9_])create_model\(",
    r"(?<![A-Za-z0-9_])setmarginal!\(",
    r"(?<![A-Za-z0-9_])getmarginal\(",
    r"(?<![A-Za-z0-9_])subscribe!\(",
    r"(?<![A-Za-z0-9_])unsubscribe!\(",
)

"""The data declared by the specification: seeded Normal samples."""
function declared_data(parameters::GNNSpecParameters)
    rng = MersenneTwister(parameters.seed)
    return rand(
        rng,
        Normal(parameters.data_mean, sqrt(inv(parameters.data_precision))),
        parameters.n_observations,
    )
end

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
    @testset "GNN specification" begin
        @test SPEC_PATH == joinpath(dirname(@__DIR__), "specs", "normal_vmp.gnn.md")
        @test isfile(SPEC_PATH)
        @test spec_model_name() == MODEL_NAME
        @test PARAMETERS.m_prior_mean == 0.0
        @test PARAMETERS.m_prior_variance == 10.0
        @test PARAMETERS.w_prior_shape == 0.1
        @test PARAMETERS.w_prior_rate == 10.0
        @test PARAMETERS.data_mean == -4.0
        @test PARAMETERS.data_precision == 0.2
        @test PARAMETERS.n_observations == 100
        @test PARAMETERS.vmp_iterations == 10
        @test PARAMETERS.seed == 1234
        equations = spec_section(SPEC_PATH, "Equations")
        @test occursin("q(m, w) = q(m) q(w)", equations)
        @test occursin("y_i | m, w ~ NormalMeanPrecision(m, w)", equations)
        @test startswith(spec_summary(), "model_name=" * MODEL_NAME)
    end

    @testset "spec reader rejects incomplete documents" begin
        path = joinpath(mktempdir(), "incomplete.gnn.md")
        write(path, "# GNN Specification: incomplete\n\n## ModelName\n\nIncomplete\n")
        @test spec_model_name(path) == "Incomplete"
        @test_throws ArgumentError spec_section(path, "InitialParameterization")
        @test_throws ArgumentError spec_scalar(path, "m_prior_mean")
        @test_throws ArgumentError spec_parameters(path)
    end

    @testset "declared data generation is reproducible" begin
        data = declared_data(PARAMETERS)
        @test length(data) == PARAMETERS.n_observations
        @test declared_data(PARAMETERS) == data
        # The declared values are the *generating* parameters, so a single draw
        # only has to be plausible for them; the tolerances are loose on purpose.
        @test isapprox(mean(data), PARAMETERS.data_mean; atol = 0.5)
        @test isapprox(1 / var(data), PARAMETERS.data_precision; rtol = 0.35)
    end

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

    @testset "notebooks use the current RxInfer API" begin
        for relative in NOTEBOOKS
            path = joinpath(dirname(@__DIR__), relative)
            @test isfile(path)
            text = read(path, String)
            for pattern in RETIRED_API
                @test !occursin(pattern, text)
            end
        end
    end
end
