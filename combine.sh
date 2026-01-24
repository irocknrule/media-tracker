#!/bin/bash

# ==============================================================================
#           Directory File Combiner Script for macOS
# ==============================================================================
#
# Description:
# This script scans for subdirectories in its current location. For each
# subdirectory found, it combines all the files within it into a single,
# master PDF file. The resulting PDFs are stored in a 'combined' directory.
# It also combines all files in the current directory (except itself).
#
# Features:
# - Creates a single PDF from multiple files (PDFs, text, csv, etc.).
# - Intelligently skips directories that have not changed, saving time.
# - Handles filenames with spaces and special characters.
# - Requires 'Ghostscript' (gs) for PDF merging.
# - Uses 'cupsfilter', a standard macOS tool, to convert non-PDF files.
#
# How to Run:
# 1. Save this script as a file, e.g., `combine.sh`.
# 2. Open Terminal and navigate to the parent directory containing your
#    subdirectories (e.g., 'seattle_childrens', 'immunizations').
# 3. Make the script executable: `chmod +x combine.sh`
# 4. Run the script: `./combine.sh`
#
# ==============================================================================

# --- Configuration ---
# The directory where all combined PDF files will be stored.
OUTPUT_DIR="combined"
# The directory to store checksums for tracking changes.
CHECKSUM_DIR="${OUTPUT_DIR}/.checksums"
# Get the script's own name to exclude it from processing
SCRIPT_NAME="$(basename "$0")"


# --- Pre-flight Checks ---
# Check if Ghostscript (gs) is installed, as it's required for merging.
if ! command -v gs &> /dev/null; then
    echo "Error: Ghostscript (gs) is not installed."
    echo "This script requires Ghostscript to merge PDF files."
    echo "Please install it, for example, using Homebrew: 'brew install ghostscript'"
    exit 1
fi

# --- Script Start ---
echo "Starting file combination process..."

# Create the main output and checksum directories if they don't exist.
mkdir -p "$OUTPUT_DIR"
mkdir -p "$CHECKSUM_DIR"
echo "Output will be saved in the '${OUTPUT_DIR}' directory."
echo

