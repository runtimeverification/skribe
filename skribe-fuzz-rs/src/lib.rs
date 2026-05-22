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
    let exit_code =
        get_cell(pattern, "Lbl'-LT-'exit-code'-GT-'").expect("Cell <exit-code> not found");
    let exit_code_str = match_int(exit_code).unwrap();
    exit_code_str.parse().unwrap()
}

pub fn write_coverage_data(pattern: &kore::Pattern, coverage: &mut [u8]) {
    // Update coverage
    // This should come in as a zeroed byte array every time, as it gets reset
    // by the observer at the beginning of each execution
    let cov = extract_coverage(pattern).unwrap();
    coverage[..cov.len()].copy_from_slice(&cov);
}

pub fn get_coverage_size(pattern: &kore::Pattern) -> usize {
    let cov = extract_coverage(pattern).unwrap();
    cov.len()
}

fn extract_coverage(pattern: &kore::Pattern) -> Result<Vec<u8>, String> {
    let cov = get_cell(pattern, "Lbl'-LT-'coverage'-GT-'").ok_or("Cell <coverage> not found")?;
    let mut entries = match_map(cov)?
        .iter()
        .map(|(k, v)| Ok((extract_int_key(k)?, extract_bytes_value(v)?)))
        .collect::<Result<Vec<(String, Vec<u8>)>, String>>()?;
    entries.sort_by(|(k1, _), (k2, _)| k1.cmp(k2));
    Ok(entries.into_iter().flat_map(|(_, v)| v).collect())
}

fn extract_int_key(pattern: &kore::Pattern) -> Result<String, String> {
    Ok(match_int(match_inj(pattern)?)?.to_owned())
}

fn extract_bytes_value(pattern: &kore::Pattern) -> Result<Vec<u8>, String> {
    match_bytes(match_inj(pattern)?)
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
        kore::Pattern::App(kore::App {
            symbol: s, args, ..
        }) if s.as_str() == symbol => args.first(),
        kore::Pattern::App(kore::App { args, .. }) => {
            args.iter().find_map(|arg| get_cell(arg, symbol))
        }
        _ => None,
    }
}

fn match_inj(pattern: &kore::Pattern) -> Result<&kore::Pattern, String> {
    match pattern {
        kore::Pattern::App(kore::App { symbol, args, .. }) if symbol.as_str() == "inj" => {
            match args.as_slice() {
                [inner] => Ok(inner),
                _ => Err(format!("Expected 1 arg in inj, got {}", args.len())),
            }
        }
        _ => Err(format!("Expected inj, got {:?}", pattern)),
    }
}

fn match_int(pattern: &kore::Pattern) -> Result<&str, String> {
    match pattern {
        kore::Pattern::Dv {
            sort: kore::Sort::App { id, .. },
            value,
        } if id.as_str() == "SortInt" => Ok(&value.0),
        p => Err(format!("Expected SortInt Dv, got {:?}", p)),
    }
}

fn match_bytes(pattern: &kore::Pattern) -> Result<Vec<u8>, String> {
    match pattern {
        kore::Pattern::Dv {
            sort: kore::Sort::App { id, .. },
            value,
        } if id.as_str() == "SortBytes" => Ok(value.0.chars().map(|c| c as u32 as u8).collect()),
        p => Err(format!("Expected SortBytes Dv, got {:?}", p)),
    }
}

pub fn kllvm_kore_block_dump_hotfix(s: &str) -> &str {
    // TODO This is a hotfix for a bug in kore_block_dump
    let terminator = r#"Lbl'-LT-'generatedCounter'-GT-'{}(\dv{SortInt{}}("0")))"#;
    let pos = s.find(terminator).expect("terminator not found");
    &s[..pos + terminator.len()]
}
