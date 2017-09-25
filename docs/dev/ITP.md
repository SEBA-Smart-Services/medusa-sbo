# ITP Development

ITP creation and interactions are important for aiding the current testing and commisioning methods used, the goal is to automate as much of the process as possible. Currently all the templates are found in app/templates with each branch having it's own seperate folder. All the models live in the app/models/ITP.py file and the controllers can be found in app/controllers.py (moving forward this may become more modular and seperated into its own folder).

## Setup

The ITP section has been developed to keep a simple layout throughout the navigation making it easier to familiarise oneself with ITPs.

### Specific and Template (generic)

The ITP currently url uses the following system \<sitename>/projects/\<projectname>/ITP/\<ITPname>/deliverable/ \<deliverablename>/ITC/\<ITCid>/checks/\<checkid>. However this system will change in the future, from name to number, so as to avoid name errors. As seen from the url, the user will move through different layers of an ITP starting a project for a given site all the way through to an Individual ITC and it's checks. Moving forward it would be good to add in a breadcrumb feature to make it easier to move up and down this chain.

In addition to this "specific" ITP section there is also a templating section which works on the following url basis, /Genric/ITC/\<ITCid>/check and /Generic/checks/\<checkid>. This is to keep templates universal across all sites making it easier to quickly grab premade templates.

### Models

As mentioned earlier the models for this section live in ITP.py and follow a similar break down to the URls. Most of the models are self explanitory however there may be some confusion with the ITC and checks section. ITCs and checks are split into two distinct groups, generic and specific. Generic ITCs and checks come from **check_generic** and **ITC** models and are used to create templates ITCs. Generic checks are added to the ITC model through the **ITC_check_map** model which is a many-to-many mapping of the two generic models. This mapping model is then used to create specific 

These templates are then brought into a deliverable based on the deliverable type chosen by creating "specific ITCs" which use the **Deliverable_ITC_map** and **Deliverable_check_map**.

### Templates

The templates for ITP components are collectively found within the *template* folder however each piece has been split up into it's own folder for ease of user. For example when working on the "projects" section of ITPs you would go to the *project* folder in templates, if you are working on specific ITCs, as opposed to template ITCs, you would go to the *specific_ITC* folder.

### Controllers

The controllers for each section of the ITP (following similar breakdown to the URL) with each componenet

## Other

### Flask Admin with Models

Flask admin has been used to look after the **Locations** and **Deliverable type** models. This was to ensure that users couldn't create numerous locations for the same place and also to limit the number of deliverable types. The design choice to place these two models in flask admin over a seperate page that only admin could access was the means of convience and to save time (moving forward this models may gain their own controllers and templates).
