# NC Bill Patterns

## Sync API Processor Pattern

Seen in `mitejia` and `qicheng/sync`.

Typical flow in subclasses of `AbstractApiProcessor`:

1. `convertRequestData(String requestBody)` parses JSON into a param class.
2. `validateBusinessParams(Object requestData)` validates required fields and bill state.
3. `executeBusinessLogic(Object requestData)` builds or converts an NC aggregate VO.
4. Save with local helper, such as `saveAggregatedVO(vo, "WRITE", billType)`.
5. `buildSuccessResult(Object businessResult)` returns bill id, bill no, third no, and body row ids.

The base class may own request logging, trace id, empty body checks, and success wrapping. Keep processor changes inside conversion/validation/business/result methods.

## OpenAPI Rule Pattern

Seen in `yingke-old`, `yingke-zs`, and `qicheng/qicheng`.

Common classes:

- `OpenApiDataBussProcess`: `conversion -> beforeProcess -> execute -> afterProcess`
- `BillBussProcess<E>`: JSON conversion using `getClazz()`, `actionScript`, and `documentConversion`
- Rule processors: usually under `rule/actuator`, returned by `executeRule()`

Typical subclass responsibilities:

1. Implement `conversion` or inherit `BillBussProcess.conversion`.
2. Implement `execute(Object data)` with VO build/conversion/save logic.
3. Implement `executeRule()` with the matching rule processor.
4. Implement `apiCode()`.
5. If extending `BillBussProcess<E>`, implement `getClazz()`.

Save/push operations often call `IPFBusiAction.processBatch(action, billTypeCode, vos, ...)` through `actionScript` or `pushOrderAction`.

## Source Bill Conversion

- Purchase arrival to purchase-in: `PfServiceScmUtil.executeVOChange("23", "45", arriveVOs)`
- Delivery to sale-out: `PfServiceScmUtil.executeVOChange("4331", "4C", deliveryVOs)`
- Purchase-in to purchase invoice: `documentConversion("45", "25", purchaseInVOs)` in older OpenAPI code

When a source bill row can split into multiple target rows:

- Use the converted row as a template.
- Copy it before applying row-specific data for the second and later target rows.
- Clear the target row primary key and set `VOStatus.NEW`.
- Reassign `crowno` after final body list assembly.

When merging multiple source bills into one target bill:

- Pick one parent/header as the target aggregate parent.
- Collect child rows into a new list.
- Reassign row numbers (`10,20,30...`) after merging.
- Recalculate totals or relation amounts when the local module has a calculator class.

## Batch And Free Fields

- `vfree2`: 彩涂颜色, body free attribute.
- `vbcdef8`: 供应商, batch custom field, usually maps to `scm_batchcode.vdef8`.
- `vbcdef9`: 油漆型号, batch custom field, usually maps to `scm_batchcode.vdef9`.

Prefer `BatchCodeUpdateUtil.updateBatchCustomFields(pkBatchcode, map)` when updating a subset of batch fields. Avoid `updateBatchCustomFieldsAll` unless every field should be overwritten.

## Row Matching

- Prefer stable business keys: source body pk, source row no, material pk, batch code.
- Be careful matching only by batch code if the same batch can appear on multiple material rows.
- If request order matters after grouping, use `LinkedHashMap`.
