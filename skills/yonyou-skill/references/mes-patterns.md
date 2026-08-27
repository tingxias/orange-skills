# MES Integration Patterns

## Service Layer

Keep MES transport details inside shared service classes under:

`uapbd/src/public/nc/buss/mes/push`

Processors/actions should build business request objects and call the service. They should not duplicate HTTP details.

## BeforeDataSyncCheck

Current request shape:

```json
{
  "PostParams": {
    "pk_cgeneralhid": "",
    "ccode": "",
    "pk_rdtypeid": "",
    "businessType": "",
    "actionType": "",
    "bodyList": []
  }
}
```

Response success rule:

- `code == 200`
- `success == true`

Anything else should be treated as failure.

## Business Types

- `PurchaseReturn`: 采购退货
- `SaleReturn`: 销售退货
- `ModalShift`: 形态转换
- `OtherInBill`: 其他入库单（形态转换单）

## Material Push Rule

For DEF0003 material-class filtering:

- Caller extracts material pk from each body row.
- Caller loops rows and calls shared rule utility with only material pk.
- Add only matched rows into MES request body.
- If all rows are filtered out, skip MES call.

This keeps row extraction local and avoids making the shared utility depend on many bill VO types.
