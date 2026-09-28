//! Dialect and Schema Inference Heuristics.

use crate::parser::{Dialect, ResilientParser};
use std::collections::HashMap;

const CANDIDATE_DELIMITERS: &[u8] = b",;\t|";

/// Infers the most likely delimiter from a byte sample.
pub fn sniff_delimiter(sample: &[u8]) -> u8 {
    let mut best_delimiter = b',';
    let mut best_score = -1.0;

    for &candidate in CANDIDATE_DELIMITERS {
        let score = evaluate_delimiter_consistency(sample, candidate);
        if score > best_score {
            best_score = score;
            best_delimiter = candidate;
        }
    }

    best_delimiter
}

/// Evaluates how consistently a candidate delimiter divides rows in the sample.
fn evaluate_delimiter_consistency(sample: &[u8], delimiter: u8) -> f64 {
    let dialect = Dialect {
        delimiter,
        repair_quotes: true,
        ..Default::default()
    };

    let mut parser = ResilientParser::new(sample, dialect);
    let mut row_lengths = Vec::new();

    // Check up to 50 rows
    while let Some(row) = parser.next_row() {
        if !row.is_empty() && (row.len() > 1 || !row[0].trim().is_empty()) {
            row_lengths.push(row.len());
        }
        if row_lengths.len() >= 50 {
            break;
        }
    }

    if row_lengths.len() < 2 {
        return 0.0;
    }

    // Find the mode (most common column count)
    let mut frequency = HashMap::new();
    for &len in &row_lengths {
        *frequency.entry(len).or_insert(0) += 1;
    }

    let mut max_freq = 0;
    let mut mode_len = 0;
    for (&len, &count) in &frequency {
        if count > max_freq && len > 1 {
            max_freq = count;
            mode_len = len;
        }
    }

    if mode_len <= 1 {
        return 0.0;
    }

    // Score is proportional to consistency: (rows matching mode / total rows) * log(columns)
    let consistency_ratio = (max_freq as f64) / (row_lengths.len() as f64);
    let col_bonus = (mode_len as f64).ln().max(1.0);

    consistency_ratio * col_bonus
}

/// Infers the expected column count by determining the statistical mode across rows.
pub fn infer_column_count(sample: &[u8], delimiter: u8) -> usize {
    let dialect = Dialect::new(delimiter);
    let mut parser = ResilientParser::new(sample, dialect);
    let mut counts = HashMap::new();
    let mut total_rows = 0;

    while let Some(row) = parser.next_row() {
        if !row.is_empty() && !(row.len() == 1 && row[0].trim().is_empty()) {
            *counts.entry(row.len()).or_insert(0) += 1;
            total_rows += 1;
        }
        if total_rows >= 100 {
            break;
        }
    }

    counts
        .into_iter()
        .max_by_key(|&(_, count)| count)
        .map(|(len, _)| len)
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sniff_comma() {
        let data = b"id,name,role\n1,Alice,Engineer\n2,Bob,Manager\n3,Charlie,Designer";
        assert_eq!(sniff_delimiter(data), b',');
    }

    #[test]
    fn test_sniff_semicolon() {
        let data = b"id;name;city;code\n1;Alice;Madrid;28001\n2;Bob;Barcelona;08001";
        assert_eq!(sniff_delimiter(data), b';');
    }

    #[test]
    fn test_sniff_pipe() {
        let data = b"order_id|customer|amount\n1001|John Doe|54.20\n1002|Jane Smith|120.00";
        assert_eq!(sniff_delimiter(data), b'|');
    }

    #[test]
    fn test_infer_columns() {
        let data = b"a,b,c\n1,2,3\n4,5,6\n7,8,9,extra\n10,11,12";
        // Mode is 3 columns
        assert_eq!(infer_column_count(data, b','), 3);
    }
}
