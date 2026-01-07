# Task Flow Setup
Currently, Task Flow is not a [supported item type](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/item-definition-overview#definition-details-for-supported-item-types) for definitions. As a result, Task Flow cannot be deployed using the set item command of Fabric CLI (or the REST API).

However, you can [manually import an existing task flow](https://learn.microsoft.com/en-us/fabric/fundamentals/task-flow-create#start-by-importing-an-existing-task-flow) in the Fabric UI using the exported json definition in this repo. Note that this will capture the Task Flow but it will *not* retain any of the associated items.

After the Task Flow is imported, items can be manually attached to each task flow task via the UI.