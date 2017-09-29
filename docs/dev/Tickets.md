# Ticketing

The ticketing system was introduced to make maintenance more proactive with faster responce times and more visbility into time spent on maintenance contracts. The following outlines the developer side to ticket creation and interaction.

## Design Considerations

* Tickets come in two sections site specific and all site tickets for a user.
* Current ticket setup follows a layout similar to [Trac Tickets](https://trac.edgewall.org/wiki/TracTickets) and follows it's [workflow diagram](https://trac.edgewall.org/wiki/TracWorkflow#TheDefaultTicketWorkflow). The current setup should have information related to the following:

| Item | Description |
| ------- | ----------- |
| Name | A short descriptive name |
| Description | Extended more indepth description of the problem |
| Creation Date | Date ticket was created, automatically done |
| Due Date (optional) | Date job needs to be completed by |
| Reporter | The person who created the ticket |
| Category | Contains: Defect, Enhancement, task and Breakdown |
| Component | Contains: BMS, Security, Mechanical,  |
| Priority | 5 levels of priority defined as: Critical, High, Standard, Low, Negligible |
| Assigned to/Owner | Current user the ticket is assigned to |
| CC (needs to be implemented) (optional) | other users who may need to recieve emails but are not owners of the tickets (maybe added to subscribing) |
| Resolution Date | Date ticket was resolved |
| Resolved by | Person who resolves the ticket |
| Resolution | Resolution type, currently contains: Fixed, Invalid, Won't Fix, Duplicate, Works for me |
| Status | Contains: Open, Working, Closed (heading forward this should be changed) |
| Facility/Site | Site ticket is allocated to |
| Project (Optional) | If a ticket is project related |
| Date Modified | If ticket is edited then there should be a record of it |
| Modified by | Who edited the ticket |
| Job Number | Reference number for the job |
| additional allowances | replies/comments, action list, attachements, subscriptions, reports, ticket filtering (not yet implemented) |

## Setup

The ticketing system is a combination of flicket and developer code to integrate the flicket design into Medusa. Naming of templates and models needs to be converted from 'flicket' to 'ticket' in various places.

### URL

The current URL for tickets is as follows `/site/<siteid>/ticket/<ticketid>` where site id could be either a specific site id or "all" which means all sites the current user has access to. 

### Models

The Models live in the `/app/ticket/models.py`and are set up similar to the original flicket integration with the main ticket model `FlicketTicket` integrating with all the other ticket models. Several of these models are being administered with Flask Admin for simplicity purposes and to stop other users creating too many objects like status' and catergories.

### Templates

The ticket templates are found in the main template folder under flicket `/app/templates/flicket` and follows the flicket naming system current with email html pages starting with *'email'* and all web related pages starting with *'flicket'*. There are potentially unused pages that need to be removed however when doing so the developer needs to ensure the page has not been used anywhere in the app or will be used in the future.

Tickets also have a statistics template under `/app/templates/flicket/flicket_index.html`, while the page may not be super useful it would be good to take some of the statistic details from here moving forward.

### Controllers

The controllers for ticketing are all found in `/app/ticket/controllers.py`. There are some controllers placed at the bottom of this file that are currently not being used however may be useful in the future. There is also a section on *'departments'* throughout the controllers file that is redundant, however some models have references to this section that causes them to crash. These sections should be cleaned up when time is available.

### Forms

Tickets also use WTF forms which is a handy way of creating the form before rendering the HTML page. It allows for a reduction in ticket templates as the controllers will just render a different form and apply it to the same template.

## Scripts

Has been copied across from the original flicket ticket system and changed as needed.

## API

Has been copied across from the original flicket ticket system and changed as needed.

## Future goals

* Ticket automation is one of the major goals heading forward in ticketing. This would involve setting up algorithms or rules to check things like alarms, if something abnormal shows up then the system should generate a ticket (and possibly assign it to a service tech. depending on priority). Of course surronding this would be a pre determined system, discussed with the client, around when to create jobs and how fast to react to issues.
  * Integrate job creation for outside techs on a particular site by integrating with their system
* Set up more visible statistics possibly?

## Other

### Flicket Integration

A lot of the ticketing system has come from the [Flicket Ticket](https://github.com/evereux/flicket) package. It has been manipulated to suit the needs of medusa by changing some of the templates and controllers.

### Reports

Reports are achieved using [weasyprint](https://pythonhosted.org/Flask-WeasyPrint/).

### Flask Mail

Once again flask mail has been used to send out notifications and changes as the tickets changed. This has been integrated with the ticket controllers
