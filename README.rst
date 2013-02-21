Distribution Map Generator
==========================

This QGIS plugin generates distribution maps based on a vector layer of point localities. It uses a chosen field in the localities attribute table to select matching features (presumably species), and intersects that with a separate vector layer which contains the grid polygons (these could also be other zonal vector layers, such as provinces or habitat types). The selected polygons are then styled and overlaid on the base map. Each distribution map is saved as a png file, with the unique identifier as a filename.

Todo
----

  * Add a button to set extent based on the current map extent
  * Add a colour selector to choose the background colour
  * Copy the style of the provided grid layer for output, rather than use the single style currently provided.
  * Add a progress bar
  
License
-------

Copyright (C) 2013  Rudi von Staden

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

http://www.gnu.org/licenses/gpl-2.0.html
