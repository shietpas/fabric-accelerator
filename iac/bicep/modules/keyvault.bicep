
// Parameters
@description('Location where resources will be deployed. Defaults to resource group location')
param location string = resourceGroup().location

@description('Cost Centre tag that will be applied to all resources in this deployment')
param cost_centre_tag string

@description('System Owner tag that will be applied to all resources in this deployment')
param owner_tag string

@description('Subject Matter Expert (SME) tag that will be applied to all resources in this deployment')
param sme_tag string

@description('Key Vault name')
param keyvault_name string

// Variables
var suffix = uniqueString(resourceGroup().id)
var keyvault_uniquename = take('${keyvault_name}-${suffix}', 24)

// Create Key Vault
resource keyvault 'Microsoft.KeyVault/vaults@2023-07-01' ={
  name: keyvault_uniquename
  location: location
  tags: {
    CostCentre: cost_centre_tag
    Owner: owner_tag
    SME: sme_tag
  }
  properties:{
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enabledForDeployment: true
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: true
    enableRbacAuthorization: true
  }
}

// Create Key Vault Access Policies for Purview
resource existing_purview_account 'Microsoft.Purview/accounts@2021-07-01' existing = if(enable_purview) {
    name: purview_account_name
    scope: resourceGroup(purviewrg)
  }

@description('This is the built-in Key Vault Secret User role. See https://docs.microsoft.com/azure/role-based-access-control/built-in-roles#key-vault-secrets-user')
resource keyVaultSecretUserRoleRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  name: '4633458b-17de-408a-b874-0445c86b69e6'
  scope: subscription()
}

@description('Grant the app service identity with key vault secret user role permissions over the key vault. This allows reading secret contents')
resource this_keyvault_secretuser_purview 'Microsoft.Authorization/roleAssignments@2020-08-01-preview' = if(enable_purview) {
  scope: keyvault
  name: guid(resourceGroup().id, existing_purview_account.id, keyVaultSecretUserRoleRoleDefinition.id)
  properties: {
    roleDefinitionId: keyVaultSecretUserRoleRoleDefinition.id
    principalId: enable_purview ? (existing_purview_account.?identity.principalId ?? '') : ''
    principalType: 'ServicePrincipal'
  }
}

// resource this_keyvault_accesspolicy 'Microsoft.KeyVault/vaults/accessPolicies@2022-07-01' = if(enable_purview) {
//   name: 'add'
//   parent: keyvault
//   properties: {
//     accessPolicies: [
//       { tenantId: subscription().tenantId
//         objectId: existing_purview_account.identity.principalId
//         permissions: { secrets:  ['list','get']}

//       }
//     ]
//   }
// }

output keyvault_name string = keyvault.name
