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

function _spec_scalar_token(section::AbstractString, path::AbstractString, key::AbstractString)
    pattern = Regex("(?m)^[ \\t]*" * key * "[ \\t]*=[ \\t]*\\{[ \\t]*\\(([^)]*)\\)[ \\t]*\\}")
    found = match(pattern, section)
    found === nothing && throw(
        ArgumentError("scalar '$key' is not declared in InitialParameterization of $path")
    )
    return strip(found.captures[1])
end

function _spec_float(token::AbstractString, path::AbstractString, key::AbstractString)::Float64
    value = tryparse(Float64, token)
    value === nothing && throw(
        ArgumentError("declared value for '$key' in $path is not a number: $token")
    )
    return value
end

_spec_integer_error(path, key, token) =
    ArgumentError("declared value for '$key' in $path must be an exact finite Int: $token")

function _spec_integer(token::AbstractString, path::AbstractString, key::AbstractString)::Int
    value = tryparse(Int, token)
    value !== nothing && return value

    # Normalize decimal/exponent spellings without rounding through Float64 or
    # constructing arbitrarily large powers. The common integer spelling above
    # needs neither this normalization nor checked digit accumulation.
    number = match(r"^([+-]?)([0-9]*)(?:\.([0-9]*))?(?:[eE]([+-]?[0-9]+))?$", token)
    number === nothing && throw(_spec_integer_error(path, key, token))
    sign, whole, fraction, exponent_token = number.captures
    digits = fraction === nothing ? whole : whole * fraction
    isempty(digits) && throw(_spec_integer_error(path, key, token))
    first_nonzero = findfirst(c -> c != '0', digits)
    first_nonzero === nothing && return 0
    last_nonzero = findlast(c -> c != '0', digits)
    exponent = exponent_token === nothing ? 0 : tryparse(Int, exponent_token)
    exponent === nothing && throw(_spec_integer_error(path, key, token))
    fraction_length = fraction === nothing ? 0 : ncodeunits(fraction)
    minimum_exponent = fraction_length - (ncodeunits(digits) - last_nonzero)
    maximum_exponent = minimum_exponent + ndigits(typemax(Int)) -
                       (last_nonzero - first_nonzero + 1)
    minimum_exponent <= exponent <= maximum_exponent ||
        throw(_spec_integer_error(path, key, token))

    value = 0
    try
        for index in first_nonzero:last_nonzero
            digit = Int(codeunit(digits, index)) - Int('0')
            value = Base.Checked.checked_add(
                Base.Checked.checked_mul(value, 10), sign == "-" ? -digit : digit
            )
        end
        for _ in 1:(exponent - minimum_exponent)
            value = Base.Checked.checked_mul(value, 10)
        end
    catch err
        err isa OverflowError || rethrow()
        throw(_spec_integer_error(path, key, token))
    end
    return value
end

"""
    spec_scalar(path, key) -> Float64

Return the number declared for `key` in the `InitialParameterization` section.
"""
function spec_scalar(path::AbstractString, key::AbstractString)::Float64
    token = _spec_scalar_token(spec_section(path, "InitialParameterization"), path, key)
    return _spec_float(token, path, key)
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
    section = spec_section(path, "InitialParameterization")
    tokens = map(key -> _spec_scalar_token(section, path, key), SPEC_SCALAR_KEYS)
    scalars = ntuple(i -> _spec_float(tokens[i], path, SPEC_SCALAR_KEYS[i]), 6)
    integers = ntuple(i -> _spec_integer(tokens[i + 6], path, SPEC_SCALAR_KEYS[i + 6]), 3)
    return GNNSpecParameters(scalars..., integers...)
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
