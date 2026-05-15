use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Signature {
    pub contract_name: String,
    pub name: String,
    pub arg_types: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct FuzzSpec {
    pub template: String,
    pub signatures: Vec<Signature>,
}

pub fn fuzz_specs_from_json(json: &str) -> Result<Vec<FuzzSpec>, serde_json::Error> {
    serde_json::from_str(json)
}

pub fn extract_template_and_signature(
    specs: Vec<FuzzSpec>,
    contract_name: &str,
    function_name: &str,
) -> Option<(String, Signature)> {
    specs.into_iter().find_map(|spec| {
        let template = spec.template;
        spec.signatures
            .into_iter()
            .find(|sig| sig.contract_name == contract_name && sig.name == function_name)
            .map(|sig| (template.clone(), sig))
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fuzz_specs_from_json() {
        let json = r#"[
            {
                "template": "X:SortGeneratedTopCell{}",
                "signatures": [
                    {
                        "contract_name": "TestSkribeEndToEnd",
                        "name": "test_end_to_end_intense",
                        "arg_types": ["bytes8", "bytes8", "bool", "(uint256,bool)[]"]
                    }
                ]
            }
        ]"#;

        let specs = fuzz_specs_from_json(json).unwrap();
        assert_eq!(specs.len(), 1);
        assert_eq!(specs[0].template, "X:SortGeneratedTopCell{}");
        assert_eq!(specs[0].signatures.len(), 1);

        let sig = &specs[0].signatures[0];
        assert_eq!(sig.contract_name, "TestSkribeEndToEnd");
        assert_eq!(sig.name, "test_end_to_end_intense");
        assert_eq!(
            sig.arg_types,
            ["bytes8", "bytes8", "bool", "(uint256,bool)[]"]
        );
    }
}
