# Fabric item runbook

This folder is structured so it can be used as the **Git-connected item root** for the **Medallion-Sandbox** workspace.

## Important constraints

- The **lakehouse items themselves are tracked in Git**, including display name, description, logical GUID, and shortcut metadata.
- **Lakehouse tables, Spark views, Files contents, and Delta data are not tracked in Git.**

That means syncing this folder to Fabric can create the two empty lakehouses and the notebooks, but the sample CSV files still need to be uploaded into each lakehouse before the notebooks are run.

## Workspace setup

1. Connect **Medallion-Sandbox** to this folder path in Git and sync the incoming items.
2. Confirm the two lakehouses exist:
   - `Modeling_DV2`
   - `Modeling_Simplified`
3. In each lakehouse, upload the contents of `..\sample_data\sample\` into:
   - `Files/modeling_scenarios/raw/`
4. Open each notebook, attach it to its matching lakehouse if needed, and run it end to end.

## Notebook items

- `Modeling_DV2.Lakehouse`
  - empty target lakehouse tracked in Git; notebooks populate its Bronze/Silver/Gold tables
- `Modeling_Simplified.Lakehouse`
  - empty target lakehouse tracked in Git; notebooks populate its Bronze/Silver/Gold tables
- `Modeling_DV2_Build.Notebook`
  - builds Bronze, Silver Raw Vault, and Gold tables for the DV2 scenario
- `Modeling_Simplified_Build.Notebook`
  - builds Bronze, Silver joined-conformed tables, and Gold marts for the simplified scenario

Both notebooks assume the same raw file layout and produce their own lakehouse-local Bronze/Silver/Gold tables.
