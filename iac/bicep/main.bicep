// Scope
targetScope = 'subscription'

// Parameters
@description('Resource group where Microsoft Fabric capacity will be deployed. Resource group will be created if it doesnt exist')
param dprg string= 'rg-fabric-accelerator'

@description('Microsoft Fabric Resource group location')
param rglocation string = 'northcentralus'

@description('Email of Fabric Capacity Administrator')
param fabric_capacity_admin_email string

@description('Cost Centre tag that will be applied to all resources in this deployment')
param cost_centre_tag string = 'DADP-Sandbox'

@description('System Owner tag that will be applied to all resources in this deployment')
param owner_tag string = 'scott.hietpas@SkylineDataAnalytics.onmicrosoft.com' //Administrators must be local tenant user (not guest)

@description('Subject Matter Expert (SME) tag that will be applied to all resources in this deployment')
param sme_tag string ='scott.hietpas@SkylineDataAnalytics.onmicrosoft.com'

@description('Timestamp that will be appended to the deployment name')
param deployment_suffix string = utcNow()

@description('Flag to indicate whether to create a new Purview resource with this data platform deployment')
param create_purview bool = false

@description('Flag to indicate whether to enable integration of data platform resources with either an existing or new Purview resource')
param enable_purview bool = true

@description('Resource group where Purview will be deployed. Resource group will be created if it doesnt exist')
param purviewrg string= 'rg-purview-lab'

@description('Location of Purview resource. This may not be same as the Fabric resource group location')
param purview_location string= 'eastus'

@description('Resource Name of new or existing Purview Account. Must be globally unique. Specify a resource name if either create_purview=true or enable_purview=true')
param purview_name string = 'DADPSandboxPurview' // Replace with a Globally unique name

@description('Flag to indicate whether auditing of data platform resources should be enabled')
param enable_audit bool = true

@description('Resource group where audit resources will be deployed if enabled. Resource group will be created if it doesnt exist')
param auditrg string= 'rg-audit'


// Variables
var fabric_deployment_name = 'fabric_dataplatform_deployment_${deployment_suffix}'
var keyvault_deployment_name = 'keyvault_deployment_${deployment_suffix}'
var audit_deployment_name = 'audit_deployment_${deployment_suffix}'
// var controldb_deployment_name = 'controldb_deployment_${deployment_suffix}'

// Create data platform resource group
resource fabric_rg  'Microsoft.Resources/resourceGroups@2024-03-01' = {
 name: dprg 
 location: rglocation
 tags: {
        CostCentre: cost_centre_tag
        Owner: owner_tag
        SME: sme_tag
  }
}

// Deploy Key Vault with default access policies using module
module kv './modules/keyvault.bicep' = {
  name: keyvault_deployment_name
  scope: fabric_rg
  params:{
     location: fabric_rg.location
     keyvault_name: 'kv-fabric-accelerator'
     cost_centre_tag: cost_centre_tag
     owner_tag: owner_tag
     sme_tag: sme_tag
     purview_account_name: enable_purview ? (purview.?outputs.purview_account_name ?? '') : ''
     purviewrg: enable_purview ? purviewrg : ''
     enable_purview: enable_purview
  }
}

// resource kv_ref 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
//   name: kv.outputs.keyvault_name
//   scope: fabric_rg
// }

//Enable auditing for data platform resources
module audit_integration './modules/audit.bicep' = if(enable_audit) {
  name: audit_deployment_name
  scope: audit_rg
  params:{
    location: audit_rg.?location ?? ''
    cost_centre_tag: cost_centre_tag
    owner_tag: owner_tag
    sme_tag: sme_tag
    audit_storage_name: 'staudit01'
    audit_storage_sku: 'Standard_LRS'    
    audit_loganalytics_name: 'log-audit01'
  }
}

//Deploy Microsoft Fabric Capacity
module fabric_capacity './modules/fabric-capacity.bicep' = {
  name: fabric_deployment_name
  scope: fabric_rg
  params:{
    fabric_name: 'fabaccelerator01'  //3-63 characters, alphanumeric
    location: fabric_rg.location
    cost_centre_tag: cost_centre_tag
    owner_tag: owner_tag
    sme_tag: sme_tag
    adminUsers: fabric_capacity_admin_email //owner_tag //kv_ref.getSecret('fabric-capacity-admin-username')
    skuName: 'F4' // Default Fabric Capacity SKU F2
  }
}

//Deploy SQL control DB 
// module controldb './modules/sqldb.bicep' = {
//   name: controldb_deployment_name
//   scope: fabric_rg
//   params:{
//      sqlserver_name: 'ba-sql01'
//      database_name: 'controlDB' 
//      location: fabric_rg.location
//      cost_centre_tag: cost_centre_tag
//      owner_tag: owner_tag
//      sme_tag: sme_tag
//      ad_admin_username:  owner_tag //kv_ref.getSecret('sqlserver-ad-admin-username')
//      ad_admin_sid:  kv_ref.getSecret('sqlserver-ad-admin-sid')  
//      auto_pause_duration: 60
//      database_sku_name: 'GP_S_Gen5_1' 
//      enable_purview: enable_purview
//      purview_resource: enable_purview ? purview.outputs.purview_resource : {}
//      enable_audit: false
//      audit_storage_name: enable_audit?audit_integration.outputs.audit_storage_uniquename:''
//      auditrg: enable_audit?audit_rg.name:''
//   }
// }
