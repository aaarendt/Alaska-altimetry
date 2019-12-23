# Overview

This code processes and analyzes [IceBridge Alaska](https://www.nasa.gov/image-feature/operation-icebridge-exploring-alaska-s-mountain-glaciers) Altimetry data. Users can select, compare and analyze any set of altimetry surveys and then apply those selections to an extrapolation using methods described in the supplemental section of [Larsen et al., 2015](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2015GL064349). 

The raw altimetry data and surface elevation change data as well as the 'altimetry' version of the RGI 4.0 called the ergi are hosted in a Postgres relational database hosted on AWS. Contact Anthony Arendt for login information. 

## Project lead 

[Chris Larsen](mailto:cflarsen@alaska.edu)

## Code Developers

[Anthony Arendt](mailto:arendta@uw.edu), Evan Burgess, Christian Kienholz

## Installation 

```pip install -e .```

## Workflow

<img src='images/workflow.jpg' width=800>

#### References

C. Larsen, E. Burgess, A. Arendt, S. O'Neel, A. Johnson, and C. Kienholz (2015). Surface melt dominates Alaska glacier mass balance. _Geophysical Research Letters_, pp. 5902-5908. ISSN: 00948276. DOI:
[10.1002/2015GL064349](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2015GL064349).

Kitzes, Justin, Daniel Turek, and Fatma Deniz, eds. The practice of reproducible research: case studies and lessons from the data-intensive sciences. [Univ of California Press, 2017.](https://books.google.com/books?hl=en&lr=&id=NDEyDwAAQBAJ&oi=fnd&pg=PR11&ots=xB91HIAONr&sig=YS0c8fgiyr93Js1ryS9QvJ9--4M#v=onepage&q&f=false)
