# Core Perl dependencies for bff-tools and validator

requires 'JSON::XS';                # JSON handling
requires 'Path::Tiny';              # File I/O
requires 'Term::ANSIColor';         # Colored CLI output
requires 'YAML::XS';                # YAML parsing
requires 'PerlIO::gzip';            # Gzip operations
requires 'Data::Structure::Util';   # Data structure helpers
requires 'List::MoreUtils';         # Internal VCF processing helpers
requires 'File::Which';             # bff-validator
requires 'JSON::Validator';         # bff-validator
requires 'Text::CSV_XS';            # bff-validator

# Optional Perl dependencies for extra utilities under utils/
requires 'Mojolicious';             # bff-portal / bff-queue
requires 'MongoDB';                 # bff-portal
requires 'Minion';                  # bff-queue
requires 'Minion::Backend::SQLite'; # bff-queue
