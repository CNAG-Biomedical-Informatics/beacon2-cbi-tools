package BFF::Output;

use strict;
use warnings;
use feature qw(say);
use Exporter 'import';
use Path::Tiny qw(path);
use Term::ANSIColor qw(:constants);
use File::Spec;

our @EXPORT_OK = qw(
  print_run_summary
  print_start_banner
  print_pipeline_status
  print_finish_banner
  format_duration
);

my $ARROW = '=>';

sub print_run_summary {
    my (%args) = @_;
    my $arg           = $args{arg}           || {};
    my $config        = $args{config}        || {};
    my $param         = $args{param}         || {};
    my $version       = $args{version}       || '';
    my $bfftools_path = $args{bfftools_path} || '';
    my $author        = $args{author}        || '';
    my $license       = $args{license}       || '';
    my $no_emoji      = $args{no_emoji}      || 0;

    _section( 'BFF-Tools ' . $version, CYAN );
    _row( 'Executable', _short_path($bfftools_path) );
    _row( 'Mode',       $arg->{mode} );
    _row( 'Input',      _short_path( $arg->{inputfile} ) );
    _row( 'Project',    _short_path( $param->{projectdir} ) );
    _row( 'Run ID',     $param->{jobid} );
    _row( 'Genome',     $param->{genome} );
    _row( 'Dataset',    $param->{datasetid} );
    _row( 'Threads',    defined $arg->{threads} ? $arg->{threads} : $param->{threadsless} );
    print "\n";

    _section( 'Details', YELLOW );
    _row( 'Author',  $author );
    _row( 'License', $license );
    _row( 'Config',  _short_path( $arg->{configfile} ) );
    _row( 'Params',  _short_path( $arg->{paramfile} ) );
    _row( 'Log',     _short_path( $param->{log} ) );
    _row( 'Emoji',   $no_emoji ? 'disabled' : 'enabled' );
    print "\n";

    _print_section_map( 'Arguments', YELLOW, _args_map($arg) );
    _print_section_map( 'Resolved Configuration', BLUE, $config );

    my %display_param = %{$param};
    for my $nested (qw(pipeline bff)) {
        next unless exists $display_param{$nested};
        $display_param{$nested} = 'See ' . _plain( $param->{log} );
    }
    _print_section_map( 'Input Parameters', GREEN, \%display_param );
}

sub print_start_banner {
    _section( 'Starting BFF-Tools', CYAN );
    say '  Pipeline execution begins now';
    print "\n";
}

sub print_pipeline_status {
    my (%args) = @_;
    my $pipeline = $args{pipeline} || '(undef)';
    my $emoji    = $args{emoji}    || '';
    my $label    = uc($pipeline);
    my $prefix   = $emoji ne '' ? "$emoji " : '';

    say BOLD . WHITE . '  ' . $prefix . $label . RESET;
}

sub print_finish_banner {
    my (%args) = @_;
    my $no_emoji = $args{no_emoji} || 0;
    my $goodbye  = $args{goodbye}  || '';
    my $runtime  = $args{runtime};
    my $verbose  = $args{verbose} || 0;

    _section( 'BFF-Tools Finished', GREEN );
    _row( 'Status',   'OK' );
    _row( 'Runtime',  format_duration($runtime) );
    _row( 'Farewell', ( $no_emoji ? '' : '👋 ' ) . $goodbye );
    _row( 'Date', scalar localtime() ) if $verbose;
    print "\n";
}

sub format_duration {
    my ($seconds) = @_;
    $seconds = 0 if !defined $seconds;
    my $total = int( $seconds + 0.5 );
    $total = 0 if $total < 0;
    my $hours = int( $total / 3600 );
    my $mins  = int( ( $total % 3600 ) / 60 );
    my $secs  = $total % 60;

    return "${hours}h ${mins}m ${secs}s" if $hours;
    return "${mins}m ${secs}s" if $mins;
    return "${secs}s";
}

sub _args_map {
    my ($arg) = @_;
    my %map = ( mode => $arg->{mode} );
    my @arg_keys = qw(
      inputfile
      configfile
      paramfile
      threads
      debug
      verbose
      nocolor
      noemoji
      projectdir-override
    );
    my @flags = qw(i c p t debug verbose nc ne po);

    for my $idx ( 0 .. $#arg_keys ) {
        my $key = $arg_keys[$idx];
        next if !defined $arg->{$key} || $arg->{$key} eq q{};
        $map{ '--' . $flags[$idx] } = $arg->{$key};
    }
    return \%map;
}

sub _print_section_map {
    my ( $title, $color, $data ) = @_;
    _section( $title, $color );

    my @keys = sort keys %{$data};
    if ( !@keys ) {
        print "\n";
        return;
    }

    my $max_key = 0;
    for my $key (@keys) {
        my $length = length $key;
        $max_key = $length if $length > $max_key;
    }

    for my $key (@keys) {
        say '  '
          . sprintf( "%-*s", $max_key, $key ) . ' '
          . $ARROW . ' '
          . _plain( $data->{$key} );
    }
    print "\n";
}

sub _section {
    my ( $title, $color ) = @_;
    say BOLD . $color . $title . RESET;
}

sub _row {
    my ( $label, $value ) = @_;
    say '  ' . sprintf( "%-12s", $label ) . ' ' . $ARROW . ' ' . _plain($value);
}

sub _plain {
    my ($value) = @_;
    return '(undef)' if !defined $value;
    return '(undef)' if !ref($value) && $value eq q{};
    return $value if !ref($value);
    return path($value)->stringify if ref($value) eq 'Path::Tiny';
    return "$value";
}

sub _short_path {
    my ($value) = @_;
    return '(undef)' if !defined $value || $value eq q{};

    my $path = path($value);
    my $display = $path->stringify;

    eval {
        my $home = path($ENV{HOME})->realpath->stringify;
        my $real_path = $path->realpath->stringify;
        my @home = grep { length } File::Spec->splitdir($home);
        my @real = grep { length } File::Spec->splitdir($real_path);
        my $matches = @home <= @real;

        if ($matches) {
            for my $idx ( 0 .. $#home ) {
                if ( $home[$idx] ne $real[$idx] ) {
                    $matches = 0;
                    last;
                }
            }
        }

        if ($matches) {
            my @tail = @real[ scalar(@home) .. $#real ];
            $display = @tail ? path( '~', @tail )->stringify : '~';
            return 1;
        }
        return 1;
    };

    my @parts = grep { length } File::Spec->splitdir( $path->stringify );
    if ( @parts > 4 ) {
        $display = path( '...', @parts[ @parts - 3 .. @parts - 1 ] )->stringify;
    }

    return $display;
}

1;
