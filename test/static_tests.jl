# Static gates: the declared specification and the notebooks as data.
#
# These tests never load RxInfer and never run inference, so they finish in
# seconds and are the default `./run.sh` arm. The full suite (`test/runtests.jl`)
# includes this file and adds the message passing checks on top.
#
#     julia --project=. test/static_tests.jl

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

@testset "static gates" begin
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

    @testset "integer settings reject authored fractions and invalid values" begin
        document = read(SPEC_PATH, String)
        mktempdir() do directory
            for (key, original) in (
                ("n_observations", "100"), ("vmp_iterations", "10"), ("seed", "1234")
            )
                invalid = (
                    original * ".4", original * ".00000000000000001",
                    "NaN", "Inf", "-Inf", "banana", "",
                    string(BigInt(typemax(Int)) + 1),
                    string(BigInt(typemin(Int)) - 1),
                    "1e1000000000000000000000000", "1e-1000000000000000000000000",
                )
                for (index, token) in enumerate(invalid)
                    path = joinpath(directory, "$key-$index.gnn.md")
                    write(path, replace(document, "$key={($original)}" => "$key={($token)}"))
                    for reader in (spec_parameters, spec_summary)
                        failure = try
                            reader(path)
                            nothing
                        catch err
                            err
                        end
                        @test failure isa ArgumentError
                        if failure isa ArgumentError
                            diagnostic = sprint(showerror, failure)
                            @test occursin(key, diagnostic)
                            @test occursin(path, diagnostic)
                            if !isempty(token)
                                @test occursin(token, diagnostic)
                            end
                        end
                    end
                end
                path = joinpath(directory, "$key-missing.gnn.md")
                write(path, replace(document, "$key={($original)}\n" => ""))
                failure = try
                    spec_parameters(path)
                    nothing
                catch err
                    err
                end
                @test failure isa ArgumentError
                if failure isa ArgumentError
                    @test occursin(key, sprint(showerror, failure))
                    @test occursin(path, sprint(showerror, failure))
                end
            end
        end
    end

    @testset "exact integer spellings preserve parameters, summary and seeded data" begin
        document = read(SPEC_PATH, String)
        mktempdir() do directory
            for (key, original, exponent) in (
                ("n_observations", "100", "1e2"),
                ("vmp_iterations", "10", "1e1"),
                ("seed", "1234", "1234e0"),
            )
                for (index, token) in enumerate((
                    original * ".0", exponent, original * "00e-2", "+0" * original * ".000e0",
                ))
                    path = joinpath(directory, "$key-exact-$index.gnn.md")
                    write(path, replace(document, "$key={($original)}" => "$key={($token)}"))
                    parameters = spec_parameters(path)
                    for field in fieldnames(GNNSpecParameters)
                        @test getfield(parameters, field) == getfield(PARAMETERS, field)
                    end
                    @test spec_summary(path) == spec_summary()
                    @test declared_data(parameters) == declared_data(PARAMETERS)
                end
            end
            # Reader-only boundary fixtures impose no new seed or positivity policy.
            for token in (string(typemin(Int)), string(typemax(Int)),
                          string(typemin(Int)) * ".0", string(typemax(Int)) * ".0", "-0.0")
                path = joinpath(directory, "seed-boundary.gnn.md")
                write(path, replace(document, "seed={(1234)}" => "seed={($token)}"))
                expected = token == "-0.0" ? 0 : parse(Int, first(split(token, '.')))
                @test spec_parameters(path).seed == expected
                @test occursin("seed=$expected", spec_summary(path))
            end
            if Sys.WORD_SIZE >= 64
                for token in ("9007199254740993", "9007199254740993.0")
                    path = joinpath(directory, "seed-float-precision.gnn.md")
                    write(path, replace(document, "seed={(1234)}" => "seed={($token)}"))
                    @test spec_parameters(path).seed == Int(9007199254740993)
                    @test occursin("seed=9007199254740993", spec_summary(path))
                end
            end
        end
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
