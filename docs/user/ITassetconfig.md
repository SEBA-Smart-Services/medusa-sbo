# Setting up a new IT Asset in Medusa

## Overview
Medusa currently supports the addition of Windows, Ubuntu and macOS based IT Assets. These assets must be configured with the Salt Minion software in order to complete configuration and connect to the cloud.

## Software links
  * [Windows](https://repo.saltstack.com/windows/Salt-Minion-2016.11.7-x86-Setup.exe)
  * [Ubuntu](https://repo.saltstack.com/2016.11.html#ubuntu)
  * [macOS](https://repo.saltstack.com/osx/salt-2016.11.7-x86_64.pkg)

## Installation procedure
To add a new IT Asset begin in Medusa:
1. Navigate to the ![Assets](https://github.com/SEBA-Smart-Services/medusa-sbo/tree/master/docs/images/assetpage.png) page
2. Click on the plus icon to add a new IT Asset
3. In the ![Add IT Asset](https://github.com/SEBA-Smart-Services/medusa-sbo/tree/master/docs/images/addassetform.png) page, fill out the form
  *Enter the site name (e.g centralhospital)
  *Enter the device type (e.g es for Enterprise Server, ws for Workstation)
  *Enter a device number (optional)
  *Click "Add and Configure Asset"
  4. On the ![Edit IT Asset](https://github.com/SEBA-Smart-Services/medusa-sbo/tree/master/docs/images/editassetpage.png) page, take note of the IT Asset Name (in this case, centralhospital-es-01). Minimise this page, you'll be coming back later
5. Download and install the Salt-Minion software available in the links above
  *Windows Installation:
  *Run the installation file downloaded from the link above
  *Press Next then consider the terms and conditions
  *On the ![Minion Settings](https://github.com/SEBA-Smart-Services/medusa-sbo/tree/master/docs/images/minionsettings.png):
  "Master IP or Hostname" = salt.sebbqld.com
  "Minion Name" = the IT Asset Name you noted previously (in this case centralhospital-es-01)
  *Press install
  *On completion of the installation, ensure the box named "Start salt-minion" is checked and press Finish
6. Now back on the Edit IT Asset page, click on the "Save Asset and Check Configuration" button
7. If successful, the green tick indication will be shown with the label ![Configuration Complete](https://github.com/SEBA-Smart-Services/medusa-sbo/tree/master/docs/images/completeconfiguration.png)
8. Press close
9. The ![IT Asset](https://github.com/SEBA-Smart-Services/medusa-sbo/tree/master/docs/images/completeitassetdetails.png) will now be scanned for its online status and base data
10. Complete!
