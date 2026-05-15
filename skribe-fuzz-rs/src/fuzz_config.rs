use kframework::kore;
use kframework_ffi::kllvm::{MarshalError, VarHandler};

use crate::SignatureAbi;

pub struct FuzzConfig {
    pub template: kore::Pattern,
    pub abi: SignatureAbi,
}

pub struct SignatureFuzzer(pub Vec<u8>);

impl VarHandler for SignatureFuzzer {
    fn substitute(
        &mut self,
        name: &str,
        _sort: &kore::Sort,
    ) -> Result<kore::Pattern, MarshalError> {
        let sort = kore::Sort::App {
            id: kore::Id::new("SortBytes".to_string()).unwrap(),
            args: vec![],
        };
        let value = kore::Str(self.0.iter().map(|&b| b as char).collect());
        match name {
            "VarCALLDATA" => Ok(kore::Pattern::Dv { sort, value }),
            _ => Err(MarshalError::Unsupported(
                "Encountered a variable that isn't CALLDATA",
            )),
        }
    }
}
