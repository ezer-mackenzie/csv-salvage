use pyo3::PyErr;
use pyo3::exceptions::{PyIOError, PyValueError};
use std::fmt;
use std::io;

/// Core error type for csv-salvage operations.
#[derive(Debug)]
pub enum SalvageError {
    Io(io::Error),
    InvalidConfiguration(String),
    ParseError { line: usize, message: String },
    InferenceError(String),
}

impl fmt::Display for SalvageError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            SalvageError::Io(err) => write!(f, "I/O error: {}", err),
            SalvageError::InvalidConfiguration(msg) => write!(f, "Invalid configuration: {}", msg),
            SalvageError::ParseError { line, message } => {
                write!(f, "Parse error at line {}: {}", line, message)
            }
            SalvageError::InferenceError(msg) => write!(f, "Schema inference error: {}", msg),
        }
    }
}

impl std::error::Error for SalvageError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            SalvageError::Io(err) => Some(err),
            _ => None,
        }
    }
}

impl From<io::Error> for SalvageError {
    fn from(err: io::Error) -> Self {
        SalvageError::Io(err)
    }
}

impl From<SalvageError> for PyErr {
    fn from(err: SalvageError) -> PyErr {
        match err {
            SalvageError::Io(e) => PyIOError::new_err(e.to_string()),
            SalvageError::InvalidConfiguration(msg) => PyValueError::new_err(msg),
            SalvageError::ParseError { line, message } => {
                PyValueError::new_err(format!("Line {}: {}", line, message))
            }
            SalvageError::InferenceError(msg) => PyValueError::new_err(msg),
        }
    }
}
