//! Resilient CSV Tokenizer & DFA Parser.
//!
//! Designed to recover from unescaped quotes, trailing characters,
//! and ragged rows where standard parsers fail.

#[derive(Debug, Clone)]
pub struct Dialect {
    pub delimiter: u8,
    pub quote_char: u8,
    pub escape_char: Option<u8>,
    pub repair_quotes: bool,
    pub trim_whitespace: bool,
}

impl Default for Dialect {
    fn default() -> Self {
        Self {
            delimiter: b',',
            quote_char: b'"',
            escape_char: None,
            repair_quotes: true,
            trim_whitespace: false,
        }
    }
}

impl Dialect {
    pub fn new(delimiter: u8) -> Self {
        Self {
            delimiter,
            ..Default::default()
        }
    }
}

/// Token emitted during row parsing.
#[derive(Debug, PartialEq, Eq)]
pub enum Token {
    Field(String),
    RowEnd,
    Eof,
}

/// State of the tokenizer FSM.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum State {
    StartOfField,
    InUnquotedField,
    InQuotedField,
    AfterClosingQuote,
}

/// Resilient CSV parser operating on a byte slice.
pub struct ResilientParser<'a> {
    input: &'a [u8],
    pos: usize,
    dialect: Dialect,
    current_line: usize,
}

impl<'a> ResilientParser<'a> {
    pub fn new(input: &'a [u8], dialect: Dialect) -> Self {
        // Automatically skip UTF-8 BOM if present
        let start = if input.starts_with(b"\xEF\xBB\xBF") {
            3
        } else {
            0
        };

        Self {
            input,
            pos: start,
            dialect,
            current_line: 1,
        }
    }

    pub fn current_line(&self) -> usize {
        self.current_line
    }

    /// Parses the next complete row. Returns None when EOF is reached.
    pub fn next_row(&mut self) -> Option<Vec<String>> {
        if self.pos >= self.input.len() {
            return None;
        }

        let mut row = Vec::new();
        let mut current_field = Vec::new();
        let mut state = State::StartOfField;

        while self.pos < self.input.len() {
            let b = self.input[self.pos];

            match state {
                State::StartOfField => {
                    if self.dialect.trim_whitespace && (b == b' ' || b == b'\t') {
                        // Skip leading whitespace before field
                        self.pos += 1;
                        continue;
                    }

                    if b == self.dialect.quote_char {
                        state = State::InQuotedField;
                        self.pos += 1;
                    } else if b == self.dialect.delimiter {
                        // Empty field
                        row.push(String::new());
                        self.pos += 1;
                        state = State::StartOfField;
                    } else if b == b'\r' || b == b'\n' {
                        // End of line
                        self.consume_newline();
                        row.push(String::new());
                        return Some(row);
                    } else {
                        current_field.push(b);
                        state = State::InUnquotedField;
                        self.pos += 1;
                    }
                }

                State::InUnquotedField => {
                    if b == self.dialect.delimiter {
                        row.push(String::from_utf8_lossy(&current_field).into_owned());
                        current_field.clear();
                        state = State::StartOfField;
                        self.pos += 1;
                    } else if b == b'\r' || b == b'\n' {
                        self.consume_newline();
                        row.push(String::from_utf8_lossy(&current_field).into_owned());
                        return Some(row);
                    } else {
                        current_field.push(b);
                        self.pos += 1;
                    }
                }

                State::InQuotedField => {
                    // Check for escape char if configured (e.g. \")
                    if self.dialect.escape_char == Some(b) && self.pos + 1 < self.input.len() {
                        current_field.push(self.input[self.pos + 1]);
                        self.pos += 2;
                        continue;
                    }

                    if b == self.dialect.quote_char {
                        // Check for standard escaped quote: ""
                        if self.pos + 1 < self.input.len()
                            && self.input[self.pos + 1] == self.dialect.quote_char
                        {
                            current_field.push(self.dialect.quote_char);
                            self.pos += 2;
                            continue;
                        }

                        // Quote repair heuristic: Is this really the closing quote?
                        if self.dialect.repair_quotes {
                            if self.is_closing_quote(self.pos + 1) {
                                state = State::AfterClosingQuote;
                                self.pos += 1;
                            } else {
                                // Orphan/stray quote inside field (e.g. "15" Monitor")
                                // Treat it as a literal quote character inside the field!
                                current_field.push(self.dialect.quote_char);
                                self.pos += 1;
                            }
                        } else {
                            state = State::AfterClosingQuote;
                            self.pos += 1;
                        }
                    } else {
                        if b == b'\n' {
                            self.current_line += 1;
                        }
                        current_field.push(b);
                        self.pos += 1;
                    }
                }

                State::AfterClosingQuote => {
                    if b == self.dialect.delimiter {
                        row.push(String::from_utf8_lossy(&current_field).into_owned());
                        current_field.clear();
                        state = State::StartOfField;
                        self.pos += 1;
                    } else if b == b'\r' || b == b'\n' {
                        self.consume_newline();
                        row.push(String::from_utf8_lossy(&current_field).into_owned());
                        return Some(row);
                    } else if b == b' ' || b == b'\t' {
                        // Tolerate trailing whitespace after quote before delimiter
                        self.pos += 1;
                    } else {
                        // Extra garbage after closing quote (e.g. "foo"bar)
                        // Salvage: append to field and treat as unquoted continuation
                        current_field.push(b);
                        state = State::InUnquotedField;
                        self.pos += 1;
                    }
                }
            }
        }

        // EOF reached while parsing
        if !current_field.is_empty() || state != State::StartOfField || !row.is_empty() {
            row.push(String::from_utf8_lossy(&current_field).into_owned());
            Some(row)
        } else {
            None
        }
    }

