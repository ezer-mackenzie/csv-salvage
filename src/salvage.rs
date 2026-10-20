//! Salvage Engine: Row alignment, quote repair, and quarantine routing.

use crate::error::SalvageError;
use crate::heuristics::{infer_column_count, sniff_delimiter};
use crate::parser::{Dialect, ResilientParser};
use memmap2::MmapOptions;
use rayon::prelude::*;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;

const PARALLEL_NORMALIZATION_THRESHOLD: usize = 1024;

type SalvageFileRows = (Vec<Vec<String>>, Vec<QuarantineRecord>, SalvageSummary);

#[derive(Debug, Clone)]
pub struct SalvageOptions {
    pub delimiter: Option<u8>,
    pub quote_char: u8,
    pub repair_quotes: bool,
    pub fill_ragged_rows: bool,
    pub merge_overflow: bool,
    pub expected_columns: Option<usize>,
}

impl Default for SalvageOptions {
    fn default() -> Self {
        Self {
            delimiter: None, // Auto-detect
            quote_char: b'"',
            repair_quotes: true,
            fill_ragged_rows: true,
            merge_overflow: true,
            expected_columns: None,
        }
    }
}

/// Statistics and diagnostics summary produced after a salvage operation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SalvageSummary {
    pub total_rows: usize,
    pub salvaged_rows: usize,
    pub repaired_rows: usize,
    pub quarantined_rows: usize,
    pub detected_delimiter: char,
    pub inferred_columns: usize,
}

/// A discarded row routed to quarantine.
#[derive(Debug, Clone)]
pub struct QuarantineRecord {
    pub line_number: usize,
    pub raw_tokens: Vec<String>,
    pub reason: String,
}

enum RowOutcome {
    Salvaged(Vec<String>, bool),
    Quarantined(QuarantineRecord),
}

fn normalize_row(
    mut row: Vec<String>,
    line_number: usize,
    expected_columns: usize,
    delimiter: u8,
    fill_ragged_rows: bool,
    merge_overflow: bool,
) -> RowOutcome {
    if expected_columns == 0 || row.len() == expected_columns {
        return RowOutcome::Salvaged(row, false);
    }

    if row.len() < expected_columns {
        if fill_ragged_rows {
            row.resize(expected_columns, String::new());
            RowOutcome::Salvaged(row, true)
        } else {
            RowOutcome::Quarantined(QuarantineRecord {
                line_number,
                raw_tokens: row,
                reason: format!("Row has too few columns (expected {})", expected_columns),
            })
        }
    } else if merge_overflow {
        let overflow = row.split_off(expected_columns - 1);
        row.push(overflow.join(&(delimiter as char).to_string()));
        RowOutcome::Salvaged(row, true)
    } else {
        RowOutcome::Quarantined(QuarantineRecord {
            line_number,
            raw_tokens: row,
            reason: format!("Row has extra columns (expected {})", expected_columns),
        })
    }
}

/// Replaces / escapes fields to conform to standard RFC-4180 CSV output.
pub fn format_csv_field(field: &str, delimiter: u8, quote_char: u8) -> String {
    let quote = quote_char as char;
    let delim = delimiter as char;

    let needs_quotes = field.contains(quote)
        || field.contains(delim)
        || field.contains('\n')
        || field.contains('\r');

    if needs_quotes {
        let escaped = field.replace(quote, &format!("{}{}", quote, quote));
        format!("{}{}{}", quote, escaped, quote)
    } else {
        field.to_string()
    }
}

/// Formats a complete row as an RFC-4180 CSV line with \n.
pub fn format_csv_row(row: &[String], delimiter: u8, quote_char: u8) -> String {
    let mut out = String::new();
    for (i, field) in row.iter().enumerate() {
        if i > 0 {
            out.push(delimiter as char);
        }
        out.push_str(&format_csv_field(field, delimiter, quote_char));
    }
    out.push('\n');
    out
}

/// Core function to salvage a byte slice into memory.
pub fn salvage_slice(
    input: &[u8],
    options: &SalvageOptions,
) -> (Vec<Vec<String>>, Vec<QuarantineRecord>, SalvageSummary) {
    if input.is_empty() {
        return (
            Vec::new(),
            Vec::new(),
            SalvageSummary {
                total_rows: 0,
                salvaged_rows: 0,
                repaired_rows: 0,
                quarantined_rows: 0,
                detected_delimiter: ',',
                inferred_columns: 0,
            },
        );
    }

    let delimiter = options.delimiter.unwrap_or_else(|| sniff_delimiter(input));
    let expected_cols = options
        .expected_columns
        .unwrap_or_else(|| infer_column_count(input, delimiter));

    let dialect = Dialect {
        delimiter,
        quote_char: options.quote_char,
        escape_char: None,
        repair_quotes: options.repair_quotes,
        trim_whitespace: false,
    };

    let mut parser = ResilientParser::new(input, dialect);
    let mut parsed_rows = Vec::new();
    loop {
        let line_number = parser.current_line();
        match parser.next_row() {
            Some(row) => parsed_rows.push((line_number, row)),
            None => break,
        }
    }
    let total_rows = parsed_rows.len();
    let normalize = |(line_number, row)| {
        normalize_row(
            row,
            line_number,
            expected_cols,
            delimiter,
            options.fill_ragged_rows,
            options.merge_overflow,
        )
    };
    let outcomes: Vec<RowOutcome> = if total_rows >= PARALLEL_NORMALIZATION_THRESHOLD {
        parsed_rows.into_par_iter().map(normalize).collect()
    } else {
        parsed_rows.into_iter().map(normalize).collect()
    };

    let mut salvaged = Vec::with_capacity(total_rows);
    let mut quarantine = Vec::new();
    let mut repaired_rows = 0;
    for outcome in outcomes {
        match outcome {
            RowOutcome::Salvaged(row, repaired) => {
                repaired_rows += usize::from(repaired);
                salvaged.push(row);
            }
            RowOutcome::Quarantined(record) => quarantine.push(record),
        }
    }

    let summary = SalvageSummary {
        total_rows,
        salvaged_rows: salvaged.len(),
        repaired_rows,
        quarantined_rows: quarantine.len(),
        detected_delimiter: delimiter as char,
        inferred_columns: expected_cols,
    };

    (salvaged, quarantine, summary)
}

