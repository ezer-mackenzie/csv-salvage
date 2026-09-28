pub mod error;
pub mod heuristics;
pub mod parser;
pub mod salvage;

pub use error::SalvageError;
pub use heuristics::{infer_column_count, sniff_delimiter};
pub use parser::{Dialect, ResilientParser};
pub use salvage::{
    QuarantineRecord, SalvageOptions, SalvageSummary as RustSalvageSummary, format_csv_field,
    format_csv_row, salvage_file as rust_salvage_file, salvage_slice,
};

use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::fs::File;
use std::io::Read;

/// Python-exposed summary of a salvage operation.
#[pyclass(name = "SalvageSummary", skip_from_py_object)]
#[derive(Clone)]
pub struct PySalvageSummary {
    #[pyo3(get)]
    pub total_rows: usize,
    #[pyo3(get)]
    pub salvaged_rows: usize,
    #[pyo3(get)]
    pub repaired_rows: usize,
    #[pyo3(get)]
    pub quarantined_rows: usize,
    #[pyo3(get)]
    pub detected_delimiter: String,
    #[pyo3(get)]
    pub inferred_columns: usize,
}

#[pymethods]
impl PySalvageSummary {
    fn __repr__(&self) -> String {
        format!(
            "<SalvageSummary total_rows={} salvaged_rows={} repaired_rows={} quarantined_rows={} delimiter='{}' inferred_columns={}>",
            self.total_rows,
            self.salvaged_rows,
            self.repaired_rows,
            self.quarantined_rows,
            self.detected_delimiter,
            self.inferred_columns
        )
    }

    /// Converts the summary into a native Python dictionary.
    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("total_rows", self.total_rows)?;
        dict.set_item("salvaged_rows", self.salvaged_rows)?;
        dict.set_item("repaired_rows", self.repaired_rows)?;
        dict.set_item("quarantined_rows", self.quarantined_rows)?;
        dict.set_item("detected_delimiter", &self.detected_delimiter)?;
        dict.set_item("inferred_columns", self.inferred_columns)?;
        Ok(dict)
    }
}

impl From<RustSalvageSummary> for PySalvageSummary {
    fn from(s: RustSalvageSummary) -> Self {
        Self {
            total_rows: s.total_rows,
            salvaged_rows: s.salvaged_rows,
            repaired_rows: s.repaired_rows,
            quarantined_rows: s.quarantined_rows,
            detected_delimiter: s.detected_delimiter.to_string(),
            inferred_columns: s.inferred_columns,
        }
    }
}

/// Salvages a corrupted CSV file and writes a clean, standard RFC-4180 file.
///
/// Args:
///     input_path: Path to the corrupted CSV file.
///     output_path: Path where the repaired CSV file will be written.
///     quarantine_path: Optional path to write unrecoverable / quarantined rows.
///     delimiter: Optional single-character delimiter (e.g. "," or ";"). If None, auto-sniffed.
///     quote_char: Optional single-character quote enclosure (default '"').
///     fill_ragged_rows: If True, pads short rows with empty strings. Default True.
///     merge_overflow: If True, merges extra tokens into the last column. Default True.
///     expected_columns: Optional explicit column count. If None, inferred automatically.
///     repair_quotes: If True, disambiguates and repairs stray internal quotes. Default True.
#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(signature = (
    input_path,
    output_path,
    quarantine_path=None,
    delimiter=None,
    quote_char="\"",
    fill_ragged_rows=true,
    merge_overflow=true,
    expected_columns=None,
    repair_quotes=true
))]
pub fn salvage_file(
    input_path: String,
    output_path: String,
    quarantine_path: Option<String>,
    delimiter: Option<String>,
    quote_char: &str,
    fill_ragged_rows: bool,
    merge_overflow: bool,
    expected_columns: Option<usize>,
    repair_quotes: bool,
) -> PyResult<PySalvageSummary> {
    let delim_byte = delimiter.and_then(|d| d.as_bytes().first().copied());
    let quote_byte = quote_char.as_bytes().first().copied().unwrap_or(b'"');

    let options = SalvageOptions {
        delimiter: delim_byte,
        quote_char: quote_byte,
        repair_quotes,
        fill_ragged_rows,
        merge_overflow,
        expected_columns,
    };

    let summary = rust_salvage_file(
        &input_path,
        &output_path,
        quarantine_path.as_deref(),
        &options,
    )?;

    Ok(summary.into())
}

