# Identifiable

## Location

Using Wikidata to gather population data of cities and countries. Then calculate the entropy of drawing a uniformly random person labelled with corresponding city/country. Compare to how many bits would be necessary to uniquely specify an individual in the total population of those selected locations.

### Caveats

Data bias of being on Wikidata in the first place. Locations without population fields are assumed to be 0 population. The values outputed are only supposed to give a relative idea as compared to entropies of uniform distribution on just the location and uniform distribution over individuals counted in those population totals.

## Other identifiers

If data is available do the same with more such as

- Birth Year
- Occupation

Likely data not available for combinations but should output the upper bound gotten by calcuating with independent marginals.
