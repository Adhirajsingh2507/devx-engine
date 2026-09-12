# Reentry exposure and financial scenarios

## Reentry input boundary

The reentry module receives a supplied footprint, never a conjunction report alone. Inputs are a GeoJSON Polygon or MultiPolygon in WGS84 longitude/latitude order, a declared scenario time window, source/revision, and exposure layers. initial release supports regional polygons that do not cross the antimeridian, latitude within -85 to 85, and valid non-self-intersecting rings. Reject unsupported global/dateline geometry visibly instead of drawing the long way around Earth.

The canonical exposure layers are arrays of synthetic point records: population sample points carry an integer represented_population; asset points carry asset_id, asset_type and replacement_value as an amount/currency object. The footprint is a GeoJSON geometry object; a full FeatureCollection adapter is optional future work. The footprint test includes its outer boundary and excludes the interior of holes. A point on a hole boundary counts as exposed under a documented conservative convention. Deduplicate identical asset IDs and population sample IDs before summation; reject conflicting duplicate records. Overlapping MultiPolygon parts do not double count.

The initial implementation uses a tested point-in-polygon library and explicit boundary tests. It does not convert geographic degrees into metres using one constant. No area-based population estimate is claimed: these are point representations, and the UI states “population represented by included sample points,” not a validated census-level casualty estimate.

## Outputs

Return included/excluded point IDs, exposed represented population, exposed asset count, exposed replacement value grouped by currency, unavailable-value count and source-layer coverage notes. Missing asset value remains unknown, not zero. Do not total INR and USD without an explicit scenario exchange rate; default show separate currency totals.

Terrain/land-cover labels provide context. Flat ground is not automatically lower consequence; settlement, critical infrastructure, fragment survival and impact energy can dominate. In the synthetic sandbox, one footprint covers more represented people/assets than another. They are alternative supplied footprints, not locations the system has proved reachable. A low-exposure footprint is not a recommended real disposal target. [^08-S02][^08-S03]

## Optional conditional damage

Only enable monetary damage when the scenario supplies, for each included asset, a probability_of_damage conditional on this reentry scenario and a mean_loss_fraction conditional on damage. Then expected damage for that asset = probability_of_damage times mean_loss_fraction times replacement_value. The same impact can damage multiple assets, so expectation of the sum is the sum of expectations without requiring independent damage events. This does not establish the probability that any damage occurs.

Keep excluded/missing vulnerability items visible. Sum only known terms and label a partial estimate if any included asset lacks assumptions. Do not infer damage probability by dividing polygon area or using TerraSight's safety score. Do not monetize people, infer casualties from point counts or produce a legal liability estimate.

## Orbital economic model

The owner supplies disjoint conditional loss components: spacecraft replacement, launch/replacement service, unrecovered mission revenue, service interruption and other documented costs. Avoid including the same lost revenue in both mission revenue and interruption. Separate insured recovery if modeled; default insurance, legal liability, environmental monetization and third-party loss are excluded.

Conditional loss L is the sum of included monetary terms in one currency. A single-event expected loss is Pc times L only when Pc applies to the same event and L describes loss conditional on that event. If Pc is unsupported, conflicting beyond a declared scenario or numerically unresolved, report the financial result as unavailable or provide separate labeled scenarios, not a blended estimate.

For a fixed comparable conditional loss, estimated net benefit of response = (Pc_before - Pc_after) times L - response_cost. With different conditional-loss assumptions, use Pc_before times L_before - Pc_after times L_after - response_cost. Response cost can include supplied operations labor, fuel/lifetime opportunity cost and interruption caused by the response, without counting the same cost twice.

Use decimal arithmetic and round only the final display to the currency's minor unit. Stored values retain sufficient precision for reproduction. Input monetary values are decimal strings. Reject negative probabilities, negative declared costs, mixed currency arithmetic and nonfinite numeric fields. A negative net benefit is displayed, not clipped to zero. It does not cancel a required review or hard safety policy.

## Reference economic case

Entirely synthetic inputs: conditional loss INR 1,000,000,000; Pc_before 0.0001; Pc_after 0.000001; response_cost INR 20,000. Expected loss before is INR 100,000; after is INR 1,000; gross expected-loss reduction is INR 99,000; net benefit is INR 79,000. Displaying INR 1,000,000,000 as “saved” would be incorrect.

One warning's updates do not create separate economic events. Do not sum a spacecraft's full loss repeatedly across overlapping encounters. The initial release financial view is per scenario/case; portfolio aggregate benefits are out of scope until event dependencies and mutually exclusive loss pathways are modeled.

## Uncertainty presentation

Show low/base/high user-supplied loss assumptions as scenarios, not confidence intervals. If probabilities come from different applicable covariance alternatives, show each probability-economic pairing with its provenance. Do not label the maximum among a handful of scenarios as the mathematical maximum possible risk.

Actual money saved is a later empirical/causal claim requiring a defensible counterfactual and observed costs. Hackathon metrics use “modeled expected-loss change” and “estimated review effort saved.” The reentry and orbital economic branches must never multiply orbital Pc directly by all asset value under a ground footprint: the intermediate breakup/reentry/impact probabilities are absent.

## Source notes

[^08-S02]: ESA, [Reentry background](https://www.esa.int/content/view/full/413425).

[^08-S03]: ESA, [Re-entry safety](https://technology.esa.int/page/re-entry-safety).
