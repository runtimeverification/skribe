use crate::Signature;
use alloy_dyn_abi::{DynSolType, DynSolValue, JsonAbiExt};
use alloy_json_abi::Function;
use arbitrary::Unstructured;
use std::fmt::Debug;

#[derive(Debug)]
pub struct SignatureAbi {
    types: Vec<DynSolType>,
    function: Function,
}

impl std::fmt::Display for SignatureAbi {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> Result<(), std::fmt::Error> {
        write!(f, "SignatureAbi({})", self.function.signature())
    }
}

impl SignatureAbi {
    pub fn from_signature(sig: Signature) -> Result<SignatureAbi, String> {
        let types: Vec<DynSolType> = sig
            .arg_types
            .iter()
            .map(|s| s.parse::<DynSolType>().map_err(|e| e.to_string()))
            .collect::<Result<Vec<_>, _>>()?;

        let arg_types = sig.arg_types.join(",");
        let sig = format!("{}({})", sig.name, arg_types);
        let function = Function::parse(&sig).map_err(|e| e.to_string())?;

        Ok(SignatureAbi { types, function })
    }

    pub fn arbitrary_input(&self, u: &mut Unstructured<'_>) -> arbitrary::Result<Vec<u8>> {
        let values = self
            .types
            .iter()
            .map(|ty| DynSolValue::arbitrary_from_type(ty, u))
            .collect::<arbitrary::Result<Vec<_>>>()?;

        self.encode_input(&values)
            .map_err(|_| arbitrary::Error::IncorrectFormat)
    }

    fn encode_input(&self, values: &[DynSolValue]) -> Result<Vec<u8>, String> {
        self.function
            .abi_encode_input(values)
            .map_err(|e| e.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use alloy_primitives::{B256, U256};
    use hex_literal::hex;

    #[test]
    fn test_to_string() {
        assert_eq!(
            signature_abi().to_string(),
            "SignatureAbi(test_end_to_end_intense(bytes8,bytes8,bool,(uint256,bool)[]))"
        );
    }

    #[test]
    fn test_types() {
        // Given
        let abi = signature_abi();
        let expected = vec![
            DynSolType::FixedBytes(8),
            DynSolType::FixedBytes(8),
            DynSolType::Bool,
            DynSolType::Array(Box::new(DynSolType::Tuple(vec![
                DynSolType::Uint(256),
                DynSolType::Bool,
            ]))),
        ];

        // When
        let actual = abi.types;

        // Then
        assert_eq!(actual, expected);
    }

    #[test]
    fn test_encode_input() {
        // Given
        let abi = signature_abi();

        let expected = hex!(
            "dc8e3faa"                                                         // selector
            "0102030405060708000000000000000000000000000000000000000000000000" // bytes8 arg1
            "deadbeef00000000000000000000000000000000000000000000000000000000" // bytes8 arg2
            "0000000000000000000000000000000000000000000000000000000000000001" // bool true
            "0000000000000000000000000000000000000000000000000000000000000080" // offset to array
            "0000000000000000000000000000000000000000000000000000000000000001" // array length
            "000000000000000000000000000000000000000000000000000000000000002a" // uint256 42
            "0000000000000000000000000000000000000000000000000000000000000000" // bool false
        );

        let values = vec![
            DynSolValue::FixedBytes(
                B256::from(hex!(
                    "0102030405060708000000000000000000000000000000000000000000000000"
                )),
                8,
            ),
            DynSolValue::FixedBytes(
                B256::from(hex!(
                    "deadbeef00000000000000000000000000000000000000000000000000000000"
                )),
                8,
            ),
            DynSolValue::Bool(true),
            DynSolValue::Array(vec![DynSolValue::Tuple(vec![
                DynSolValue::Uint(U256::from(42u64), 256),
                DynSolValue::Bool(false),
            ])]),
        ];

        // When
        let actual = abi.encode_input(&values).unwrap();

        // Then
        assert_eq!(actual, expected);
    }

    #[test]
    fn test_arbitrary_input() {
        // Given
        let abi = signature_abi();
        let raw = vec![0u8; 256];
        let mut u = Unstructured::new(&raw);

        // When
        let result = abi.arbitrary_input(&mut u);

        // Then
        assert!(result.is_ok());
    }

    fn signature_abi() -> SignatureAbi {
        SignatureAbi::from_signature(signature()).unwrap()
    }

    fn signature() -> Signature {
        Signature {
            contract_name: "TestSkribeEndToEnd".to_string(),
            name: "test_end_to_end_intense".to_string(),
            arg_types: vec![
                "bytes8".to_string(),
                "bytes8".to_string(),
                "bool".to_string(),
                "(uint256,bool)[]".to_string(),
            ],
        }
    }
}
