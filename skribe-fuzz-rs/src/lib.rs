mod abi;
mod fuzz_config;
mod fuzz_spec;

pub use abi::SignatureAbi;
pub use fuzz_config::{FuzzConfig, SignatureFuzzer};
pub use fuzz_spec::{FuzzSpec, Signature, extract_template_and_signature, fuzz_specs_from_json};

pub use kframework::kore;
pub use kframework_ffi::kllvm;

/// Get the <exit-code> cell value from a configuration
pub fn get_exit_code(pattern: &kore::Pattern) -> u32 {
    let exit_code_cell =
        get_cell(pattern, "Lbl'-LT-'exit-code'-GT-'").expect("Cell <exit-code> not found");
    let args = match_app(exit_code_cell).unwrap();
    let exit_code_str = match_int(&args[0]).unwrap();
    exit_code_str.parse().unwrap()
}

pub fn write_coverage_data(pattern: &kore::Pattern, coverage: &mut [u8]) {
    // Update coverage
    // This should come in as a zeroed byte array every time, as it gets reset
    // by the observer at the beginning of each execution
    let coverages = extract_coverages(pattern).unwrap();
    let mut base = 0;
    for cov in &coverages {
        for entry in &cov.entries {
            for i in entry.offset..entry.offset + entry.length {
                coverage[base + i] = 0xff;
            }
        }
        base += cov.size;
    }
}

pub fn get_coverage_size(pattern: &kore::Pattern) -> usize {
    let coverages = extract_coverages(pattern).unwrap();
    coverages.iter().map(|c| c.size).sum()
}

fn extract_coverages(pattern: &kore::Pattern) -> Result<Vec<Coverage>, String> {
    let coverage_cell =
        get_cell(pattern, "Lbl'-LT-'coverage'-GT-'").ok_or("Cell <coverage> not found")?;
    let coverage_cell_args = match_app(coverage_cell)?;
    let mut entries = match_map(&coverage_cell_args[0])?
        .iter()
        .map(|(k, v)| Ok((match_coverage_map_key(k)?, match_coverage_map_value(v)?)))
        .collect::<Result<Vec<_>, String>>()?;
    entries.sort_by(|(a, _), (b, _)| a.cmp(b));
    Ok(entries
        .into_iter()
        .map(|(_key, coverage)| coverage)
        .collect())
}

fn match_coverage_map_key(pattern: &kore::Pattern) -> Result<String, String> {
    Ok(match_int(match_inj(pattern)?)?.to_owned())
}

fn match_coverage_map_value(pattern: &kore::Pattern) -> Result<Coverage, String> {
    Ok(match_coverage(match_inj(pattern)?)?)
}

struct Coverage {
    pub size: usize,
    pub entries: Vec<CovEntry>,
}

struct CovEntry {
    pub offset: usize,
    pub length: usize,
}

fn match_coverage(pattern: &kore::Pattern) -> Result<Coverage, String> {
    let args = match_symbol(pattern, "Lbl'Hash'coverage")?;
    match args {
        [size, entries] => {
            let size = match_int(size)?
                .parse::<usize>()
                .map_err(|e| format!("Invalid size: {e}"))?;
            let entries = match_set(entries)?
                .iter()
                .map(|p| match_cov_entry(match_inj(p)?))
                .collect::<Result<Vec<_>, _>>()?;
            Ok(Coverage { size, entries })
        }
        _ => Err(format!("Expected 2 args for #coverage, got {}", args.len())),
    }
}

fn match_cov_entry(pattern: &kore::Pattern) -> Result<CovEntry, String> {
    let args = match_symbol(pattern, "Lbl'Hash'covEntry")?;
    match args {
        [offset, length] => Ok(CovEntry {
            offset: match_int(offset)?
                .parse::<usize>()
                .map_err(|e| format!("Invalid offset: {e}"))?,
            length: match_int(length)?
                .parse::<usize>()
                .map_err(|e| format!("Invalid length: {e}"))?,
        }),
        _ => Err(format!("Expected 2 args for #covEntry, got {}", args.len())),
    }
}

fn match_set(pattern: &kore::Pattern) -> Result<Vec<&kore::Pattern>, String> {
    let mut entries = Vec::new();
    collect_set_entries(pattern, &mut entries)?;
    Ok(entries)
}

