pub use kframework_ffi::kllvm;
pub use kframework::kore;

use kframework_ffi::kllvm::{Marshaller, VarHandler};
use kframework::kore::{Id, Pattern, Sort};

struct DummyHandler;

impl VarHandler for DummyHandler {
    fn substitute(&mut self, _name: &str, _sort: &Sort) -> Result<Pattern, kllvm::MarshalError> {
        Err(kllvm::MarshalError::Unsupported("Not handling variables"))
    }
}

pub fn make_dv() -> kllvm::Pattern {
    let dv = Pattern::Dv { sort: Sort::App { id: Id::new("SortInt".to_string()).unwrap(), args: vec![] }, value: "1".into() };

    let mut marshal: Marshaller<DummyHandler> = Marshaller::new(None);

    marshal.marshal(&dv).unwrap()
}
