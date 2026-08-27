# NC65 Data Dictionary

Use this reference when mapping interface fields to NC65 primary keys, codes, names, custom archives, and common base-data tables.

## Core Rule

Before writing mapping code, decide what the target VO setter expects:

- NC primary key: fields named like `pk_*`, `c*id`, `*_id`, `ctrantypeid`.
- Code: request-facing fields often use `code`, `vtrantypecode`, `user_code`, material code, org code.
- Name: some Excel/import/custom-archive mappings use display names.
- Custom archive value: resolve through `bd_defdoclist` + `bd_defdoc`.

Do not assume incoming codes can be assigned directly to NC VO pk fields. Most bill VO reference fields must be converted to primary keys.

## Query Utilities

Use the local project's existing utility:

- `mitejia` sync style: `com.yonyou.common.util.SyncQueryDataUtil`
- `qicheng/sync` sync style: `com.yonyou.common.util.SyncQueryDataUtil`
- `qicheng/qicheng` OpenAPI style: `nc.custom.pub.util.QueryDataUtil`
- `yingke-zs` OpenAPI style: `nc.custom.pub.util.QueryDataUtil`
- Some `qicheng/qicheng` CT code uses `nc.customer.pub.qicheng.ct.util.PubQueryService`

Common processors:

- `ColumnProcessor`: single column/single value.
- `ColumnListProcessor`: one column list.
- `MapProcessor`: one row map.
- `MapListProcessor`: multi-row map list.

When using string-built SQL, escape external values if the local module has an escape helper. If none exists, add a small local `replace("'", "''")` helper rather than spreading unsafe concatenation.

## Custom Archives

Tables:

- `bd_defdoclist`: custom archive definition/list.
- `bd_defdoc`: custom archive items.

Common query shape:

```sql
select pk_defdoc
from bd_defdoc
where dr = 0
  and enablestate = 2
  and pk_defdoclist = (
    select pk_defdoclist
    from bd_defdoclist
    where code = '<archive_code>' and dr = 0
  )
  and code = '<item_code>'
```

Common `bd_defdoc` fields:

- `pk_defdoc`: item primary key.
- `pk_defdoclist`: archive list primary key.
- `code`: item code.
- `name`: item name or configured value in many interface-option archives.
- `shortname`: short value, often used for days, flags, or mapped codes.
- `mnecode`: mnemonic value, often used for workflow/business mapping.
- `memo`: remarks, often used for view names, bill type codes, or extra config.
- `def1` to `def20`: project-defined extension fields.
- `pk_org`: organization scope when the archive is organization-specific.
- `enablestate`: enabled state, usually `2` means enabled.
- `dr`: delete flag, usually require `dr = 0`.

Examples from these projects:

- `ITFOPTION`: interface URL/config archive; many utilities call `getDefdocName("ITFOPTION", interfaceCode)` and use `bd_defdoc.name` as URL/config value.
- `DEF0003`: material-class push whitelist; configured as `bd_defdoc.code = bd_marbasclass.name` and `bd_defdoc.name = bd_marbasclass.code`.
- `QC_01`, `QC_02`, `QC_03`, `QC_04`, `QC_05`, `QC_06`, `QC_07`, `QC_08`, `QC_10`: qicheng business custom archives used by contract/order/import code.
- `DSJYLX`, `NC2OA`, `xmz_nc-oa`, `CT_WORKFLOWID`: business type/workflow mapping archives.
- `TB_CK`, `TB_WLFL`, `TB_KHFL`, `TB_CGDDLX`, `TBSJGZ`: sync filter/config archives.

## Common Base Tables

Frequently used NC65 base-data tables:

- `org_orgs`: organization. Use `code -> pk_org`; filter `dr = 0`, `enablestate = 2`, and sometimes `islastversion = 'Y'`.
- `org_dept` / `org_dept_v`: department current/versioned data. Use the field expected by the target VO (`pk_dept` vs `pk_vid`).
- `bd_psndoc`: personnel. Use `code -> pk_psndoc`.
- `sm_user`: users. Use `user_code -> cuserid`; `pk_psndoc` links to personnel.
- `bd_material`: material master. Use `code -> pk_material`; some projects also accept `pk_material` directly.
- `bd_material_v`: material version. Use only when the VO expects material version/source fields.
- `bd_marbasclass`: material base classification. Join from `bd_material.pk_marbasclass`.
- `bd_stordoc`: warehouse. Use `code -> pk_stordoc`.
- `bd_billtype`: bill type. Use `pk_billtypecode/vtrantypecode -> pk_billtypeid` when the VO wants transaction type id.
- `bd_busitype`: business type; often maps transaction or bill business codes.
- `bd_currtype`: currency. Use `code -> pk_currtype`.
- `bd_measdoc`: unit of measure.
- `bd_taxcode` / `bd_taxrate`: tax code and tax rate.
- `scm_batchcode`: batch master/custom fields. Batch custom fields often map to `vdef*`.

## Bill Type And Transaction Type

Common patterns:

```sql
select pk_billtypeid
from bd_billtype
where pk_billtypecode = '<vtrantypecode>'
  and dr = 0
```

Reverse lookup:

```sql
select pk_billtypecode
from bd_billtype
where pk_billtypeid = '<ctrantypeid>'
  and dr = 0
```

Always check local code because some older processors omit `dr = 0`, while newer ones include it.

## Material Class Filtering

For `DEF0003` material-class rules:

1. Resolve material from `bd_material` by `pk_material` or `code`.
2. Join `bd_marbasclass` through `bd_material.pk_marbasclass`.
3. Compare `bd_marbasclass.name|bd_marbasclass.code` against `bd_defdoc.code|bd_defdoc.name` under `bd_defdoclist.code = 'DEF0003'`.
4. Filter request body rows before building outbound payloads when only some rows qualify.

Keep material pk extraction in each bill/action class; call the shared rule utility with the material pk or code.

## Interface Field Decisions

For public APIs:

- If the user says "字段格式为主键", do not perform code/name lookup for that field unless validation requires existence checks.
- If request fields are business codes, convert to NC primary keys before setting VO reference fields.
- If output is for third-party systems, usually send codes/names rather than NC primary keys unless the interface contract explicitly says primary key.
- For `creator`, `modifier`, `billmaker`, `approver`, check whether the target VO field stores `sm_user.cuserid` or `bd_psndoc.pk_psndoc`; these are not interchangeable.

For batch fields:

- `vfree*`: bill body free attribute.
- `vbcdef*`: batch custom field on bill body/request, often persisted into `scm_batchcode.vdef*`.
- Preserve unrelated batch custom fields when updating a subset.