    /// Looks ahead from `next_pos` to determine if a quote acts as a closing quote.
    fn is_closing_quote(&self, mut next_pos: usize) -> bool {
        // Skip optional trailing spaces/tabs
        while next_pos < self.input.len()
            && (self.input[next_pos] == b' ' || self.input[next_pos] == b'\t')
        {
            next_pos += 1;
        }

        if next_pos >= self.input.len() {
            // Quote right at EOF is a closing quote
            return true;
        }

        let next_b = self.input[next_pos];
        if next_b == self.dialect.delimiter || next_b == b'\r' || next_b == b'\n' {
            return true;
        }

        // If next_b is not delimiter or newline, check if there is another closing quote
        // candidate later on the same line.
        // If there IS a later quote followed by delimiter/newline, this quote is an internal stray quote!
        // If there is NO other quote on this line, this quote must be the closing quote.
        let has_later = self.has_later_closing_quote_on_line(next_pos);
        !has_later
    }

    fn has_later_closing_quote_on_line(&self, start: usize) -> bool {
        let mut i = start;
        while i < self.input.len() && self.input[i] != b'\n' && self.input[i] != b'\r' {
            if self.input[i] == self.dialect.quote_char {
                let mut after = i + 1;
                while after < self.input.len()
                    && (self.input[after] == b' ' || self.input[after] == b'\t')
                {
                    after += 1;
                }
                if after >= self.input.len()
                    || self.input[after] == self.dialect.delimiter
                    || self.input[after] == b'\r'
                    || self.input[after] == b'\n'
                {
                    return true;
                }
            }
            i += 1;
        }
        false
    }

    fn consume_newline(&mut self) {
        if self.pos < self.input.len() && self.input[self.pos] == b'\r' {
            self.pos += 1;
        }
        if self.pos < self.input.len() && self.input[self.pos] == b'\n' {
            self.pos += 1;
        }
        self.current_line += 1;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_standard_csv() {
        let data = b"id,name,age\n1,Alice,30\n2,Bob,25";
        let mut parser = ResilientParser::new(data, Dialect::default());

        assert_eq!(
            parser.next_row(),
            Some(vec!["id".into(), "name".into(), "age".into()])
        );
        assert_eq!(
            parser.next_row(),
            Some(vec!["1".into(), "Alice".into(), "30".into()])
        );
        assert_eq!(
            parser.next_row(),
            Some(vec!["2".into(), "Bob".into(), "25".into()])
        );
        assert_eq!(parser.next_row(), None);
    }

    #[test]
    fn test_stray_orphan_quotes() {
        // Here 15" is inside a quoted cell: "15" Monitor"
        let data = b"id,product,price\n101,\"15\" Monitor\",49.99\n102,\"Standard Widget\",10.00";
        let mut parser = ResilientParser::new(data, Dialect::default());

        assert_eq!(
            parser.next_row(),
            Some(vec!["id".into(), "product".into(), "price".into()])
        );
        assert_eq!(
            parser.next_row(),
            Some(vec!["101".into(), "15\" Monitor".into(), "49.99".into()])
        );
        assert_eq!(
            parser.next_row(),
            Some(vec!["102".into(), "Standard Widget".into(), "10.00".into()])
        );
    }

    #[test]
    fn test_standard_escaped_quotes() {
        let data = b"1,\"He said \"\"Hello\"\"\",9.99";
        let mut parser = ResilientParser::new(data, Dialect::default());
        assert_eq!(
            parser.next_row(),
            Some(vec!["1".into(), "He said \"Hello\"".into(), "9.99".into()])
        );
    }

    #[test]
    fn test_embedded_newline_in_quotes() {
        let data = b"1,\"Line 1\nLine 2\",100\n2,Normal,200";
        let mut parser = ResilientParser::new(data, Dialect::default());

        assert_eq!(
            parser.next_row(),
            Some(vec!["1".into(), "Line 1\nLine 2".into(), "100".into()])
        );
        assert_eq!(
            parser.next_row(),
            Some(vec!["2".into(), "Normal".into(), "200".into()])
        );
    }

    #[test]
    fn test_trailing_garbage_after_quote() {
        let data = b"1,\"Foo\"Bar,3";
        let mut parser = ResilientParser::new(data, Dialect::default());
        assert_eq!(
            parser.next_row(),
            Some(vec!["1".into(), "FooBar".into(), "3".into()])
        );
    }

    #[test]
    fn test_crlf_and_missing_trailing_newline() {
        let data = b"a,b,c\r\n1,2,3";
        let mut parser = ResilientParser::new(data, Dialect::default());
        assert_eq!(
            parser.next_row(),
            Some(vec!["a".into(), "b".into(), "c".into()])
        );
        assert_eq!(
            parser.next_row(),
            Some(vec!["1".into(), "2".into(), "3".into()])
        );
        assert_eq!(parser.next_row(), None);
    }
}
