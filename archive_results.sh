#!/bin/bash
# Archive mutation results into a single .tar.gz file.
# Usage: ./archive_results.sh [output_dir] [archive_name]

OUTPUT_DIR="${1:-./fuzz_output}"
ARCHIVE_NAME="${2:-rust_twins_mut_results_$(date +%Y%m%d_%H%M%S).tar.gz}"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: $OUTPUT_DIR is not a directory"
    exit 1
fi

RS_COUNT=$(find "$OUTPUT_DIR" -name 'mutated_*.rs' | wc -l | tr -d ' ')
echo "Found $RS_COUNT mutated .rs files in $OUTPUT_DIR"

tar czf "$ARCHIVE_NAME" -C "$(dirname "$OUTPUT_DIR")" "$(basename "$OUTPUT_DIR")"

echo "Archive created: $ARCHIVE_NAME ($(du -h "$ARCHIVE_NAME" | cut -f1))"