fn collect_set_entries<'a>(
    pattern: &'a kore::Pattern,
    entries: &mut Vec<&'a kore::Pattern>,
) -> Result<(), String> {
    match pattern {
        kore::Pattern::LeftAssoc(kore::App { symbol, args, .. })
            if symbol.as_str() == "Lbl'Unds'Set'Unds'" =>
        {
            for arg in args {
                collect_set_entries(arg, entries)?;
            }
            Ok(())
        }
        kore::Pattern::App(kore::App { symbol, args, .. })
            if symbol.as_str() == "Lbl'Unds'Set'Unds'" =>
        {
            for arg in args {
                collect_set_entries(arg, entries)?;
            }
            Ok(())
        }
        kore::Pattern::App(kore::App { symbol, .. }) if symbol.as_str() == "Lbl'Stop'Set" => Ok(()),
        kore::Pattern::App(kore::App { symbol, args, .. }) if symbol.as_str() == "LblSetItem" => {
            match args.as_slice() {
                [elem] => {
                    entries.push(elem);
                    Ok(())
                }
                _ => Err(format!("Expected 1 arg in SetItem, got {}", args.len())),
            }
        }
        _ => Err(format!("Expected set pattern, got {:?}", pattern)),
    }
}

fn match_map(pattern: &kore::Pattern) -> Result<Vec<(&kore::Pattern, &kore::Pattern)>, String> {
    let mut entries = Vec::new();
    collect_map_entries(pattern, &mut entries)?;
    Ok(entries)
}

fn collect_map_entries<'a>(
    pattern: &'a kore::Pattern,
    entries: &mut Vec<(&'a kore::Pattern, &'a kore::Pattern)>,
) -> Result<(), String> {
    match pattern {
        kore::Pattern::LeftAssoc(kore::App { symbol, args, .. })
            if symbol.as_str() == "Lbl'Unds'Map'Unds'" =>
        {
            for arg in args {
                collect_map_entries(arg, entries)?;
            }
            Ok(())
        }
        kore::Pattern::App(kore::App { symbol, args, .. })
            if symbol.as_str() == "Lbl'Unds'Map'Unds'" =>
        {
            for arg in args {
                collect_map_entries(arg, entries)?;
            }
            Ok(())
        }
        kore::Pattern::App(kore::App { symbol, .. }) if symbol.as_str() == "Lbl'Stop'Map" => Ok(()),
        kore::Pattern::App(kore::App { symbol, args, .. })
            if symbol.as_str() == "Lbl'UndsPipe'-'-GT-Unds'" =>
        {
            match args.as_slice() {
                [k, v] => {
                    entries.push((k, v));
                    Ok(())
                }
                _ => Err(format!("Expected 2 args in map item, got {}", args.len())),
            }
        }
        _ => Err(format!("Expected map pattern, got {:?}", pattern)),
    }
}

fn get_cell<'a>(pattern: &'a kore::Pattern, symbol: &str) -> Option<&'a kore::Pattern> {
    match pattern {
        kore::Pattern::App(kore::App { symbol: s, .. }) if s.as_str() == symbol => Some(pattern),
        kore::Pattern::App(kore::App { args, .. }) => {
            args.iter().find_map(|arg| get_cell(arg, symbol))
        }
        _ => None,
    }
}

fn match_app<'a>(pattern: &'a kore::Pattern) -> Result<&'a [kore::Pattern], String> {
    match pattern {
        kore::Pattern::App(kore::App { args, .. }) => Ok(args.as_slice()),
        _ => Err(format!("Expected App, got {:?}", pattern)),
    }
}

fn match_symbol<'a>(
    pattern: &'a kore::Pattern,
    symbol: &'a str,
) -> Result<&'a [kore::Pattern], String> {
    match pattern {
        kore::Pattern::App(kore::App {
            symbol: sym, args, ..
        }) if sym.as_str() == symbol => Ok(args.as_slice()),
        _ => Err(format!("Expected App {}, got {:?}", symbol, pattern)),
    }
}

fn match_inj(pattern: &kore::Pattern) -> Result<&kore::Pattern, String> {
    let args = match_symbol(pattern, "inj")?;
    match args {
        [inner] => Ok(inner),
        _ => Err(format!("Expected 1 arg in inj, got {}", args.len())),
    }
}

fn match_dv<'a>(pattern: &'a kore::Pattern, sort: &str) -> Result<&'a str, String> {
    match pattern {
        kore::Pattern::Dv {
            sort: kore::Sort::App { id, .. },
            value,
        } if id.as_str() == sort => Ok(&value.0),
        _ => Err(format!("Expected {} Dv, got {:?}", sort, pattern)),
    }
}

fn match_int(pattern: &kore::Pattern) -> Result<&str, String> {
    match_dv(pattern, "SortInt")
}

pub fn kllvm_kore_block_dump_hotfix(s: &str) -> &str {
    // TODO This is a hotfix for a bug in kore_block_dump
    let terminator = r#"Lbl'-LT-'generatedCounter'-GT-'{}(\dv{SortInt{}}("0")))"#;
    let pos = s.find(terminator).expect("terminator not found");
    &s[..pos + terminator.len()]
}
