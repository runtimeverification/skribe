use kframework::kore;
use kframework_ffi::kllvm::{MarshalError, VarHandler};

use crate::SignatureAbi;

pub struct FuzzConfig {
    pub template: kore::Pattern,
    pub abi: SignatureAbi,
    pub coverage: bool,
}

pub struct SignatureFuzzer {
    pub input: Vec<u8>,
    pub coverage: bool,
}

impl VarHandler for SignatureFuzzer {
    fn substitute(
        &mut self,
        name: &str,
        _sort: &kore::Sort,
    ) -> Result<kore::Pattern, MarshalError> {
        match name {
            "VarCALLDATA" => Ok(kore::Pattern::Dv {
                sort: kore::Sort::App {
                    id: kore::Id::new("SortBytes".to_owned()).unwrap(),
                    args: vec![],
                },
                value: kore::Str(self.input.iter().map(|&b| b as char).collect()),
            }),
            "VarCOVERAGE'Unds'ENABLED" => Ok(kore::Pattern::Dv {
                sort: kore::Sort::App {
                    id: kore::Id::new("SortBool".to_owned()).unwrap(),
                    args: vec![],
                },
                value: kore::Str(self.coverage.to_string()),
            }),
            _ => Err(MarshalError::UnknownVar(format!(
                "Encountered unsupported variable: {name}"
            ))),
        }
    }
}