/// Detects the most likely delimiter from a CSV string sample.
#[pyfunction]
pub fn sniff(sample: &str) -> String {
    let delim = sniff_delimiter(sample.as_bytes());
    (delim as char).to_string()
}

/// In-memory streaming reader iterating over salvaged rows.
#[pyclass(name = "SalvageReader")]
pub struct PySalvageReader {
    rows: Vec<Vec<String>>,
    index: usize,
    #[pyo3(get)]
    pub summary: PySalvageSummary,
}

#[pymethods]
impl PySalvageReader {
    #[allow(clippy::too_many_arguments)]
    #[new]
    #[pyo3(signature = (
        file_path,
        delimiter=None,
        quote_char="\"",
        fill_ragged_rows=true,
        merge_overflow=true,
        expected_columns=None,
        repair_quotes=true
    ))]
    fn new(
        file_path: String,
        delimiter: Option<String>,
        quote_char: &str,
        fill_ragged_rows: bool,
        merge_overflow: bool,
        expected_columns: Option<usize>,
        repair_quotes: bool,
    ) -> PyResult<Self> {
        let mut file = File::open(&file_path)?;
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)?;

        let delim_byte = delimiter.and_then(|d| d.as_bytes().first().copied());
        let quote_byte = quote_char.as_bytes().first().copied().unwrap_or(b'"');

        let options = SalvageOptions {
            delimiter: delim_byte,
            quote_char: quote_byte,
            repair_quotes,
            fill_ragged_rows,
            merge_overflow,
            expected_columns,
        };

        let (salvaged, _quarantine, summary) = salvage_slice(&buffer, &options);

        Ok(Self {
            rows: salvaged,
            index: 0,
            summary: summary.into(),
        })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>) -> Option<Vec<String>> {
        if slf.index < slf.rows.len() {
            let row = slf.rows[slf.index].clone();
            slf.index += 1;
            Some(row)
        } else {
            None
        }
    }

    fn __len__(&self) -> usize {
        self.rows.len()
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    #[pyo3(signature = (_exc_type=None, _exc_val=None, _exc_tb=None))]
    fn __exit__(
        &self,
        _exc_type: Option<&Bound<'_, PyAny>>,
        _exc_val: Option<&Bound<'_, PyAny>>,
        _exc_tb: Option<&Bound<'_, PyAny>>,
    ) -> bool {
        false
    }
}

/// Convenience function to open and stream a salvaged CSV file.
#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(name = "open", signature = (
    file_path,
    delimiter=None,
    quote_char="\"",
    fill_ragged_rows=true,
    merge_overflow=true,
    expected_columns=None,
    repair_quotes=true
))]
pub fn py_open(
    file_path: String,
    delimiter: Option<String>,
    quote_char: &str,
    fill_ragged_rows: bool,
    merge_overflow: bool,
    expected_columns: Option<usize>,
    repair_quotes: bool,
) -> PyResult<PySalvageReader> {
    PySalvageReader::new(
        file_path,
        delimiter,
        quote_char,
        fill_ragged_rows,
        merge_overflow,
        expected_columns,
        repair_quotes,
    )
}

/// The native _csv_salvage_backend Python module.
#[pymodule]
fn _csv_salvage_backend(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add(
        "__doc__",
        "High-performance, fault-tolerant CSV salvage and reconstruction engine.\n\n\
         Rescues corrupted, broken, and malformed CSV files where strict parsers\n\
         (Polars, DuckDB, Pandas) abort with ParserError.",
    )?;
    m.add(
        "__all__",
        vec![
            "salvage_file",
            "sniff",
            "open",
            "SalvageSummary",
            "SalvageReader",
        ],
    )?;

    m.add_function(wrap_pyfunction!(salvage_file, m)?)?;
    m.add_function(wrap_pyfunction!(sniff, m)?)?;
    m.add_function(wrap_pyfunction!(py_open, m)?)?;
    m.add_class::<PySalvageSummary>()?;
    m.add_class::<PySalvageReader>()?;
    Ok(())
}