# --- Main Processing Loop ---
# Find all subdirectories in the current path (at a depth of 1).
# Exclude the output directory itself from processing.
find . -maxdepth 1 -mindepth 1 -type d -not -name "$OUTPUT_DIR" | while read -r dir; do
    # Get the clean name of the directory (e.g., 'seattle_childrens').
    dir_name=$(basename "$dir")
    output_file="${OUTPUT_DIR}/${dir_name}.pdf"
    checksum_file="${CHECKSUM_DIR}/${dir_name}.sha256"

    echo "--- Processing directory: '${dir_name}' ---"

    # Calculate a single checksum for the contents of the directory.
    # This involves finding all files (excluding .DS_Store), sorting them for
    # consistency, getting their individual SHA256 hashes, and then creating
    # a final hash of that list. This robustly detects any change.
    current_checksum=$(find "$dir" -type f -not -name '.DS_Store' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')

    # Check if a previous checksum exists and if it matches the current one.
    if [ -f "$checksum_file" ] && [ "$(cat "$checksum_file")" == "$current_checksum" ]; then
        echo "No changes detected. '${output_file}' is up to date. Skipping."
        echo
        continue
    fi

    echo "Changes detected. Generating a new combined PDF..."

    # Create a secure, temporary directory to stage the files for merging.
    temp_dir=$(mktemp -d)
    # Ensure the temporary directory is removed when the script exits.
    trap 'rm -rf "$temp_dir"' EXIT

    # Find all files in the source directory and prepare them for merging.
    find "$dir" -type f -not -name '.DS_Store' | sort | while read -r file; do
        filename=$(basename "$file")
        # Use a predictable temporary filename
        temp_pdf="${temp_dir}/${filename}.pdf"

        echo "  - Preparing file: $filename"

        # Check the file extension to decide on the conversion strategy.
        if [[ ${file##*.} == "pdf" || ${file##*.} == "PDF" ]]; then
            # If it's already a PDF, just copy it to the temp location.
            cp "$file" "$temp_pdf"
        else
            # For non-PDF files, attempt to convert them to PDF using `cupsfilter`.
            # This is part of the macOS printing system and can handle many file types.
            if cupsfilter "$file" > "$temp_pdf" 2>/dev/null; then
                 : # Successfully converted
            else
                echo "    Warning: Failed to convert '$filename' to PDF. Skipping this file."
            fi
        fi
    done

    # Wait for the file processing sub-shell to finish
    wait

    # Re-read files from the temp directory to pass to ghostscript.
    # This loop correctly handles filenames with spaces or other special characters,
    # preventing the 'undefinedfilename' error.
    pdf_files_to_merge=()
    while IFS= read -r -d '' file; do
        pdf_files_to_merge+=("$file")
    done < <(find "$temp_dir" -name '*.pdf' -print0 | sort -z)


    # Check if we have any actual PDF files to merge.
    if [ ${#pdf_files_to_merge[@]} -gt 0 ]; then
        # Use Ghostscript to merge all staged PDFs into the final output file.
        # The "${pdf_files_to_merge[@]}" syntax ensures each filename is passed as a
        # single, distinct argument to Ghostscript.
        gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile="$output_file" "${pdf_files_to_merge[@]}"

        echo "Successfully updated '${output_file}'"

        # If successful, update the checksum file with the new checksum.
        echo "$current_checksum" > "$checksum_file"
    else
        echo "No valid files were found to combine in '${dir_name}'."
    fi

    # Clean up the temporary directory.
    rm -rf "$temp_dir"
    trap - EXIT # Clear the trap
    echo
done

# --- Process Current Directory Files ---
# Process files in the current directory (excluding the script itself, OUTPUT_DIR, and .DS_Store)
echo "--- Processing current directory ---"

# Get the current directory name for the output file
current_dir_name=$(basename "$(pwd)")
output_file="${OUTPUT_DIR}/${current_dir_name}.pdf"
checksum_file="${CHECKSUM_DIR}/${current_dir_name}.sha256"

# Calculate checksum for files in the current directory (excluding script, OUTPUT_DIR, and .DS_Store)
current_checksum=$(find . -maxdepth 1 -type f -not -name '.DS_Store' -not -name "$SCRIPT_NAME" -not -path "./${OUTPUT_DIR}/*" -print0 | sort -z | xargs -0 shasum -a 256 2>/dev/null | shasum -a 256 | awk '{print $1}')

# Check if we have any files to process (checksum won't be empty if files exist)
if [ -z "$current_checksum" ]; then
    echo "No files found in the current directory (excluding '${SCRIPT_NAME}'). Skipping."
    echo
else
    # Check if a previous checksum exists and if it matches the current one.
    if [ -f "$checksum_file" ] && [ "$(cat "$checksum_file")" == "$current_checksum" ]; then
        echo "No changes detected. '${output_file}' is up to date. Skipping."
        echo
    else
        echo "Changes detected. Generating a new combined PDF..."

        # Create a secure, temporary directory to stage the files for merging.
        temp_dir=$(mktemp -d)
        # Ensure the temporary directory is removed when the script exits.
        trap 'rm -rf "$temp_dir"' EXIT

        # Find all files in the current directory and prepare them for merging.
        # Exclude the script itself, OUTPUT_DIR, and .DS_Store files
        find . -maxdepth 1 -type f -not -name '.DS_Store' -not -name "$SCRIPT_NAME" | sort | while read -r file; do
            filename=$(basename "$file")
            # Use a predictable temporary filename
            temp_pdf="${temp_dir}/${filename}.pdf"

            echo "  - Preparing file: $filename"

            # Check the file extension to decide on the conversion strategy.
            if [[ ${file##*.} == "pdf" || ${file##*.} == "PDF" ]]; then
                # If it's already a PDF, just copy it to the temp location.
                cp "$file" "$temp_pdf"
            else
                # For non-PDF files, attempt to convert them to PDF using `cupsfilter`.
                # This is part of the macOS printing system and can handle many file types.
                if cupsfilter "$file" > "$temp_pdf" 2>/dev/null; then
                     : # Successfully converted
                else
                    echo "    Warning: Failed to convert '$filename' to PDF. Skipping this file."
                fi
            fi
        done

        # Wait for the file processing sub-shell to finish
        wait

        # Re-read files from the temp directory to pass to ghostscript.
        # This loop correctly handles filenames with spaces or other special characters,
        # preventing the 'undefinedfilename' error.
        pdf_files_to_merge=()
        while IFS= read -r -d '' file; do
            pdf_files_to_merge+=("$file")
        done < <(find "$temp_dir" -name '*.pdf' -print0 | sort -z)

        # Check if we have any actual PDF files to merge.
        if [ ${#pdf_files_to_merge[@]} -gt 0 ]; then
            # Use Ghostscript to merge all staged PDFs into the final output file.
            # The "${pdf_files_to_merge[@]}" syntax ensures each filename is passed as a
            # single, distinct argument to Ghostscript.
            gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile="$output_file" "${pdf_files_to_merge[@]}"

            echo "Successfully updated '${output_file}'"

            # If successful, update the checksum file with the new checksum.
            echo "$current_checksum" > "$checksum_file"
        else
            echo "No valid files were found to combine in the current directory."
        fi

        # Clean up the temporary directory.
        rm -rf "$temp_dir"
        trap - EXIT # Clear the trap
        echo
    fi
fi

echo "---"
echo "Script finished. All directories processed."
