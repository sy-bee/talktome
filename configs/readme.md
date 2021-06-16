# Azure Private Link

Terraform module which provides Azure Private Link Endpoint resources to enable secure connectivity to Azure based Private Link Services and Resources. The following resources are provided by this module:

- Azure Private Link Endpoints with specified Private Service Connection to a Private Link Resource or a Private Link Service
- Private DNS zone linked to the VNET with one or more specified records pointing to Private Link Endpoints

## Notes

- Private Service Connection can be configured with Azure Private Link Service alias or ID
- VNET subnet for the Private Link Endpoint at the moment is chosen randomly from the list of provided subnets
- Future iterations may automatically choose a subnet with most number of free IP addresses

## Usage

```
module "private_link" {
  source = "../../../modules/azure-private-link"

  resource_group    = "resource_group"
  vnet_id           = "123456"
  vnet_subnets      = ["subnet1", "subnet2"]

  private_links = [
    {
      name                 = "Test_PL"
      service_alias        = "plservice.XXX.northeurope.azure.privatelinkservice"
      service_id           = null
      subresource_names    = null
      is_manual_connection = true
      request_message      = "Request for connection. Over."
      private_dns_zone     = "tentran.com"
      private_dns_records  = ["account", "ocsp.account"]
    }
  ]
}
```

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.14 |
| <a name="requirement_azurerm"></a> [azurerm](#requirement\_azurerm) | >= 2.60.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_azurerm"></a> [azurerm](#provider\_azurerm) | >= 2.60.0 |
| <a name="provider_random"></a> [random](#provider\_random) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [azurerm_private_dns_a_record.private_link_dns_records](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/private_dns_a_record) | resource |
| [azurerm_private_dns_zone.private_link](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/private_dns_zone) | resource |
| [azurerm_private_dns_zone_virtual_network_link.private_dns_link](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/private_dns_zone_virtual_network_link) | resource |
| [azurerm_private_endpoint.private_link](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/private_endpoint) | resource |
| [random_shuffle.subnet](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/shuffle) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_environment"></a> [environment](#input\_environment) | Tag with the same name will be set to this value | `string` | `"dev"` | no |
| <a name="input_private_links"></a> [private\_links](#input\_private\_links) | A list of objects containing the Private Link connection details:<br><br>\| Variable \| Description \|<br>\| --- \| --- \|<br>\| `name` \| Private Link Endpoint name \|<br>\| `service_alias` \| Service Alias of the Private Link Enabled Remote Resource which this Private Endpoint should be connected to. One of `service_alias` or `service_id` must be specified \|<br>\| `service_id` \| ID of the Private Link Enabled Remote Resource which this Private Endpoint should be connected to. One of `service_alias` or `service_id` must be specified \|<br>\| `subresource_names` \| List of subresource names which the Private Endpoint is able to connect to, e.g. "blob", "table", etc \|<br>\| `is_manual_connection` \| Does the Private Endpoint require Manual Approval from the remote resource owner? \|<br>\| `request_message` \| A message passed to the owner of the remote resource when the private endpoint attempts to establish the connection to the remote resource (max 140 chars) \|<br>\| `private_dns_zone` \| Private DNS zone to be used for the private link \|<br>\| `private_dns_records` \| Private DNS records to be created in the `private_dns_zone` \| | <pre>list(object({<br>    name                 = string<br>    service_alias        = string<br>    service_id           = string<br>    subresource_names    = list(string)<br>    is_manual_connection = bool<br>    request_message      = string<br>    private_dns_zone     = string<br>    private_dns_records  = list(string)<br>  }))</pre> | n/a | yes |
| <a name="input_resource_group"></a> [resource\_group](#input\_resource\_group) | Resource group where to create Private Link Endpoints | `any` | n/a | yes |
| <a name="input_ttl"></a> [ttl](#input\_ttl) | Time To Live (TTL) of the DNS record in seconds | `number` | `300` | no |
| <a name="input_vnet_id"></a> [vnet\_id](#input\_vnet\_id) | VNET subnet ID to link private DNS zone | `string` | n/a | yes |
| <a name="input_vnet_subnets"></a> [vnet\_subnets](#input\_vnet\_subnets) | List of VNET subnets where to create Private Link Endpoints | `list(any)` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_private_dns_records"></a> [private\_dns\_records](#output\_private\_dns\_records) | List of DNS records grouped by Private Link Endpoint names |
