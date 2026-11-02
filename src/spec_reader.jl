# Reading the committed Generalized Notation Notation document.
#
# This file is dependency free on purpose. It is included by
# `RxInfer.jl/01_message_passing.ipynb`, by `test/runtests.jl`, and run with a
# bare `julia` binary by `scripts/validate_gnn_spec.py`, which compares what it
# reads with the pinned GNN parser. Do not add `using` statements.

"""
    GNNSpecParameters

Parameters of the mean-field VMP Normal estimation model declared by
`specs/normal_vmp.gnn.md`.
"""
struct GNNSpecParameters
    m_prior_mean::Float64
    m_prior_variance::Float64
    w_prior_shape::Float64
    w_prior_rate::Float64
    data_mean::Float64
    data_precision::Float64
    n_observations::Int
    vmp_iterations::Int
    seed::Int
end

"""Absolute path of the committed GNN document."""
const SPEC_PATH = joinpath(dirname(@__DIR__), "specs", "normal_vmp.gnn.md")

"""Declarations of the `InitialParameterization` section read by this reader."""
const SPEC_SCALAR_KEYS = (
    "m_prior_mean",
    "m_prior_variance",
    "w_prior_shape",
    "w_prior_rate",
    "data_mean",
    "data_precision",
    "n_observations",
    "vmp_iterations",
    "seed",
)

"""
    spec_section(path, name) -> String

Return the body of the `## name` section of the GNN document at `path`.
"""
function spec_section(path::AbstractString, name::AbstractString)::String
    text = read(path, String)
    header = match(Regex("(?m)^##[ \\t]*" * name * "[ \\t]*\$"), text)
    header === nothing && throw(ArgumentError("section '## $name' not found in $path"))
    tail = header.offset + ncodeunits(header.match)
    tail > ncodeunits(text) && return ""
    body = SubString(text, nextind(text, tail))
    following = findfirst(Regex("(?m)^##[ \\t]+[^ \\t]"), body)
    following === nothing && return String(body)
    first(following) == 1 && return ""
    return String(SubString(body, 1, first(following) - 1))
end

"""
    spec_scalar(path, key) -> Float64

Return the number declared for `key` in the `InitialParameterization` section.
"""
function spec_scalar(path::AbstractString, key::AbstractString)::Float64
    section = spec_section(path, "InitialParameterization")
    pattern = Regex("(?m)^[ \\t]*" * key * "[ \\t]*=[ \\t]*\\{[ \\t]*\\(([^)]*)\\)[ \\t]*\\}")
    found = match(pattern, section)
    found === nothing && throw(
        ArgumentError("scalar '$key' is not declared in InitialParameterization of $path")
    )
    value = tryparse(Float64, strip(found.captures[1]))
    value === nothing && throw(
        ArgumentError("declared value for '$key' in $path is not a number: $(found.captures[1])")
    )
    return value
end

"""
    spec_model_name(path = SPEC_PATH) -> String

Return the model name declared by the GNN document.
"""
function spec_model_name(path::AbstractString = SPEC_PATH)::String
    return strip(spec_section(path, "ModelName"))
end

"""
    spec_parameters(path = SPEC_PATH) -> GNNSpecParameters

Read the mean-field VMP model parameters declared by the GNN document.
"""
function spec_parameters(path::AbstractString = SPEC_PATH)::GNNSpecParameters
    values = Dict(key => spec_scalar(path, key) for key in SPEC_SCALAR_KEYS)
    return GNNSpecParameters(
        values["m_prior_mean"],
        values["m_prior_variance"],
        values["w_prior_shape"],
        values["w_prior_rate"],
        values["data_mean"],
        values["data_precision"],
        Int(round(values["n_observations"])),
        Int(round(values["vmp_iterations"])),
        Int(round(values["seed"])),
    )
end

"""
    spec_summary(path = SPEC_PATH) -> String

Return `key=value` lines describing the declared model, the form consumed by
`scripts/validate_gnn_spec.py`.
"""
function spec_summary(path::AbstractString = SPEC_PATH)::String
    parameters = spec_parameters(path)
    return join(
        (
            "model_name=" * spec_model_name(path),
            "m_prior_mean=$(parameters.m_prior_mean)",
            "m_prior_variance=$(parameters.m_prior_variance)",
            "w_prior_shape=$(parameters.w_prior_shape)",
            "w_prior_rate=$(parameters.w_prior_rate)",
            "data_mean=$(parameters.data_mean)",
            "data_precision=$(parameters.data_precision)",
            "n_observations=$(parameters.n_observations)",
            "vmp_iterations=$(parameters.vmp_iterations)",
            "seed=$(parameters.seed)",
        ),
        "\n",
    )
end
