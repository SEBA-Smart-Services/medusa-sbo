# ITP Development

ITP creation and interactions are important for aiding the current testing and commisioning methods used, the goal is to automate as much of the process as possible. Currently all the templates are found in app/templates with each branch having it's own seperate folder. All the models live in the `app/models/ITP.py` file and the controllers can be found in app/controllers.py (moving forward this may become more modular and seperated into its own folder).

## Design considerations

* For ITC creation there is a templating section and a allocated ITC section. This is so reusable templates can be created by the users as needed.
* Initial ITCs are created dynamically based on the chosen deliverable type, these can be altered after creation. This was to reduce time for users trying to find all applicable ITCs. This logic is based on the ITC templates having a deliverable type.

## Setup

The ITP section has been developed to keep a simple layout throughout the navigation making it easier to familiarise oneself with ITPs.

### Specific and Template (generic)

The ITP currently url uses the following system `<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/checks/<checkid>`. However this system will change in the future, from name to number, so as to avoid name errors. As seen from the url, the user will move through different layers of an ITP starting a project for a given site all the way through to an Individual ITC and it's checks. Moving forward it would be good to add in a breadcrumb feature to make it easier to move up and down this chain.

In addition to this "specific" ITP section there is also a templating section which works on the following url basis, `/genric/ITC/<ITCid>/check/<checkid>` and `/generic/check/<checkid>`. This is to keep templates universal across all sites making it easier to quickly grab premade templates.

### Models

As mentioned earlier the models for this section live in ITP.py and follow a similar break down to the URls. Most of the models are self explanitory however there may be some confusion with the ITC and checks section. ITCs and checks are split into two distinct groups, generic and specific. Generic ITCs and checks come from **check_generic** and **ITC** models and are used to create templates ITCs. Generic checks are added to the ITC model through the **ITC_check_map** model which is a many-to-many mapping of the two generic models. This mapping model is then used to create specific 

These templates are then brought into a deliverable based on the deliverable type chosen when creating "specific ITCs" using the **Deliverable_ITC_map** and **Deliverable_check_map** models.

### Templates

The templates for ITP components are collectively found within the *template* folder however each piece has been split up into it's own folder for ease of user. For example when working on the "projects" section of ITPs you would go to the *project* folder in templates, if you are working on specific ITCs, as opposed to template ITCs, you would go to the *specific_ITC* folder.

### Controllers

The controllers for each section of the ITP (following similar breakdown to the URLs) are found in the main `app/controller.py` file. Most are broken into the save 4 to 5 controllers: new, edit, delete, list and item pages. In order to avoid name clashes there is code in place to check for the same name in both edit and new pages. When deleting objects we need to ensure that any other object that may rely on that one gets deleted or updated. For example if a template ITC is deleted then the corresponding specific ITCs will be deleted. Therefore where possible avoid deleting templates, in the future it would be best to possibly save the state of the deleted object so that you dont need to remove it from specific ITC records.

## Other

### Flask Admin with Models

Flask admin has been used to look after the **Locations** and **Deliverable type** models. This was to ensure that users couldn't create numerous locations for the same place and also to limit the number of deliverable types. The design choice to place these two models in flask admin over a seperate page that only admin could access was the means of convience and to save time (moving forward this models may gain their own controllers and templates).
