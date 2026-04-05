//! Declarative macros for ACLI spec enforcement.

/// Declares an ACLI command struct with auto-injected `--output` field.
///
/// Use `acli_args!` to define your command's clap arguments with an
/// automatic `--output` field (and `--dry-run` if `dry_run` is specified).
///
/// # Example: Idempotent command (gets --output only)
///
/// ```rust
/// use acli::acli_args;
///
/// acli_args! {
///     /// Get weather for a city.
///     pub struct GetArgs {
///         #[arg(long)]
///         pub city: String,
///     }
/// }
/// // GetArgs now has: city, output (auto-injected)
/// ```
///
/// # Example: Non-idempotent command (gets --output and --dry-run)
///
/// ```rust
/// use acli::acli_args;
///
/// acli_args! {
///     /// Deploy to target.
///     pub struct DeployArgs {
///         #[arg(long)]
///         pub target: String,
///     } with dry_run
/// }
/// // DeployArgs now has: target, output, dry_run (both auto-injected)
/// ```
#[macro_export]
macro_rules! acli_args {
    // With dry_run
    (
        $(#[$meta:meta])*
        $vis:vis struct $name:ident {
            $(
                $(#[$field_meta:meta])*
                $field_vis:vis $field_name:ident : $field_ty:ty
            ),* $(,)?
        } with dry_run
    ) => {
        $(#[$meta])*
        #[derive(::clap::Parser, Debug)]
        $vis struct $name {
            $(
                $(#[$field_meta])*
                $field_vis $field_name: $field_ty,
            )*

            /// Output format.
            #[arg(long, default_value = "text", help = "Output format. type:enum[text|json|table]")]
            pub output: $crate::OutputFormat,

            /// Describe actions without executing.
            #[arg(long, default_value_t = false, help = "Describe actions without executing. type:bool")]
            pub dry_run: bool,
        }
    };

    // Without dry_run (idempotent commands)
    (
        $(#[$meta:meta])*
        $vis:vis struct $name:ident {
            $(
                $(#[$field_meta:meta])*
                $field_vis:vis $field_name:ident : $field_ty:ty
            ),* $(,)?
        }
    ) => {
        $(#[$meta])*
        #[derive(::clap::Parser, Debug)]
        $vis struct $name {
            $(
                $(#[$field_meta])*
                $field_vis $field_name: $field_ty,
            )*

            /// Output format.
            #[arg(long, default_value = "text", help = "Output format. type:enum[text|json|table]")]
            pub output: $crate::OutputFormat,
        }
    };
}
