#!/usr/bin/env perl
#
#   Script to transform dataTables-JSON to HTML
#
#   Version taken from $beacon
#
#   Copyright (C) 2021-2022 Manuel Rueda - CRG
#   Copyright (C) 2023-2025 Manuel Rueda - CNAG (manuel.rueda@cnag.eu)
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <https://www.gnu.org/licenses/>.
#
#   If this program helps you in your research, please cite.
#
#   Last Modified: Dec/23/2025
#
#   Clinician-friendly improvements:
#     - Sticky "Quick filters" bar with clear button
#     - Optional filters:
#         (1) clinicalRelevance matches /pathogenic/i
#         (2) biosampleId contains homozygous ALT genotype (1/1 or 1|1)
#       If both toggles are ON, both must match (AND).
#     - Optional visual scan aid: highlight rows with Pathogenic clinicalRelevance
#       (even when filtering is OFF)
#     - Per-tab counter: "Showing X of Y variants" (updates on draw)
#
#   JSON expected: { "data": [ [..row..], ... ] }
#   DataTables stack assumed: legacy (TableTools/ColVis/ColReorder) -> DataTables 1.9-style init.

use strict;
use warnings;
use autodie;
use Getopt::Long;
use Pod::Usage;
use File::Basename;
use feature qw(say);

#### Main ####
json2html();
exit;

sub json2html {
    my $version        = '2.0.11';
    my @browser_fields = qw(
      variantInternalId assemblyId refseqId position referenceBases alternateBases
      QUAL FILTER variantType genomicHGVSId geneIds molecularEffects aminoacidChanges
      annotationImpact conditionId dbSNP ClinVar clinicalRelevance biosampleId
    );

    GetOptions(
        'id=s'          => \my $id,
        'assets-dir=s'  => \my $assets_dir,
        'panel-dir=s'   => \my $panel_dir,
        'project-dir=s' => \my $project_dir,
        'help|?'        => \my $help,
        'man'           => \my $man,
        'debug=i'       => \my $debug,
        'verbose'       => \my $verbose,
        'version|v'     => sub { say "$0 Version $version"; exit; }
    ) or pod2usage(2);

    pod2usage(1)                              if $help;
    pod2usage( -verbose => 2, -exitval => 0 ) if $man;

    pod2usage(
        -message => "Please specify a valid id with -id <id>\n",
        -exitval => 1
    ) unless ( $id && $id =~ /\w+/ );

    pod2usage(
        -message => "Please specify a valid --panel-dir value\n",
        -exitval => 1
    ) unless ( $panel_dir && $panel_dir =~ /\w+/ );

    pod2usage(
        -message => "Please specify a valid --assets-dir value\n",
        -exitval => 1
    ) unless ( $assets_dir && $assets_dir =~ /\w+/ );

    my @panel_files = glob("$panel_dir/*.lst");
    my %panel_counts;

    for my $panel_file (@panel_files) {
        my $count = 0;
        open( my $fh, '<', $panel_file );
        $count++ while <$fh>;
        close $fh;

        my $key = basename( $panel_file, '.lst' );
        $panel_counts{$key} = $count;
    }

    my @panels = sort keys %panel_counts;

    my $html =
        generate_html_head( $assets_dir, \@panels )
      . generate_navbar()
      . generate_body_start( $project_dir, $id, \%panel_counts )
      . generate_filters()
      . generate_table_tabs( \%panel_counts, \@browser_fields )
      . generate_footer();

    print $html;
    return 1;
}

