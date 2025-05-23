#!/usr/bin/env bash
#
#   Script that generates HTML format from BFF
#
#   Last Modified: Jan/10/2025
#
#   Version taken from $BEACON
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

set -euo pipefail
export LC_ALL=C
#____WRAPPER_VARIABLES____#

function usage {

    USAGE="""
    Usage: $0 <../vcf/genomicVariationsVcf.json.gz> <PROJECTDIR> <ID>
    """
    echo "$USAGE"
    exit 1
}

# Check #arguments
if [ $# -lt 3 ]; then
    usage
fi

# Load arguments
INPUT_BFF=$1
PROJECTDIR=$2
ID=$3

# Set patterns 
PATTERN_HIGH='HIGH' # it only appears in field 'Annotation Impact', otherwise use awk with #col (see below)
PATTERN_MODERATE='MODERATE' # Idem
PATTERN="${PATTERN_HIGH}.${PATTERN_MODERATE}"

# Step 1: Parse BFF according to gene panels
echo "# Running BFF2JSON"
for PANEL in $PANELDIR/*.lst
do
    BASE=$(basename "$PANEL" .lst)
    # NB:
    zgrep -F -w -e $PATTERN_HIGH -e $PATTERN_MODERATE "$INPUT_BFF" | grep -F -w -f "$PANEL" > "$ID"."$BASE".$PATTERN.json || echo "Nothing found for $BASE"
    $BFF2JSON -i "$ID"."$BASE".$PATTERN.json -f json | jq -s . > "$BASE".json || echo "Could not run $BFF2JSON -f json for $BASE"  # jq needed
    $BFF2JSON -i "$ID"."$BASE".$PATTERN.json -f json4html > "$BASE".mod.json || echo "Could not run $BFF2JSON -f json4html for $BASE"
done

# Step 2: Create HTML for JSON
echo "# Running JSON2HTML"
ln -s "$ASSETSDIR" assets # symbolic link for css, etc.
$JSON2HTML --id "$ID" --assets-dir assets --panel-dir "$PANELDIR" --project-dir "$PROJECTDIR" > "$ID".html

cat <<EOF > README.txt
### PREFERRED MODE

# To visualize <$ID.html>:

1. Go to the bff_browser directory:
   cd beacon2-cbi-tools/utils/bff_browser

2. Start the BFF Browser Flask App:
   python3 app.py

3. Open your browser and navigate to:
   http://0.0.0.0:8001/

4. Follow the instructions on the Home page.

---

### ALTERNATIVE MODES

# Option 1: Open <$ID.html> directly in Chromium
chromium --allow-file-access-from-files --disable-web-security $ID.html

# Option 2: Use an HTTP server. Example using Python 3:
python3 -m http.server
EOF

# All done
echo "# Finished OK"