pub(crate) fn salvage_file_rows(
    input_path: impl AsRef<Path>,
    options: &SalvageOptions,
) -> Result<SalvageFileRows, SalvageError> {
    let input_file = File::open(input_path)?;
    let mapped = if input_file.metadata()?.len() == 0 {
        None
    } else {
        // SAFETY: The mapping is read-only and is consumed before this function
        // returns. Callers must not modify the input file during this operation.
        Some(unsafe { MmapOptions::new().map(&input_file)? })
    };
    let input = mapped.as_deref().unwrap_or_default();
    let result = salvage_slice(input, options);

    drop(mapped);
    drop(input_file);
    Ok(result)
}

/// Reads a corrupted CSV file, repairs it, and writes an RFC-4180 clean file + optional quarantine log.
///
/// The input file must not be modified while the operation is running.
pub fn salvage_file(
    input_path: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
    quarantine_path: Option<impl AsRef<Path>>,
    options: &SalvageOptions,
) -> Result<SalvageSummary, SalvageError> {
    let (salvaged, quarantine, summary) = salvage_file_rows(input_path, options)?;

    // Write cleaned output file
    let out_file = File::create(output_path.as_ref())?;
    let mut out_writer = BufWriter::new(out_file);
    let delim = summary.detected_delimiter as u8;
    let quote = options.quote_char;

    for row in &salvaged {
        let line = format_csv_row(row, delim, quote);
        out_writer.write_all(line.as_bytes())?;
    }
    out_writer.flush()?;

    // Write quarantine log if requested and there are quarantined records
    if let Some(q_path) = quarantine_path {
        let q_file = File::create(q_path.as_ref())?;
        let mut q_writer = BufWriter::new(q_file);
        q_writer.write_all(b"line,reason,raw_content\n")?;

        for rec in &quarantine {
            let raw_content = rec.raw_tokens.join(&String::from(delim as char));
            let line = format!(
                "{},\"{}\",\"{}\"\n",
                rec.line_number,
                rec.reason.replace('"', "\"\""),
                raw_content.replace('"', "\"\"")
            );
            q_writer.write_all(line.as_bytes())?;
        }
        q_writer.flush()?;
    }

    Ok(summary)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_salvage_slice_orphan_quote_and_ragged_rows() {
        let data = b"id,name,price\n1,\"15\" Monitor\",49.99\n2,Keyboard\n3,Mouse,12.50,Extra,Data";
        let options = SalvageOptions {
            delimiter: Some(b','),
            expected_columns: Some(3),
            fill_ragged_rows: true,
            merge_overflow: true,
            ..Default::default()
        };

        let (salvaged, quarantine, summary) = salvage_slice(data, &options);

        assert_eq!(summary.total_rows, 4); // header + 3 rows
        assert_eq!(summary.salvaged_rows, 4);
        assert_eq!(quarantine.len(), 0);

        // Row 1: Header
        assert_eq!(salvaged[0], vec!["id", "name", "price"]);
        // Row 2: Repaired quote
        assert_eq!(salvaged[1], vec!["1", "15\" Monitor", "49.99"]);
        // Row 3: Padded short row
        assert_eq!(salvaged[2], vec!["2", "Keyboard", ""]);
        // Row 4: Merged overflow row
        assert_eq!(salvaged[3], vec!["3", "Mouse", "12.50,Extra,Data"]);
    }

    #[test]
    fn test_parallel_normalization_preserves_row_order_and_source_lines() {
        let mut data = String::from("id,name,role\n");
        for index in 0..PARALLEL_NORMALIZATION_THRESHOLD {
            if index == 10 {
                data.push_str("10,\"person\ncontinued\",role\n");
            } else {
                data.push_str(&format!("{index},person,role\n"));
            }
        }
        data.push_str("short,row\n");
        data.push_str("too,many,columns,here\n");

        let options = SalvageOptions {
            delimiter: Some(b','),
            expected_columns: Some(3),
            fill_ragged_rows: false,
            merge_overflow: false,
            ..Default::default()
        };

        let (salvaged, quarantine, summary) = salvage_slice(data.as_bytes(), &options);

        assert_eq!(summary.total_rows, PARALLEL_NORMALIZATION_THRESHOLD + 3);
        assert_eq!(summary.salvaged_rows, PARALLEL_NORMALIZATION_THRESHOLD + 1);
        assert_eq!(summary.quarantined_rows, 2);
        assert_eq!(salvaged[1], vec!["0", "person", "role"]);
        assert_eq!(
            salvaged.last().unwrap(),
            &vec![
                (PARALLEL_NORMALIZATION_THRESHOLD - 1).to_string(),
                "person".to_string(),
                "role".to_string()
            ]
        );
        assert_eq!(
            quarantine
                .iter()
                .map(|record| record.line_number)
                .collect::<Vec<_>>(),
            vec![
                PARALLEL_NORMALIZATION_THRESHOLD + 3,
                PARALLEL_NORMALIZATION_THRESHOLD + 4
            ]
        );
    }
}