sub generate_html_head {
    my ( $assets_dir, $panels_ref ) = @_;

    my $html = <<"EOF";
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>BFF Browser</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Beacon Friendly Format Browser">
    <meta name="author" content="Manuel Rueda">

    <!-- Styles -->
    <link rel="icon" href="$assets_dir/img/favicon.ico" type="image/x-icon" />
    <link rel="stylesheet" href="$assets_dir/css/bootstrap.css">
    <link rel="stylesheet" href="$assets_dir/css/bootstrap-responsive.css">
    <link rel="stylesheet" href="$assets_dir/css/main.css">
    <link rel="stylesheet" href="$assets_dir/jsD/media/css/jquery.dataTables.css">
    <link rel="stylesheet" href="$assets_dir/jsD/media/css/dataTables.colReorder.css">
    <link rel="stylesheet" href="$assets_dir/jsD/media/css/dataTables.colVis.css">
    <link rel="stylesheet" href="$assets_dir/jsD/media/css/dataTables.tableTools.css">

    <style type="text/css">
      /* Manual selection always visible */
      tr.row_manual td { background-color: #f9d2d2 !important; }

      /* Auto-highlight scan aid (Pathogenic rows) */
      tr.row_pathogenic td { background-color: #fff2f2 !important; }

      /* Sticky filters bar */
      .filters-bar {
        position: sticky;
        top: 50px; /* below navbar */
        z-index: 999;
        padding: 10px 12px;
        border-radius: 6px;
        margin-top: 10px;
      }

      /* Nicer table headers */
      table.dataTable thead th {
        background: #f7f7f7;
        border-bottom: 1px solid #ddd !important;
      }

      /* Tighter rows */
      table.dataTable tbody td {
        padding-top: 4px;
        padding-bottom: 4px;
      }

      /* Active tab cue */
      .nav-tabs > .active > a,
      .nav-tabs > .active > a:hover {
        font-weight: bold;
      }

      /* Small counter text */
      .table-counter {
        margin: 6px 0 0 0;
        font-size: 12px;
      }
    </style>

    <!-- JavaScript -->
    <script src="$assets_dir/js/jquery.min.js"></script>
    <script src="$assets_dir/js/bootstrap.min.js"></script>
    <script src="$assets_dir/jsD/media/js/jquery.dataTables.min.js"></script>
    <script src="$assets_dir/jsD/media/js/dataTables.colReorder.js"></script>
    <script src="$assets_dir/jsD/media/js/dataTables.colVis.js"></script>
    <script src="$assets_dir/jsD/media/js/dataTables.tableTools.js"></script>
    <script src="$assets_dir/js/jqBootstrapValidation.js"></script>

    <script type="text/javascript" class="init">
EOF

    $html .= generate_shared_filter_and_init_js($panels_ref);

    $html .= <<'EOF';
    </script>
  </head>
EOF
    return $html;
}

sub generate_shared_filter_and_init_js {
    my ($panels_ref) = @_;

    my $panels_js_array = join(
        ", ",
        map { "'" . _js_escape($_) . "'" } sort @$panels_ref
    );

    return <<"EOF";
\$(document).ready(function() {

  var PANELS = [$panels_js_array];

  // 0-based indices:
  // 17 = clinicalRelevance
  // 18 = biosampleId
  var CLINREL_COL   = 17;
  var BIOSAMPLE_COL = 18;

  function stripHtml(x) {
    if (x === null || x === undefined) return '';
    return String(x).replace(/<[^>]*>/g, '').trim();
  }

  function togglePathogenicOn() {
    return (\$('#toggle-only-pathogenic').length && \$('#toggle-only-pathogenic').prop('checked'));
  }

  function toggleHomAltOn() {
    return (\$('#toggle-only-homalt').length && \$('#toggle-only-homalt').prop('checked'));
  }

  function toggleHighlightOn() {
    return (\$('#toggle-highlight-pathogenic').length && \$('#toggle-highlight-pathogenic').prop('checked'));
  }

  function rowIsPathogenic(aData) {
    var cr = stripHtml(aData[CLINREL_COL]);
    return /pathogenic/i.test(cr);
  }

  function rowIsHomAlt(aData) {
    var bs = stripHtml(aData[BIOSAMPLE_COL]);
    return /1[\\/|]1/.test(bs);
  }

  // DataTables 1.9 filter hook
  if (\$.fn.dataTableExt && \$.fn.dataTableExt.afnFiltering) {
    \$.fn.dataTableExt.afnFiltering.push(function(oSettings, aData, iDataIndex) {

      var pOn = togglePathogenicOn();
      var hOn = toggleHomAltOn();
      if (!pOn && !hOn) return true;

      if (pOn && !rowIsPathogenic(aData)) return false;
      if (hOn && !rowIsHomAlt(aData))     return false;

      return true;
    });
  }

  var DT = {};

  function updateCounter(panel, dtApi) {
    try {
      var s = dtApi.fnSettings();
      var total   = (s && typeof s.fnRecordsTotal === 'function')   ? s.fnRecordsTotal()   : null;
      var display = (s && typeof s.fnRecordsDisplay === 'function') ? s.fnRecordsDisplay() : null;
      if (total === null || display === null) return;

      var el = \$('#counter-' + panel);
      if (!el.length) return;

      el.html(
        'Showing <strong>' + display + '</strong> of <strong>' + total + '</strong> variants' +
        ((togglePathogenicOn() || toggleHomAltOn()) ? ' <span class="muted">(filters applied)</span>' : '')
      );
    } catch (e) {
      // keep UI alive
    }
  }

  function applyHighlight(panel, dtApi) {
    try {
      var nodes = dtApi.fnGetNodes();
      for (var i = 0; i < nodes.length; i++) {
        var rowNode = nodes[i];

        if (!toggleHighlightOn()) {
          \$(rowNode).removeClass('row_pathogenic');
          continue;
        }

        var rowData = dtApi.fnGetData(rowNode);
        if (rowIsPathogenic(rowData)) \$(rowNode).addClass('row_pathogenic');
        else \$(rowNode).removeClass('row_pathogenic');
      }
    } catch (e) {
      // keep UI alive
    }
  }

  function initPanel(panel) {
    var tableId = '#table-panel-' + panel;

    var dt = \$(tableId).dataTable({
      "sAjaxSource": panel + ".mod.json",
      "sAjaxDataProp": "data",
      "sServerMethod": "GET",

      "bDeferRender": true,
      "stateSave": true,

      "language": {
        "sSearch": '<span class="icon-search" aria-hidden="true"></span>',
        "lengthMenu": "Show _MENU_ variants",
        "sInfo": "Showing _START_ to _END_ of _TOTAL_ variants",
        "sInfoFiltered": " (filtered from _MAX_ variants)"
      },

      "order": [[ 1, "asc" ]],
      "search": { "regex": true },

      "aoColumnDefs": [
        { "visible": false, "targets": [ 0, 1, 6, 7, 9, 12, 13, 15, 14, 18 ] }
      ],

      "dom": 'CRT<"clear">lfrtip',
      "colVis": { "showAll": "Show all", "showNone": "Show none" },
      "tableTools": {
        "aButtons": [
          { "sExtends": "print", "sButtonText": '<span class="icon-print" aria-hidden="true"></span>' }
        ]
      },

      // IMPORTANT FIX:
      // Use oSettings.oInstance (available during init) instead of the dt var
      "fnInitComplete": function(oSettings) {
        var api = (oSettings && oSettings.oInstance) ? oSettings.oInstance : dt;
        updateCounter(panel, api);
        applyHighlight(panel, api);
      },

      "fnDrawCallback": function(oSettings) {
        var api = (oSettings && oSettings.oInstance) ? oSettings.oInstance : dt;
        updateCounter(panel, api);
        applyHighlight(panel, api);
      }
    });

    DT[panel] = dt;

    \$(tableId + ' tbody').on('click', 'tr', function() {
      \$(this).toggleClass('row_manual');
    });
  }

  for (var i = 0; i < PANELS.length; i++) initPanel(PANELS[i]);

  function redrawAll() {
    for (var i = 0; i < PANELS.length; i++) {
      var p = PANELS[i];
      if (DT[p] && typeof DT[p].fnDraw === 'function') DT[p].fnDraw();
    }
  }

  \$('#toggle-only-pathogenic').on('change', redrawAll);
  \$('#toggle-only-homalt').on('change', redrawAll);
  \$('#toggle-highlight-pathogenic').on('change', redrawAll);

  \$('#btn-clear-filters').on('click', function(e) {
    e.preventDefault();
    \$('#toggle-only-pathogenic').prop('checked', false);
    \$('#toggle-only-homalt').prop('checked', false);
    redrawAll();
  });

});
EOF
}

sub generate_navbar {
    my $navbar = <<'EOF';
  <body class="dt-example">
    <!-- NAVBAR -->
    <div class="navbar navbar-inverse navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container">
          <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </a>
          <a class="brand" href="#">BFF Browser - Genomic Variations</a>
          <div class="nav-collapse collapse">
            <ul class="nav">
              <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                  Help <b class="caret"></b>
                </a>
                <ul class="dropdown-menu">
                  <li class="nav-header">Help</li>
                  <li>
                    <a href="https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools/tree/main/utils/bff_browser">
                      <span class="icon-question-sign"></span> Help Page
                    </a>
                  </li>
                  <li class="divider"></li>
                  <li class="nav-header">FAQs</li>
                  <li>
                    <a href="https://cnag-biomedical-informatics.github.io/beacon2-cbi-tools/help/faq/">
                      <span class="icon-question-sign"></span> FAQs Page
                    </a>
                  </li>
                </ul>
              </li>
              <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                  Links <b class="caret"></b>
                </a>
                <ul class="dropdown-menu">
                  <li class="nav-header">Contact</li>
                  <li>
                    <a href="mailto:manuel.rueda\@cnag.eu">
                      <span class="icon-envelope"></span> Author
                    </a>
                  </li>
                  <li class="divider"></li>
                  <li class="nav-header">Links</li>
                  <li>
                    <a href="https://www.cnag.eu">
                      <span class="icon-home"></span> CNAG
                    </a>
                  </li>
                </ul>
              </li>
            </ul>
          </div><!--/.nav-collapse -->
        </div>
      </div>
    </div>
EOF
    return $navbar;
}

sub generate_body_start {
    my ( $project_dir, $id, $panel_counts_ref ) = @_;

    my $html = qq(  <div class="container">\n);

    foreach my $panel ( sort keys %$panel_counts_ref ) {
        my $panel_uc = ucfirst($panel);
        $html .= qq(    <a class="btn pull-right" href="./$panel.json"><i class="icon-download"></i> $panel_uc JSON</a>\n);
    }

    $html .= qq(    <h4>Project &#9658; $project_dir</h4>\n);
    $html .= qq(    <h3>Job ID &#9658; $id &#9658; genomicVariationsVcf</h3>\n);
    $html .= qq(    <p>Displaying variants with <strong>Annotation Impact</strong> values equal to <strong>HIGH | MODERATE</strong></p>\n);

    return $html;
}

sub generate_filters {
    return <<'EOF';
    <div class="well filters-bar">
      <div class="row-fluid">
        <div class="span9">
          <h4 style="margin:0 0 6px 0;">Quick filters</h4>

          <label class="checkbox" style="margin-bottom:6px;">
            <input type="checkbox" id="toggle-only-pathogenic">
            <strong>Clinical relevance:</strong>
            show only <span class="label label-important">Pathogenic</span>
            <span class="muted">(matches <code>clinicalRelevance</code>, case-insensitive)</span>
          </label>

          <label class="checkbox" style="margin-bottom:6px;">
            <input type="checkbox" id="toggle-only-homalt">
            <strong>Genotype:</strong>
            show only <span class="label label-info">Homozygous ALT</span>
            <span class="muted">(<code>1/1</code> or <code>1|1</code> in <code>biosampleId</code>)</span>
          </label>

          <label class="checkbox" style="margin-bottom:0;">
            <input type="checkbox" id="toggle-highlight-pathogenic" checked>
            <strong>Scan aid:</strong>
            softly highlight rows with <span class="label label-important">Pathogenic</span>
            <span class="muted">(no filtering)</span>
          </label>
        </div>

        <div class="span3" style="text-align:right;">
          <button class="btn btn-small" id="btn-clear-filters" style="margin-top:22px;">
            <i class="icon-remove"></i> Clear filters
          </button>
        </div>
      </div>
    </div>
EOF
}

sub generate_table_tabs {
    my ( $panel_counts_ref, $header_ref ) = @_;

    my @panels = sort keys %$panel_counts_ref;

    my $html = qq(    <ul class="nav nav-tabs">\n);
    for my $i ( 0 .. $#panels ) {
        my $panel    = $panels[$i];
        my $panel_uc = ucfirst($panel);
        my $active   = $i == 0 ? 'active' : '';
        $html .= qq(      <li class="$active"><a href="#tab-panel-$panel" data-toggle="tab">$panel_uc panel - $panel_counts_ref->{$panel} genes</a></li>\n);
    }
    $html .= qq(    </ul>\n);

    $html .= qq(    <div id="myTabContent" class="tab-content">\n);
    for my $i ( 0 .. $#panels ) {
        my $panel = $panels[$i];
        my $active_class = $i == 0 ? 'active' : '';
        $html .= generate_table( $panel, $active_class, $header_ref );
    }
    $html .= qq(    </div>\n);

    return $html;
}

sub generate_table {
    my ( $panel, $active_class, $header_ref ) = @_;

    my $html = qq(      <div class="tab-pane fade in $active_class" id="tab-panel-$panel">\n);
    $html .= qq(        <div class="table-counter muted" id="counter-$panel">Loading variants…</div>\n);
    $html .= qq(        <!-- TABLE -->\n);
    $html .= qq(        <table id="table-panel-$panel" class="display table table-hover table-condensed">\n);
    $html .= qq(          <thead>\n            <tr>\n);

    foreach my $field (@$header_ref) {
        $html .= qq(              <th>$field</th>\n);
    }

    $html .= qq(            </tr>\n          </thead>\n        </table>\n      </div>\n);
    return $html;
}

sub generate_footer {
    my $html = <<'EOF';
      <br /><p class="pagination-centered">BFF Browser - Genomic Variations</p>
      <hr>
      <!-- FOOTER -->
      <footer>
          <p>&copy; 2021-2025 CNAG | Barcelona, Spain </p>
      </footer>
    </div><!-- /.container -->
  </body>
</html>
EOF
    return $html;
}

sub _js_escape {
    my ($s) = @_;
    $s =~ s/\\/\\\\/g;
    $s =~ s/'/\\'/g;
    $s =~ s/\r//g;
    $s =~ s/\n//g;
    return $s;
}

__END__

=head1 NAME

bff2html: A script to transform dataTables-JSON to HTML

=head1 SYNOPSIS

bff2html.pl -id your_id -assets-dir /path/foo/bar -panel-dir /path/web [-options]

     Arguments:                       
       -id              ID (string)
       -assets-dir      /path to directory with css, img and stuff.
       -panel-dir       /path to directory with gene panels

     Options:
       -h|help         Brief help message
       -man            Full documentation
       -debug          Print debugging (from 1 to 5, being 5 max)
       -verbose        Verbosity on

=head1 CITATION

The author requests that any published work that utilizes B<B2RI> includes a cite to the following reference:

Rueda, M, Ariosa R. "Beacon v2 Reference Implementation: a toolkit to enable federated sharing of genomic and phenotypic data". I<Bioinformatics>, btac568, https://doi.org/10.1093/bioinformatics/btac568

=head1 SUMMARY

Clinician-friendly HTML viewer for BFF tables.

Adds:
  - Sticky Quick filters
  - Filter 1: clinicalRelevance matches /pathogenic/i
  - Filter 2: biosampleId contains genotype 1/1 or 1|1 (homozygous ALT)
  - Soft highlight of Pathogenic rows (scan aid)
  - Per-tab counter "Showing X of Y variants"

=head1 HOW TO RUN BFF2HTML

...

=head1 AUTHOR 

Written by Manuel Rueda, PhD. Info about CNAG can be found at L<https://www.cnag.eu>.

=head1 REPORTING BUGS

Report bugs or comments to <manuel.rueda@cnag.eu>.

=head1 COPYRIGHT

This PERL file is copyrighted. See the LICENSE file included in this distribution.

=cut
